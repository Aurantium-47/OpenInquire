"""Offline regression checks for X pagination, provenance and credential handling."""
import os
import unittest
from unittest.mock import patch
import httpx
import server


class XSearchTests(unittest.TestCase):
    def test_missing_key_uses_browser_without_request(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(server, "_get_json") as get:
            result = server.search_x("IPO since:2025-07-31")
        get.assert_not_called()
        self.assertFalse(result["ok"])
        self.assertIn("since%3A2025-07-31", result["browser_fallback"])

    def test_small_limit_does_not_drop_posts_between_pages(self):
        payload = {"data": [{"id": str(i), "author_id": "a"} for i in range(10)],
                   "includes": {"users": [{"id": "a", "username": "example"}]},
                   "meta": {"next_token": "next"}}
        with patch.dict(os.environ, {"X_BEARER_TOKEN": "test-only"}), patch.object(
                server, "_get_json", return_value=payload) as get:
            result = server.search_x("IPO", 3, "previous")
        self.assertEqual(len(result["items"]), 10)
        self.assertEqual(get.call_args.kwargs["params"]["next_token"], "previous")
        self.assertEqual(get.call_args.kwargs["params"]["max_results"], 10)
        self.assertEqual(result["meta"]["next_token"], "next")
        self.assertEqual(result["items"][0]["author"]["username"], "example")
        self.assertEqual(result["items"][0]["url"], "https://x.com/i/web/status/0")

    def test_api_errors_are_not_success_or_secret_output(self):
        request = httpx.Request("GET", "https://api.x.com/2/tweets/search/recent")
        response = httpx.Response(401, request=request)
        error = httpx.HTTPStatusError("test-only-secret", request=request, response=response)
        with patch.dict(os.environ, {"X_BEARER_TOKEN": "test-only-secret"}), patch.object(
                server, "_get_json", side_effect=error):
            result = server.search_x("IPO")
        self.assertFalse(result["ok"])
        self.assertNotIn("test-only-secret", str(result))
        self.assertIn("401", result["error"])


if __name__ == "__main__":
    unittest.main()
