# TubeAlfred YouTube

Use TubeAlfred YouTube data and billing usage inside Hermes Agent.

This plugin gives Hermes read-only tools for YouTube videos, transcripts, comments, replies, channels, Shorts, playlists, community posts, search results, hashtags, autocomplete suggestions, URL resolution, and account billing usage.

## What You Can Ask Hermes

After installing the plugin, you can ask Hermes things like:

```text
Fetch the transcript for this YouTube video and summarize the key points:
https://www.youtube.com/watch?v=VIDEO_ID
```

```text
Fetch the latest videos from this YouTube channel and turn them into a table with title, URL, publish time, and view count:
@channel-handle
```

```text
Pull the first page of comments from this video and group the audience feedback by theme:
https://www.youtube.com/watch?v=VIDEO_ID
```

```text
Search YouTube for "YOUR KEYWORD" and compare the top results.
```

```text
Get YouTube autocomplete suggestions for "YOUR TOPIC".
```

## Requirements

- Hermes Agent installed locally.
- A TubeAlfred account.
- A TubeAlfred API key with `youtube.read` for YouTube tools and `billing.read` for billing usage.
- A configured Hermes model provider, so Hermes can run the agent.

If `hermes -z "hello"` fails with an inference provider error, run:

```bash
hermes model
```

## Get a TubeAlfred API Key

Open:

```text
https://tubealfred.com/app/api-keys
```

Then:

1. Choose **Create key**.
2. Select the scopes you need.
3. Copy the key immediately.

TubeAlfred only shows the full key once.

## Install

```bash
hermes plugins install tubealfred/tubealfred-youtube --enable
```

Hermes will ask for:

```text
TUBEALFRED_API_KEY
```

Paste the TubeAlfred key you created. Hermes stores it locally in your Hermes environment file.

If you already have the key in your shell:

```bash
export TUBEALFRED_API_KEY=ta_live_...
hermes plugins install tubealfred/tubealfred-youtube --enable
```

If you use Hermes gateway integrations, restart the gateway after installing:

```bash
hermes gateway restart
```

## Verify Install

```bash
hermes plugins list
hermes tools --summary list
```

You should see:

```text
tubealfred-youtube enabled
tubealfred_youtube enabled
```

## Quick Test

Run:

```bash
hermes -z "Use TubeAlfred to fetch video details for VIDEO_ID. Return the title, channel, and URL." -t tubealfred_youtube
```

Replace `VIDEO_ID` with the ID from any public YouTube video URL.

Expected result shape:

```text
Title: ...
Channel: ...
URL: ...
```

## Available Tools

Hermes can use these tools automatically when the `tubealfred_youtube` toolset is enabled:

| Tool | What it does |
| --- | --- |
| `tubealfred_billing_usage` | Fetch credit balance and billing usage. |
| `tubealfred_youtube_video_get` | Fetch video metadata. |
| `tubealfred_youtube_video_transcript` | Fetch a video transcript. |
| `tubealfred_youtube_comments_list` | Fetch the first comments page for a video. |
| `tubealfred_youtube_comments_page` | Fetch the next comments page. |
| `tubealfred_youtube_replies_list` | Fetch replies for a top-level comment. |
| `tubealfred_youtube_replies_page` | Fetch the next replies page. |
| `tubealfred_youtube_channel_get` | Fetch channel details. |
| `tubealfred_youtube_channel_about` | Fetch a channel about page. |
| `tubealfred_youtube_channel_videos` | Fetch recent channel videos. |
| `tubealfred_youtube_channel_shorts` | Fetch channel Shorts. |
| `tubealfred_youtube_channel_playlists` | Fetch channel playlists. |
| `tubealfred_youtube_channel_community` | Fetch channel community posts. |
| `tubealfred_youtube_search_query` | Search YouTube. |
| `tubealfred_youtube_search_hashtag` | Search YouTube by hashtag. |
| `tubealfred_youtube_search_suggest` | Fetch autocomplete suggestions. |
| `tubealfred_youtube_playlist_get` | Fetch playlist videos. |
| `tubealfred_youtube_url_resolve` | Resolve a YouTube URL to IDs. |

## Notes on API Keys

- The plugin needs `TUBEALFRED_API_KEY`.
- Use `youtube.read` for YouTube tools and `billing.read` for billing usage.
- Do not commit your key to a repository.
- Rotate the key if you paste it into a shared chat, issue, or log.

## Troubleshooting

### Hermes says no inference provider is configured

The plugin is installed, but Hermes cannot run an agent yet. Configure a model provider:

```bash
hermes model
```

### Hermes cannot see the tools

Check that the plugin and toolset are enabled:

```bash
hermes plugins list
hermes tools --summary list
```

If the plugin is installed but not enabled:

```bash
hermes plugins enable tubealfred-youtube
```

### Hermes says the API key is missing

Set the key in your shell:

```bash
export TUBEALFRED_API_KEY=ta_live_...
```

Or reinstall the plugin and paste the key when Hermes asks:

```bash
hermes plugins install tubealfred/tubealfred-youtube --enable --force
```

## For Developers

Repository layout:

```text
plugin.yaml      # Hermes manifest and API key prompt metadata
__init__.py      # register() wires schemas to handlers
schemas.py       # generic generated-schema and request adapter
generated_operations.py # generated tool catalog (do not edit)
contracts/       # vendored versioned TubeAlfred operation manifest
scripts/         # contract synchronization and drift checking
tools.py         # tool handlers and TubeAlfred HTTP client
tests/           # metadata and request mapping tests
```

Run tests:

```bash
python3 scripts/sync_contract.py --check --source contracts/tubealfred-youtube-operations.v1.json
python3 -m unittest discover -s tests
```

Tool names, schemas, paths, and `plugin.yaml` declarations are generated from the versioned platform contract. Run `python3 scripts/sync_contract.py` to refresh them from the published manifest.
