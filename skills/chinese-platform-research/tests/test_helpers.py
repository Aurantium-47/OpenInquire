"""Offline regressions; temporary evidence is retained, never recursively deleted."""
import hashlib
import io
from contextlib import redirect_stdout
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix='platform-research-tests-'))
        cls.video = load('read_video_local')
        cls.recent = load('research_recent')
        cls.media = cls.work / 'fixture.bin'
        cls.media.write_bytes(b'fixture' * 200000)
        cls.engine = cls.work / 'engine.py'
        cls.engine.write_text('# fixture; subprocess is mocked\n', encoding='utf-8')
        cls.model = cls.work / 'model'
        cls.model.mkdir()
        for name in ('config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt'):
            (cls.model / name).write_text('fixture', encoding='utf-8')

    def video_args(self, *extra):
        return ['helper', str(self.media), '--out', str(self.work / self._testMethodName), *extra]

    def test_streaming_hash_without_read_bytes(self):
        expected = hashlib.sha256(b'fixture' * 200000).hexdigest()
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('must stream')):
            self.assertEqual(self.video.file_sha256(self.media), expected)

    def test_srt_rounding_carries_seconds(self):
        self.assertEqual(self.video.srt_time(59.9996), '00:01:00,000')

    def test_invalid_frame_interval_leaves_no_output(self):
        for value in ('0', '-1', 'nan', 'inf'):
            with self.subTest(value=value), patch.object(sys, 'argv', self.video_args('--no-asr', '--frame-step', value)):
                with self.assertRaises(SystemExit) as exc:
                    self.video.main()
                self.assertEqual(exc.exception.code, 2)
        self.assertFalse((self.work / self._testMethodName).exists())

    def test_existing_output_is_untouched(self):
        out = self.work / self._testMethodName
        out.mkdir()
        sentinel = out / 'keep.txt'
        sentinel.write_text('keep', encoding='utf-8')
        with patch.object(sys, 'argv', self.video_args('--no-asr')):
            with self.assertRaises(SystemExit):
                self.video.main()
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'keep')
        self.assertEqual(list(out.iterdir()), [sentinel])

    def test_silent_media_rejected_before_output(self):
        probe = {'format': {'duration': '2'}, 'streams': [{'codec_type': 'video'}]}
        with patch.object(sys, 'argv', self.video_args('--model', str(self.model))), \
             patch.object(self.video.shutil, 'which', return_value='installed'), \
             patch.object(self.video, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(probe), '')):
            with self.assertRaises(SystemExit):
                self.video.main()
        self.assertFalse((self.work / self._testMethodName).exists())

    def test_missing_ffmpeg_leaves_no_output(self):
        with patch.object(sys, 'argv', self.video_args('--no-asr')), patch.object(self.video.shutil, 'which', return_value=None):
            with self.assertRaises(SystemExit):
                self.video.main()
        self.assertFalse((self.work / self._testMethodName).exists())

    def test_explicit_engine_forwards_exit_and_isolates_providers(self):
        args = ['helper', 'topic', '--out', str(self.work / 'reports'), '--engine', str(self.engine), '--preflight', '--summary']
        with patch.object(sys, 'argv', args), patch.dict(os.environ, {'OPENAI_API_KEY': 'test-only', 'BRAVE_API_KEY': 'test-only'}), \
             patch.object(self.recent.subprocess, 'run', return_value=subprocess.CompletedProcess([], 7)) as call:
            self.assertEqual(self.recent.main(), 7)
        command = call.call_args.args[0]
        env = call.call_args.kwargs['env']
        self.assertEqual(command[1], str(self.engine.resolve()))
        self.assertIn('hackernews,github', command)
        self.assertIn('--preflight', command)
        self.assertNotIn('OPENAI_API_KEY', env)
        self.assertNotIn('BRAVE_API_KEY', env)
        self.assertEqual(env['FROM_BROWSER'], 'off')

    def test_missing_engine_is_clear_error(self):
        args = ['helper', 'topic', '--out', str(self.work / 'reports'), '--engine', str(self.work / 'missing.py')]
        with patch.object(sys, 'argv', args), patch.object(self.recent.subprocess, 'run') as call:
            with self.assertRaises(SystemExit) as exc:
                self.recent.main()
        self.assertEqual(exc.exception.code, 2)
        call.assert_not_called()

    def test_relocated_install_finds_new_upstream_layout(self):
        checkout = self.work / 'relocated'
        engine = checkout / 'skills/last30days/scripts/last30days.py'
        engine.parent.mkdir(parents=True)
        engine.write_text('# fixture', encoding='utf-8')
        args = ['helper', 'topic', '--out', str(self.work / 'reports')]
        with patch.object(sys, 'argv', args), patch.dict(os.environ, {'LAST30DAYS_HOME': str(checkout)}), \
             patch.object(self.recent.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as call:
            self.assertEqual(self.recent.main(), 0)
        self.assertEqual(call.call_args.args[0][1], str(engine.resolve()))

    def test_summary_retains_full_evidence_and_discussion_links(self):
        out = self.work / self._testMethodName
        report = {'topic': 'fixture', 'source_status': {'hackernews': {'state': 'ok'}},
                  'ranked_candidates': [{'title': f'candidate {i}', 'url': f'https://example.org/{i}',
                    'source_items': [{'body': 'evidence ' * 2000,
                        'metadata': {'hn_url': f'https://news.ycombinator.com/item?id={i}'}}]}
                    for i in range(12)]}
        engine = self.work / 'summary-engine.py'
        engine.write_text('import sys; print(' + repr(json.dumps(report)) + '); print("diagnostic", file=sys.stderr)', encoding='utf-8')
        command = [sys.executable, str(engine)]
        # Two runs must preserve both reports, including candidates not printed.
        paths = []
        for _ in range(2):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = self.recent.run_summary(command, os.environ.copy(), out)
            summary = json.loads(stdout.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(summary['candidate_count'], 12)
            self.assertEqual(len(summary['candidates']), 8)
            self.assertEqual(summary['candidates'][0]['discussion_urls'], ['https://news.ycombinator.com/item?id=0'])
            path = Path(summary['raw_report'])
            paths.append(path)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')), report)
            self.assertIn('diagnostic', Path(summary['engine_log']).read_text(encoding='utf-8'))
            self.assertLess(len(stdout.getvalue()), len(path.read_text(encoding='utf-8')) // 5)
        self.assertNotEqual(*paths)

    def test_summary_preserves_partial_failure(self):
        report = {'source_status': {'github': {'state': 'error'}}, 'ranked_candidates': []}
        command = [sys.executable, '-c', 'import sys; print(' + repr(json.dumps(report)) + '); sys.exit(7)']
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = self.recent.run_summary(command, os.environ.copy(), self.work / self._testMethodName)
        summary = json.loads(stdout.getvalue())
        self.assertEqual(code, 7)
        self.assertEqual(summary['source_status']['github']['state'], 'error')

    def test_summary_reports_invalid_engine_output(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = self.recent.run_summary([sys.executable, '-c', 'print("not JSON")'],
                                           os.environ.copy(), self.work / self._testMethodName)
        summary = json.loads(stdout.getvalue())
        self.assertNotEqual(code, 0)
        self.assertIn('output_error', summary)
        self.assertEqual(Path(summary['raw_report']).read_text(encoding='utf-8').strip(), 'not JSON')


if __name__ == '__main__':
    unittest.main()
