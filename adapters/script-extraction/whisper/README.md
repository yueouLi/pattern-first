# Adapter: whisper (video/audio transcription)

Called by `/cheat-learn-from` in Way b (the user provides a video file and lets the tool transcribe it).

> **Prefer Way a** (the user pastes the script text directly—simple + accurate). Way b (whisper) is only for when the user **can't find the script and only has the video**.

---

## What this adapter is for

Convert media files like mp4 / mov / mp3 into a text transcript, so Claude can read the benchmark account's scripts.

Most Douyin / Bilibili / YouTube videos **have no official subtitles**—getting the script can't avoid ASR (speech recognition). That's why this adapter exists.

---

## Install (one-time)

### Option A: whisper-cpp (**recommended**—fast, light, pure C++)

On a Mac M-series chip, a 3-minute video transcribes in 30-60 seconds.

```bash
# 1. install whisper-cpp
brew install whisper-cpp

# 2. install ffmpeg (whisper-cpp dependency, to extract audio from the video)
brew install ffmpeg

# 3. download a model (for Chinese, medium or large-v3 recommended, good accuracy + decent speed)
# whisper-cpp auto-downloads on first run, or manually:
mkdir -p ~/.whisper-cpp/models
cd ~/.whisper-cpp/models
# the medium model (~1.5GB)
curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin
```

### Option B: openai-whisper (the Python version, slower but with API compatibility)

```bash
pip install openai-whisper
brew install ffmpeg

# the model auto-downloads
```

### Option C: use a cloud API (no local model needed)

`/cheat-learn-from` doesn't directly support a cloud API for now—if you have an OpenAI / Azure / Aliyun ASR API key, you can modify `run.sh` yourself to use the cloud.

---

## Usage

cheat-learn-from calls it automatically, you don't need to run it manually. But if you want to test manually:

```bash
# transcribe a single video
bash run.sh <video_path> <output_dir>

# e.g.:
bash run.sh ~/Desktop/benchmark-account/some-video.mp4 ~/my-channel/samples/benchmark-account/abc123/
# → outputs ~/my-channel/samples/benchmark-account/abc123/transcript.md
```

## Output format

`transcript.md`:

```markdown
# Transcript: <video filename>

**Source**: <video file path>
**Transcribed at**: <ISO timestamp>
**Engine**: whisper-cpp medium / openai-whisper large / etc.
**Duration**: <video length>

---

[plain-text transcription, split into paragraphs (not subtitle format)]
```

> Note whisper's output subtitles are split by **sentence** (each sentence on its own line + a timestamp).
> run.sh strips the timestamps + merges short sentences into paragraphs, so Claude reads it like a script, not a subtitle table.

## Failure modes

| Symptom | Cause | Handling |
|---|---|---|
| `whisper-cpp: command not found` | not installed | run `brew install whisper-cpp` |
| `ffmpeg: command not found` | ffmpeg not installed | run `brew install ffmpeg` |
| garbled / many typos in the transcription | the video is English but used a Chinese model, or vice versa | change the `--language` param in `run.sh` |
| transcription slow (>10 minutes) | used a large model + no GPU/M-chip acceleration | switch to the medium model |
| Disk full | the model file is large (large-v3 ~3GB) | medium (~1.5GB) is enough |

## Stability level

★★★★—whisper is an open-source standard ASR, won't suddenly fail. Model updates are free, version-pinning is safe.

## Risk notes

- **TOS**: transcribing **benchmark-account videos you downloaded yourself** for personal learning reference is fair use; **don't** re-publish the transcription results
- **Privacy**: whisper runs entirely locally, sends no data to the cloud

## File manifest

```
adapters/script-extraction/whisper/
├── README.md           # this file
└── run.sh              # the wrapper cheat-learn-from calls
```

## Relationship with other adapters

- Like `adapters/perf-data/douyin-session/` and `adapters/trend-sources/*`, it's an optional cheat-on-content adapter
- Only called at `/cheat-learn-from --way b`—Way a (paste text) doesn't need it

## Note on the user downloading videos themselves

The tool **doesn't fetch videos directly**—to avoid TOS risk + anti-scraping maintenance cost. Recommend using:

- **Douyin**: third-party downloaders / Douyin PC version → copy the video link → paste into the downloader
- **Bilibili**: [BBDown](https://github.com/nilaoda/BBDown) / [you-get](https://github.com/soimort/you-get)
- **YouTube**: [yt-dlp](https://github.com/yt-dlp/yt-dlp) (the most powerful)
- **Xiaohongshu**: [xhs-downloader](https://github.com/JoeanAmier/XHS-Downloader)

After downloading, drop it at `samples/<benchmark-name>/<video-id>/source.mp4`—cheat-learn-from finds it automatically.
