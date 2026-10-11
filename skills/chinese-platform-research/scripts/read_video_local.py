"""Create local transcript and visual evidence; does not interpret the content.

Adapted from the verified local FFmpeg/faster-whisper workflow. SRT formatting
derives from yuzhang-ai/ai-video-transcriber (MIT); see LICENSE.video-transcriber.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess


def run(command):
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    return result


def srt_time(seconds):
    hours, rest = divmod(round(seconds * 1000), 3600000)
    minutes, rest = divmod(rest, 60000)
    secs, millis = divmod(rest, 1000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}'


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('media', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--model', type=Path)
    parser.add_argument('--language', default='zh')
    parser.add_argument('--no-asr', action='store_true')
    parser.add_argument('--no-frames', action='store_true')
    parser.add_argument('--frame-step', type=float)
    parser.add_argument('--source-url', help='Original work URL supplied by the caller; not fetched')
    args = parser.parse_args()
    media, out = args.media.resolve(), args.out.resolve()
    if not media.is_file():
        parser.error('media must be an existing local file')
    if args.frame_step is not None and (not math.isfinite(args.frame_step) or args.frame_step <= 0):
        parser.error('frame-step must be positive and finite')
    if not args.no_asr:
        if args.model is None or not all((args.model / n).is_file() for n in ['config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt']):
            parser.error('provide an existing complete local model directory, or --no-asr')
    if out.exists():
        parser.error('output directory already exists; choose a new path')
    missing = [tool for tool in ('ffmpeg', 'ffprobe') if not shutil.which(tool)]
    if missing:
        parser.error('required on PATH: ' + ', '.join(missing))
    probe = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(media)]).stdout)
    duration = float(probe['format']['duration'])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('invalid media duration')
    video = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
    if not args.no_asr and not any(s['codec_type'] == 'audio' for s in probe['streams']):
        parser.error('media has no audio stream; use --no-asr for visual-only processing')
    required = ([] if args.no_asr else ['faster_whisper']) + (['PIL'] if video and not args.no_frames else [])
    missing = [name for name in required if importlib.util.find_spec(name) is None]
    if missing:
        parser.error('missing Python dependencies: ' + ', '.join(missing))
    out.mkdir(parents=True, exist_ok=False)
    save_json(out / 'media-probe.json', probe)
    meta = {'source': str(media), 'source_url': args.source_url, 'sha256': file_sha256(media), 'duration': duration, 'processing_complete': False, 'content_read_status': 'not_read'}
    save_json(out / 'metadata.json', meta)
    decode = run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(media), '-f', 'null', os.devnull])
    (out / 'decode.log').write_text(decode.stderr, encoding='utf-8')
    meta['full_decode'] = True
    if video and not args.no_frames:
        from PIL import Image, ImageDraw
        frames = out / 'frames'
        frames.mkdir()
        scene = run(['ffmpeg', '-v', 'info', '-i', str(media), '-vf', r'select=gt(scene\,0.28),showinfo', '-an', '-f', 'null', os.devnull])
        (out / 'scene.log').write_text(scene.stderr, encoding='utf-8')
        cuts = sorted(set(float(t) for t in re.findall(r'pts_time:([0-9.]+)', scene.stderr)))
        video_duration = float(video.get('duration') or duration)
        safe_end = max(0, video_duration - 0.25)
        step = args.frame_step or (4 if duration <= 90 else 8)
        times = {round(i * step, 3): 'overview' for i in range(math.ceil(video_duration / step)) if i * step <= safe_end}
        times[round(safe_end, 3)] = 'ending'
        for cut in cuts:
            for delta in [-0.16, 0, 0.16]:
                times[round(min(safe_end, max(0, cut + delta)), 3)] = 'scene_neighbor'

        def extract(pair):
            i, seconds = pair
            path = frames / f'frame-{i:04d}.jpg'
            run(['ffmpeg', '-v', 'error', '-ss', str(seconds), '-i', str(media), '-vf', 'format=yuvj420p', '-threads', '1', '-strict', 'unofficial', '-frames:v', '1', '-q:v', '2', '-n', str(path)])
            with Image.open(path) as picture:
                picture.verify()
            return {'file': path.name, 'seconds': seconds, 'role': times[seconds]}

        with ThreadPoolExecutor(max_workers=2) as pool:
            index = list(pool.map(extract, enumerate(sorted(times))))
        save_json(frames / 'index.json', index)
        for offset in range(0, len(index), 12):
            sheet = Image.new('RGB', (1600, 1290), '#111111')
            draw = ImageDraw.Draw(sheet)
            for pos, item in enumerate(index[offset:offset + 12]):
                x, y = (pos % 4) * 400, (pos // 4) * 430
                with Image.open(frames / item['file']) as picture:
                    picture.thumbnail((394, 398))
                    sheet.paste(picture, (x + (400 - picture.width) // 2, y))
                draw.text((x + 5, y + 404), f"{item['seconds']:.3f}s {item['role']}", fill='white')
            sheet.save(frames / f'sheet-{offset // 12 + 1:02d}.jpg')
        meta['visual'] = {'frame_count': len(index), 'overview_step': step, 'scene_threshold': 0.28, 'cuts': cuts, 'viewed': False, 'coverage': 'sampling; not continuous viewing'}
    if not args.no_asr:
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        from faster_whisper import WhisperModel
        audio = out / 'audio-16k.wav'
        run(['ffmpeg', '-v', 'error', '-i', str(media), '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', '-n', str(audio)])
        audio_duration = float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(audio)]).stdout)
        run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(audio), '-f', 'null', os.devnull])
        model = WhisperModel(str(args.model.resolve()), device='cpu', compute_type='int8', cpu_threads=4, local_files_only=True)
        segments, info = model.transcribe(str(audio), language=args.language, vad_filter=False, condition_on_previous_text=False, beam_size=5)
        rows = []
        with (out / 'asr-segments.jsonl').open('x', encoding='utf-8') as handle:
            for segment in segments:
                row = {'start': segment.start, 'end': segment.end, 'text': segment.text.strip(), 'no_speech_prob': segment.no_speech_prob, 'avg_logprob': segment.avg_logprob, 'compression_ratio': segment.compression_ratio}
                rows.append(row)
                handle.write(json.dumps(row, ensure_ascii=False) + '\n')
                handle.flush()
        valid = bool(rows) and all(r['text'] and math.isfinite(r['start']) and math.isfinite(r['end']) and 0 <= r['start'] <= r['end'] <= audio_duration + 0.1 for r in rows) and all(b['start'] >= a['start'] for a, b in zip(rows, rows[1:]))
        save_json(out / 'asr.json', {'segments': rows})
        (out / 'asr-raw.txt').write_text('\n'.join(r['text'] for r in rows), encoding='utf-8')
        (out / 'asr-timestamps.txt').write_text('\n'.join(f"[{r['start']:.3f}--{r['end']:.3f}] {r['text']}" for r in rows), encoding='utf-8')
        (out / 'asr.srt').write_text('\n\n'.join(f"{i+1}\n{srt_time(r['start'])} --> {srt_time(r['end'])}\n{r['text']}" for i, r in enumerate(rows)), encoding='utf-8')
        meta['asr'] = {'model': str(args.model.resolve()), 'offline': True, 'device': 'cpu', 'compute_type': 'int8', 'language': args.language, 'vad': False, 'condition_on_previous_text': False, 'beam_size': 5, 'audio_duration': audio_duration, 'segment_count': len(rows), 'timestamps_valid': valid, 'reviewed': False}
        if not valid:
            save_json(out / 'metadata.json', meta)
            raise ValueError('empty transcript or invalid timestamps; inspect partial artifacts')
    meta['processing_complete'] = True
    save_json(out / 'metadata.json', meta)
    print(json.dumps({'output': str(out), 'processing_complete': True, 'content_read_status': 'not_read', 'frames': meta.get('visual', {}).get('frame_count'), 'segments': meta.get('asr', {}).get('segment_count')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
