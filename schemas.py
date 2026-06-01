"""Tool schemas and TubeAlfred API request mapping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import quote

PLUGIN_NAME = "tubealfred-youtube"
TOOLSET = "tubealfred_youtube"
VERSION = "0.1.2"
API_KEY_ENV = "TUBEALFRED_API_KEY"
MAX_COUNT = 500


@dataclass(frozen=True)
class RequestSpec:
    path: str
    method: str = "GET"
    query: dict[str, Any] | None = None
    body: dict[str, Any] | None = None


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    request: Callable[[dict[str, Any]], RequestSpec]


def _string_schema(description: str, *, min_length: int = 1) -> dict[str, Any]:
    return {"type": "string", "minLength": min_length, "description": description}


def _enum_schema(description: str, values: list[str]) -> dict[str, Any]:
    return {"type": "string", "enum": values, "description": description}


def _boolean_schema(description: str) -> dict[str, Any]:
    return {"type": "boolean", "description": description}


def _count_schema() -> dict[str, Any]:
    return {
        "type": "integer",
        "minimum": 1,
        "maximum": MAX_COUNT,
        "description": f"Number of items to fetch per page (1-{MAX_COUNT}).",
    }


def _continuation_schema(description: str) -> dict[str, Any]:
    return _string_schema(description)


def _object_schema(
    properties: dict[str, dict[str, Any]],
    required: list[str],
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _required_string(params: dict[str, Any], name: str) -> str:
    value = params.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required.")
    return value.strip()


def _optional_string(params: dict[str, Any], name: str) -> str | None:
    value = params.get(name)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string when provided.")
    return value.strip()


def _optional_enum(params: dict[str, Any], name: str, allowed: list[str]) -> str | None:
    value = params.get(name)
    if value is None:
        return None
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(allowed)}.")
    return value


def _optional_boolean(params: dict[str, Any], name: str) -> bool | None:
    value = params.get(name)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean.")
    return value


def _optional_count(params: dict[str, Any]) -> int | None:
    value = params.get("count")
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("count must be an integer.")
    if value < 1 or value > MAX_COUNT:
        raise ValueError(f"count must be between 1 and {MAX_COUNT}.")
    return value


def _path_arg(params: dict[str, Any], name: str) -> str:
    return quote(_required_string(params, name), safe="")


def _compact(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if value is not None}


VIDEO_ID = _string_schema("YouTube video ID.")
CHANNEL_ID = _string_schema("YouTube UC channel ID, @handle, or username.")
COMMENT_ID = _string_schema("Top-level YouTube comment ID returned by the comments endpoint.")
PLAYLIST_ID = _string_schema("YouTube playlist ID.")
CONTINUATION = _continuation_schema("Pagination continuation token from a previous TubeAlfred response.")

SEARCH_UPLOAD_DATE = ["all", "today", "week", "month", "year"]
SEARCH_DURATION = ["all", "under_three_mins", "three_to_twenty_mins", "over_twenty_mins"]
SEARCH_SORT = ["relevance", "popularity"]
SEARCH_TYPE = ["all", "video", "shorts", "channel", "playlist", "movie"]


TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="tubealfred_youtube_video_get",
        description="Fetch YouTube video details through TubeAlfred.",
        parameters=_object_schema({"video_id": VIDEO_ID}, ["video_id"]),
        request=lambda params: RequestSpec(
            path=f"/v1/youtube/video/{_path_arg(params, 'video_id')}",
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_video_transcript",
        description="Fetch a YouTube video transcript through TubeAlfred.",
        parameters=_object_schema({"video_id": VIDEO_ID}, ["video_id"]),
        request=lambda params: RequestSpec(
            path=f"/v1/youtube/video/{_path_arg(params, 'video_id')}/transcript/fast",
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_comments_list",
        description="Fetch the first YouTube comments page for a video through TubeAlfred.",
        parameters=_object_schema({"video_id": VIDEO_ID, "count": _count_schema()}, ["video_id"]),
        request=lambda params: RequestSpec(
            path=f"/v1/youtube/video/{_path_arg(params, 'video_id')}/comments",
            query=_compact({"count": _optional_count(params)}),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_comments_page",
        description="Fetch a paginated YouTube comments page through TubeAlfred.",
        parameters=_object_schema(
            {
                "video_id": VIDEO_ID,
                "continuation_token": _continuation_schema("Comment pagination continuation token returned by the previous comments response."),
                "count": _count_schema(),
            },
            ["video_id", "continuation_token"],
        ),
        request=lambda params: RequestSpec(
            method="POST",
            path=f"/v1/youtube/video/{_path_arg(params, 'video_id')}/comments/page",
            body=_compact({
                "continuation_token": _required_string(params, "continuation_token"),
                "count": _optional_count(params),
            }),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_replies_list",
        description="Fetch the first replies page for a top-level YouTube comment through TubeAlfred.",
        parameters=_object_schema(
            {"video_id": VIDEO_ID, "comment_id": COMMENT_ID, "count": _count_schema()},
            ["video_id", "comment_id"],
        ),
        request=lambda params: RequestSpec(
            path=f"/v1/youtube/video/{_path_arg(params, 'video_id')}/comments/{_path_arg(params, 'comment_id')}/replies",
            query=_compact({"count": _optional_count(params)}),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_replies_page",
        description="Fetch a paginated replies page for a top-level YouTube comment through TubeAlfred.",
        parameters=_object_schema(
            {
                "video_id": VIDEO_ID,
                "comment_id": COMMENT_ID,
                "continuation_token": _continuation_schema("Reply pagination continuation token returned by the previous replies response."),
                "count": _count_schema(),
            },
            ["video_id", "comment_id", "continuation_token"],
        ),
        request=lambda params: RequestSpec(
            method="POST",
            path=f"/v1/youtube/video/{_path_arg(params, 'video_id')}/comments/{_path_arg(params, 'comment_id')}/replies/page",
            body=_compact({
                "continuation_token": _required_string(params, "continuation_token"),
                "count": _optional_count(params),
            }),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_channel_get",
        description="Fetch YouTube channel details through TubeAlfred.",
        parameters=_object_schema({"channel_id": CHANNEL_ID}, ["channel_id"]),
        request=lambda params: RequestSpec(
            path=f"/v1/youtube/channel/{_path_arg(params, 'channel_id')}",
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_channel_about",
        description="Fetch a YouTube channel about section through TubeAlfred.",
        parameters=_object_schema({"channel_id": CHANNEL_ID}, ["channel_id"]),
        request=lambda params: RequestSpec(
            path=f"/v1/youtube/channel/{_path_arg(params, 'channel_id')}/about",
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_channel_videos",
        description="Fetch recent YouTube videos for a channel through TubeAlfred.",
        parameters=_object_schema({"channel_id": CHANNEL_ID, "continuation_token": CONTINUATION}, ["channel_id"]),
        request=lambda params: RequestSpec(
            path=f"/v1/youtube/channel/{_path_arg(params, 'channel_id')}/videos",
            query=_compact({"continuation_token": _optional_string(params, "continuation_token")}),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_channel_shorts",
        description="Fetch YouTube Shorts for a channel through TubeAlfred.",
        parameters=_object_schema({"channel_id": CHANNEL_ID, "continuation_token": CONTINUATION}, ["channel_id"]),
        request=lambda params: RequestSpec(
            path=f"/v1/youtube/channel/{_path_arg(params, 'channel_id')}/shorts",
            query=_compact({"continuation_token": _optional_string(params, "continuation_token")}),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_channel_playlists",
        description="Fetch YouTube channel playlists through TubeAlfred.",
        parameters=_object_schema({"channel_id": CHANNEL_ID, "continuation_token": CONTINUATION}, ["channel_id"]),
        request=lambda params: RequestSpec(
            path=f"/v1/youtube/channel/{_path_arg(params, 'channel_id')}/playlists",
            query=_compact({"continuation_token": _optional_string(params, "continuation_token")}),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_channel_community",
        description="Fetch YouTube channel community posts through TubeAlfred.",
        parameters=_object_schema({"channel_id": CHANNEL_ID, "continuation_token": CONTINUATION}, ["channel_id"]),
        request=lambda params: RequestSpec(
            path=f"/v1/youtube/channel/{_path_arg(params, 'channel_id')}/community",
            query=_compact({"continuation_token": _optional_string(params, "continuation_token")}),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_search_query",
        description="Search YouTube through TubeAlfred.",
        parameters=_object_schema(
            {
                "query": _string_schema("YouTube search query."),
                "upload_date": _enum_schema(
                    "Filter by upload date. One of: all, today, week, month, year.", SEARCH_UPLOAD_DATE
                ),
                "duration": _enum_schema(
                    "Filter by video duration. One of: all, under_three_mins, three_to_twenty_mins, over_twenty_mins.",
                    SEARCH_DURATION,
                ),
                "sort": _enum_schema("Search ranking preference. One of: relevance, popularity.", SEARCH_SORT),
                "type": _enum_schema(
                    "Restrict result type. One of: all, video, shorts, channel, playlist, movie.", SEARCH_TYPE
                ),
                "features": _string_schema(
                    "Comma-separated feature filters: hd, subtitles, creative_commons, 3d, live, purchased, 4k, 360, location, hdr, vr180."
                ),
                "live": _boolean_schema("Shortcut for features=live."),
                "shorts": _boolean_schema("Shortcut for type=shorts."),
                "continuation_token": CONTINUATION,
            },
            ["query"],
        ),
        request=lambda params: RequestSpec(
            path="/v1/youtube/search/",
            query=_compact({
                "query": _required_string(params, "query"),
                "upload_date": _optional_enum(params, "upload_date", SEARCH_UPLOAD_DATE),
                "duration": _optional_enum(params, "duration", SEARCH_DURATION),
                "sort": _optional_enum(params, "sort", SEARCH_SORT),
                "type": _optional_enum(params, "type", SEARCH_TYPE),
                "features": _optional_string(params, "features"),
                "live": _optional_boolean(params, "live"),
                "shorts": _optional_boolean(params, "shorts"),
                "continuation_token": _optional_string(params, "continuation_token"),
            }),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_search_hashtag",
        description="Search YouTube by hashtag through TubeAlfred.",
        parameters=_object_schema(
            {"hashtag": _string_schema("YouTube hashtag, with or without the # prefix."), "continuation_token": CONTINUATION},
            ["hashtag"],
        ),
        request=lambda params: RequestSpec(
            path="/v1/youtube/search/hashtag",
            query=_compact({
                "hashtag": _required_string(params, "hashtag"),
                "continuation_token": _optional_string(params, "continuation_token"),
            }),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_search_suggest",
        description="Fetch YouTube search autocomplete suggestions through TubeAlfred.",
        parameters=_object_schema(
            {
                "q": _string_schema("Partial search query.", min_length=2),
                "prev": _string_schema("Optional previous query context."),
            },
            ["q"],
        ),
        request=lambda params: RequestSpec(
            path="/v1/youtube/search/suggestions",
            query=_compact({
                "q": _required_string(params, "q"),
                "prev": _optional_string(params, "prev"),
            }),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_playlist_get",
        description="Fetch YouTube playlist contents through TubeAlfred.",
        parameters=_object_schema({"playlist_id": PLAYLIST_ID, "continuation_token": CONTINUATION}, ["playlist_id"]),
        request=lambda params: RequestSpec(
            path=f"/v1/youtube/playlist/{_path_arg(params, 'playlist_id')}",
            query=_compact({"continuation_token": _optional_string(params, "continuation_token")}),
        ),
    ),
    ToolDefinition(
        name="tubealfred_youtube_url_resolve",
        description="Resolve a YouTube URL to canonical identifiers through TubeAlfred.",
        parameters=_object_schema({"url": _string_schema("Full YouTube URL.")}, ["url"]),
        request=lambda params: RequestSpec(
            path="/v1/youtube/utility/resolve",
            query={"url": _required_string(params, "url")},
        ),
    ),
]
