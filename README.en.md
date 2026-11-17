[Español](README.md) | **English** | [Português](README.pt.md)

# Clipper Live

A free skill for Claude Code that **watches streams LIVE** and keeps cutting vertical clips while the streamer
plays. Built for the GTA 6 launch, but it works with any stream.

Send the stream link (Twitch, Kick or YouTube), leave the computer on, and every 30 minutes you get:

- vertical clips (1080×1920): streamer camera on top, gameplay below
- a hook title and word-by-word captions
- a `.txt` with the post caption, hashtags and stream credit

You approve or reject each clip. Approved clips go to a folder; rejected ones are deleted.

The system defaults to **Spanish** and also works in **English** and **Portuguese**.

📖 **[Step-by-step guide](docs/GUIDE.en.md)**: installation, usage, approving clips and troubleshooting.

## How it works

```
 stream ──► Streamlink records 5-min chunks ──► Whisper writes what's said + measures shouting
   └──────► chat reader (Twitch / YouTube / Kick) ──► marks where chat went wild
                              │
           every 30 min: a text block with [LOUD +12dB] [CHAT 3x] [LAUGH/HYPE]
                              │
              Claude reads it, scores it and picks the moments
                              │
     clip assembled (camera + gameplay + title + captions) ──► approval queue
                              │
     cleanup: deletes recordings already turned into clips, within the GB you reserved
```

- **Live recording with [Streamlink](https://github.com/streamlink/streamlink)**: skips Twitch ads, reconnects if
  the stream drops and waits for it to start (up to 8 h).
- **Listening on your computer** (faster-whisper). Uses an NVIDIA graphics card if you have one.
- **Live chat**: Twitch (no account needed), YouTube and Kick. If a platform blocks the chat, it keeps going with
  speech and volume.
- **Safe automatic updates**: Streamlink, yt-dlp, Whisper and ffmpeg update themselves every 12 h. If a new version
  breaks something, it rolls back.
- It also clips finished videos (VODs): just send the link.

## Installation

You need **Claude Code**: the app at https://claude.com/download, in the **Code** tab. It also runs for free with
Ollama, but the picks are worse.

Paste into Claude Code:

> install the clipper live in English: https://github.com/nexcorsair-create/Clipper-Live

Or run it directly (also used to update):

- **Windows (PowerShell):** `$env:CLIPPER_LANG="en"; irm https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.ps1 | iex`
- **Mac/Linux:** `curl -fsSL https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.sh | CLIPPER_LANG=en bash`

It checks Python, installs Streamlink, yt-dlp, ffmpeg and Whisper, tests everything and tells you when it's ready.
Then Claude asks **which folder to use** and **how many GB to reserve**. I recommend 50 GB: one hour of stream in
720p takes about 2 GB until it's analyzed.

### Changing the language

Tell Claude "switch the language to English", or run `clip.py configure --language en` (`es`, `en`, `pt`).

## Usage

- "watch this stream: https://twitch.tv/someone"
- "find the biggest GTA 6 streams right now"
- "approve 3 and 5" / "reject 4"
- "how's the stream going?" / "stop watching"

Clips are saved in `YOUR-FOLDER/cortes/pendientes` and, once approved, in `YOUR-FOLDER/cortes/aprobados`.

**Tip:** when Claude asks permission to run `clip.py`, choose "always allow". That way it works on its own for the
whole stream.

## Requirements

- Windows, Mac or Linux
- Python 3.10 or newer (the installer handles it on Windows)
- about 3 GB for the program and models, plus the GB reserved for recordings
- a stable internet connection (it records the stream while you watch)

## Limits

- Members-only or age-restricted streams can't be recorded (they require login).
- The system decides from speech, volume and chat; it doesn't "see" the picture. A purely visual moment only gets
  in if the chat explodes.
- A clip comes out 30 to 40 min after the moment (that's the analysis cycle). You can change it: "analyze every
  20 min".
- It doesn't post anything: you post the approved clips.

## Respect the streamers

Only clip streamers who allow it and keep the credit that comes in each clip's `.txt`.

## Credits

Workflow idea (listen to the stream, have the AI score it in blocks, camera on top and gameplay below) inspired by
[skill-clips](https://github.com/davixavier-coder/skill-clips) by Davi Xavier. Live recording with
[Streamlink](https://github.com/streamlink/streamlink); downloads with [yt-dlp](https://github.com/yt-dlp/yt-dlp);
listening with [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
