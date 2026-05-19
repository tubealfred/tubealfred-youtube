import importlib.util
import types
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TOOLS = [
    "tubealfred_youtube_video_get",
    "tubealfred_youtube_video_transcript",
    "tubealfred_youtube_comments_list",
    "tubealfred_youtube_comments_page",
    "tubealfred_youtube_replies_list",
    "tubealfred_youtube_replies_page",
    "tubealfred_youtube_channel_get",
    "tubealfred_youtube_channel_about",
    "tubealfred_youtube_channel_videos",
    "tubealfred_youtube_channel_shorts",
    "tubealfred_youtube_channel_playlists",
    "tubealfred_youtube_channel_community",
    "tubealfred_youtube_search_query",
    "tubealfred_youtube_search_hashtag",
    "tubealfred_youtube_search_suggest",
    "tubealfred_youtube_playlist_get",
    "tubealfred_youtube_url_resolve",
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

        self.assertEqual(manifest_tools(), EXPECTED_TOOLS)
        self.assertEqual(runtime_tools, EXPECTED_TOOLS)
        self.assertEqual(len(set(runtime_tools)), len(EXPECTED_TOOLS))

    def test_request_specs_match_tubealfred_paths(self):
        plugin = load_plugin()
        by_name = {tool.name: tool for tool in plugin.TOOLS}

        video = by_name["tubealfred_youtube_video_get"].request({"video_id": "abc123"})
        self.assertEqual(video.path, "/v1/youtube/video/abc123")
        self.assertEqual(video.method, "GET")

        comments = by_name["tubealfred_youtube_comments_page"].request({
            "video_id": "abc123",
            "continuation_token": "token",
            "count": 50,
        })
        self.assertEqual(comments.method, "POST")
        self.assertEqual(comments.path, "/v1/youtube/video/abc123/comments/page")
        self.assertEqual(comments.body["continuation_token"], "token")
        self.assertEqual(comments.body["count"], 50)


if __name__ == "__main__":
    unittest.main()
