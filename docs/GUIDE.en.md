[Español](GUIA.md) | **English** | [Português](GUIA.pt.md)

# Clipper Live — Step-by-step guide

This guide explains, without jargon, how to install Clipper Live and use it to clip streams while they happen.
You don't need to know how to code: you talk to Claude and it takes care of the rest.

---

## 1. What Clipper Live does

Clipper Live watches a Twitch, Kick or YouTube stream **while it's live** and, every 30 minutes, hands you the best
moments already cut as vertical videos, ready for TikTok, Reels or Shorts.

Each clip comes with:

- the **streamer camera on top** and the **gameplay below** (1080×1920)
- a **hook title** written on the video
- **word-by-word captions**
- a `.txt` file with the **post caption**, **hashtags** and the stream **credit**

You just **approve** or **reject** each clip. Approved clips are kept; rejected ones are deleted.

### How it decides what a good moment is

1. It **records** the stream in 5-minute chunks.
2. It **listens** to everything the streamer says and turns it into text, on your own computer.
3. It **measures shouting**: it marks when the streamer got much louder than usual.
4. It **reads the chat**: it marks when people started typing much faster (or spamming "LOL", "CLIP"…).
5. Every 30 minutes, **Claude reads all of that**, scores each moment from 0 to 100 and picks the best ones.
6. The system **assembles the clips** and puts them in the queue for you to approve.

---

## 2. What you need

| You need | Details |
|---|---|
| A computer | Windows, Mac or Linux. 16 GB of RAM is comfortable; an NVIDIA graphics card is even better. |
| Claude Code | The Claude app (https://claude.com/download), **Code** tab. Pro plan or higher. |
| Disk space | About **3 GB** for the program + the space you reserve for recordings (**50 GB** recommended). |
| Internet | A stable connection. The system records the stream while you watch it. |
| Python | 3.10 or newer. On Windows the installer sets it up. On Mac, this guide tells you what to do. |

> **Free option?** It also runs with Ollama (local AI, no payment), but the moment picks are worse and you need a
> powerful computer (16 GB of RAM or more).

---

## 3. Installation (only once)

### Step 1 — Open Claude Code

Open the Claude app, go to the **Code** tab and pick any folder to work in (for example, a new folder called
`clips`).

### Step 2 — Ask for the installation

Type in the chat:

> install the clipper live in English: https://github.com/nexcorsair-create/Clipper-Live

Claude runs the installer. It takes 5 to 15 minutes the first time, because it downloads:

- **Streamlink** (records the stream)
- **yt-dlp** (downloads videos and YouTube chat)
- **ffmpeg** (builds the videos)
- **Whisper** (turns speech into text)
- the face detector (finds the streamer's camera)

At the end you'll see **ALL INSTALLED**.

> **If Python is missing:** on Windows the installer installs it and asks you to close and reopen the Claude app;
> then ask for the installation again. On Mac the Python website opens: click **Download Python**, install it and
> ask for the installation again.

> **Manual install** (if you'd rather not ask Claude), in Windows PowerShell:
> `$env:CLIPPER_LANG="en"; irm https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.ps1 | iex`
> On Mac/Linux, in the Terminal:
> `curl -fsSL https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.sh | CLIPPER_LANG=en bash`

### Step 3 — Choose the folder and the space

Claude asks you two questions:

1. **Which folder should recordings and clips go in?**
   Usually `C:\Users\YOUR-USER\clipper-live` (Windows) or `~/clipper-live` (Mac). An external drive with space is
   even better.
2. **How many GB can I use?**
   Each hour of 720p stream takes about 2 GB until it's analyzed. Cleanup automatically deletes what has already
   become a clip. **Recommended: 50 GB** (minimum 15).

Done: you can start watching streams.

### Step 4 — Permissions (important)

The first time Claude runs the program, the app asks whether to allow it. Choose **"always allow"** for
`clip.py`. That way Claude can work on its own for hours without asking you every time.

---

## 4. Watching a stream

### Step 1 — Send the link

Type in Claude:

> watch this stream: https://www.twitch.tv/CHANNEL-NAME

**Twitch** (`twitch.tv/channel`), **Kick** (`kick.com/channel`) and **YouTube** links (the stream link or
`youtube.com/@channel/live`) all work.

Don't know who to watch? Ask:

> find the biggest GTA 6 streams right now

Claude shows a list with how many people are watching each one, and you pick.

### Step 2 — Leave the computer on

From here on everything is automatic:

- If the stream **hasn't started yet**, the system waits (up to 8 hours).
- If the stream **drops**, it reconnects on its own.
- After **20 minutes with no signal**, it treats the stream as ended.
- The recorder keeps running even if you close the terminal window.

**Don't turn the computer off or let it sleep** while it's watching.

### Step 3 — Get and approve the clips

Every 30 minutes of stream, Claude shows you the new clips, for example:

```
#3  score 88  [01:12:03–01:12:41]  HE COULDN'T BELIEVE THE MAP SIZE
     shouts when he sees the whole map; chat exploded; stands on its own
     C:\Users\...\clipper-live\cortes\pendientes\003_channel.mp4
```

Open the video, watch it and reply:

> approve 3 and 5

> reject 4

- **Approved** → moved to `cortes/aprobados/`.
- **Rejected** → deleted right away.
- If you don't reply, the clip waits in `cortes/pendientes/` and Claude keeps working.

### Step 4 — Post

In `cortes/aprobados/STREAM-NAME/` each clip has its `.mp4` and its `.txt`. Copy the `.txt` text as the post
caption: it already has the hashtags and the credit to the streamer.

### Step 5 — Finish

When the stream ends, Claude gives you a summary (how many clips came out, how many you approved and where they
are). To stop earlier:

> stop watching

---

## 5. Useful phrases

| You want to… | Type |
|---|---|
| See how everything is going | "how's the stream going?" |
| See clips waiting for approval | "which clips are pending?" |
| Watch several streams at once | "watch these streams: LINK1 LINK2" |
| Analyze more often | "analyze every 20 minutes" |
| Be pickier | "only clips scored 80 or more" |
| More clips per block | "up to 5 clips per block" |
| Better video quality | "record in 1080p" (uses more space) |
| Change the language | "switch the language to Spanish" / "…to Portuguese" |
| Force an update | "update the clipper" |
| Clip a video that already ended | "clip this video: LINK" |

---

## 6. Where everything is

```
clipper-live/                       ← the folder you chose
├── cortes/
│   ├── pendientes/                 ← clips waiting for your approval
│   └── aprobados/
│       └── channel-2026-11-19/     ← approved clips from each stream (.mp4 + .txt)
└── lives/
    └── channel-2026-11-19/         ← recording, text, chat and blocks (cleaned up automatically)
```

The program itself is installed in `~/.clipper-live` (you don't need to touch it).

---

## 7. Disk space and cleanup

Clipper Live respects the GB you reserved:

- Recording that was **already analyzed and clipped** is deleted one hour later.
- If usage goes over **85%** of the reserved space, it deletes earlier.
- Over **95%**, it even deletes recording that hasn't been analyzed yet and warns you (a sign you should reserve more
  space).
- **Rejected** clips are deleted right away.
- **Approved** clips are **never deleted automatically**: once you've posted them, move them out of the folder.

---

## 8. Updates

You don't have to do anything. Every time you start watching a stream, if more than 12 hours have passed since the
last time, the system updates Streamlink, yt-dlp, Whisper and ffmpeg. Then it **tests that everything works**; if a
new version broke something, it rolls back automatically.

It never updates while a stream is being recorded.

To update Clipper Live itself (when a new version is on GitHub), ask:

> update the clipper live skill

---

## 9. Common problems

| You see… | What it means | What to do |
|---|---|---|
| "age-restricted" or "members only" | The site requires login to watch that stream. | Pick another stream. |
| "(no chat)" in the status | The platform blocked chat reading. | Nothing: clips keep coming from speech and volume. |
| "THE WATCHER CRASHED" | Something failed at startup (wrong link, site down…). | Check the link. If it's fine, ask "update the clipper" and watch again. |
| "SPACE: deleted recording not yet analyzed" | Too little space reserved, or Claude is behind. | Reserve more GB: "use 80 GB". |
| The stream is live but nothing records | Possibly a platform change. | Ask "update the clipper" and watch again. |
| A clip came out bad | The AI picked a bad moment. | "reject N". |

---

## 10. Limits (what it doesn't do)

- It doesn't record **members-only** or **age-restricted** streams.
- It decides from **speech, volume and chat**; it doesn't "see" the picture. A purely visual moment only gets in if
  the chat explodes.
- A clip comes out **30 to 40 minutes** after the moment (that's the analysis cycle).
- It **doesn't post** to social media: you post the approved clips.

---

## 11. Respect the streamers

Only clip streamers who allow it (many have an official clips channel or authorize it). Always keep the credit that
comes in each clip's `.txt`.
