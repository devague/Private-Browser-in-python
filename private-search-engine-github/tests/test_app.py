import unittest
from unittest.mock import patch

import app as search_app


class PrivateSearchTests(unittest.TestCase):
    def setUp(self):
        search_app.app.config["TESTING"] = True
        self.client = search_app.app.test_client()

    def test_homepage_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Private Search", response.data)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_empty_query_is_rejected(self):
        response = self.client.post("/api/search", json={"query": "  "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_long_query_is_rejected(self):
        response = self.client.post("/api/search", json={"query": "x" * 301})
        self.assertEqual(response.status_code, 400)

    @patch("app.generate_answer", return_value=("Example answer [1]", None))
    @patch("app.search_web", return_value=[{
        "title": "Example",
        "url": "https://example.com/",
        "content": "An example result.",
        "engine": "test",
    }])
    def test_search_returns_sources_and_answer(self, mock_search, mock_answer):
        response = self.client.post("/api/search", json={"query": "example"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["answer"], "Example answer [1]")
        self.assertEqual(payload["sources"][0]["url"], "https://example.com/")
        mock_search.assert_called_once_with("example")
        mock_answer.assert_called_once()

    @patch("app.search_web", side_effect=OSError("connection refused"))
    def test_unavailable_searxng_returns_clear_error(self, mock_search):
        response = self.client.post("/api/search", json={"query": "example"})
        self.assertEqual(response.status_code, 502)
        self.assertIn("Cannot connect to SearXNG", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
