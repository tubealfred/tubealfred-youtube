import importlib.util
import json
import types
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
def expected_tools() -> list[str]:
    contract = json.loads(
        (ROOT / "contracts" / "tubealfred-youtube-operations.v1.json").read_text()
    )
    return [
        "tubealfred_billing_usage",
        *[operation["clients"]["agent_tool"]["name"] for operation in contract["operations"]],
    ]


def load_plugin():
    if "hermes_plugins" not in sys.modules:
        parent = types.ModuleType("hermes_plugins")
        parent.__path__ = []
        sys.modules["hermes_plugins"] = parent

    spec = importlib.util.spec_from_file_location(
        "hermes_plugins.tubealfred_youtube",
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def manifest_text() -> str:
    return (ROOT / "plugin.yaml").read_text()


def manifest_tools() -> list[str]:
    lines = manifest_text().splitlines()
    start = lines.index("provides_tools:")
    tools = []
    for line in lines[start + 1:]:
        if line.startswith("  - "):
            tools.append(line.removeprefix("  - ").strip())
        elif line and not line.startswith(" "):
            break
    return tools


class MetadataTests(unittest.TestCase):
    def test_manifest_uses_hermes_plugin_name(self):
        text = manifest_text()

        self.assertIn("manifest_version: 1", text)
        self.assertIn("name: tubealfred-youtube", text)
        self.assertIn("name: TUBEALFRED_API_KEY", text)
        self.assertIn("url: https://tubealfred.com/app/api-keys", text)
        self.assertIn("secret: true", text)

    def test_manifest_and_runtime_declare_same_tools(self):
        plugin = load_plugin()
        runtime_tools = [tool.name for tool in plugin.TOOLS]

        expected = expected_tools()

        self.assertEqual(manifest_tools(), expected)
        self.assertEqual(runtime_tools, expected)
        self.assertEqual(len(set(runtime_tools)), len(expected))

    def test_request_timeout_leaves_response_margin_above_api_timeout(self):
        load_plugin()
        tools = sys.modules["hermes_plugins.tubealfred_youtube.tools"]

        self.assertEqual(tools.TIMEOUT_SECONDS, 35)

    def test_request_specs_match_tubealfred_paths(self):
        plugin = load_plugin()
        by_name = {tool.name: tool for tool in plugin.TOOLS}

        billing = by_name["tubealfred_billing_usage"].request({})
        self.assertEqual(billing.path, "/v1/billing/usage")
        self.assertEqual(billing.method, "GET")

        video = by_name["tubealfred_youtube_video_get"].request({"video_id": "abc123"})
        self.assertEqual(video.path, "/v1/youtube/video/abc123")
        self.assertEqual(video.method, "GET")

        transcript = by_name["tubealfred_youtube_video_transcript"].request({
            "video_id": "abc123",
            "language": "en",
            "kind": "manual",
        })
        self.assertEqual(transcript.path, "/v1/youtube/video/abc123/transcript/fast")
        self.assertEqual(transcript.query["language"], "en")
        self.assertEqual(transcript.query["kind"], "manual")

        comments = by_name["tubealfred_youtube_comments_page"].request({
            "video_id": "abc123",
            "continuation_token": "token",
            "count": 50,
        })
        self.assertEqual(comments.method, "POST")
        self.assertEqual(comments.path, "/v1/youtube/video/abc123/comments/page")
        self.assertEqual(comments.body["continuation_token"], "token")
        self.assertEqual(comments.body["count"], 50)

        search = by_name["tubealfred_youtube_search_query"].request({
            "query": "how to learn faster",
            "upload_date": "month",
            "duration": "three_to_twenty_mins",
            "sort": "popularity",
            "type": "video",
            "features": "hd,subtitles",
            "live": True,
        })
        self.assertEqual(search.path, "/v1/youtube/search/")
        self.assertEqual(search.query["upload_date"], "month")
        self.assertEqual(search.query["duration"], "three_to_twenty_mins")
        self.assertEqual(search.query["sort"], "popularity")
        self.assertEqual(search.query["type"], "video")
        self.assertEqual(search.query["features"], "hd,subtitles")
        self.assertEqual(search.query["live"], True)
        self.assertNotIn("shorts", search.query)

        search_page = by_name["tubealfred_youtube_search_page"].request({
            "query": "how to learn faster",
            "continuation_token": "token",
            "channel_id": "@tubealfred",
        })
        self.assertEqual(search_page.method, "POST")
        self.assertEqual(search_page.path, "/v1/youtube/search/page")
        self.assertEqual(search_page.body["query"], "how to learn faster")
        self.assertEqual(search_page.body["continuation_token"], "token")
        self.assertEqual(search_page.body["channel_id"], "@tubealfred")

        batch = by_name["tubealfred_youtube_videos_batch"].request({
            "ids": ["dQw4w9WgXcQ"],
            "fields": "id,title",
        })
        self.assertEqual(batch.method, "POST")
        self.assertEqual(batch.path, "/v1/youtube/videos:batch")
        self.assertEqual(batch.query["fields"], "id,title")
        self.assertEqual(batch.body["ids"], ["dQw4w9WgXcQ"])

        with self.assertRaises(ValueError):
            by_name["tubealfred_youtube_search_query"].request({
                "query": "how to",
                "upload_date": "decade",
            })

        with self.assertRaises(ValueError):
            by_name["tubealfred_youtube_comments_list"].request({
                "video_id": "abc123",
                "count": 101,
            })


if __name__ == "__main__":
    unittest.main()
