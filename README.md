# LiveJam

Play a song with your body. LiveJam watches you through your webcam and lets you
"conduct" an isolated instrument stem in real time — swing your right hand faster and
the guitar swells; hold still and it settles back to a quiet baseline. The audio is
gated to the track's own note onsets, so your gestures feel like they're driving the
performance instead of just riding a volume fader.

## Demo


https://github.com/user-attachments/assets/91358fab-e549-4292-8104-a57415433ff3


## How it works

```
YouTube URL ──► download_audio.py ──► audio/<title>.mp3
                                          │
                                          ▼
                              music_separation.py  (Demucs)
                                          │
                    audio/output/.../<title>_guitar.mp3  (+ drums, no_guitar, ...)
                                          │
                                          ▼
   webcam ──► MediaPipe Pose ──► right-wrist velocity ──► live gain ──► speakers
                              (hand_gestures.py + velocity.py)
```

1. **`download_audio.py`** — pulls the best audio for a YouTube URL with `yt-dlp` and
   saves an MP3 into `audio/`.
2. **`music_separation.py`** — runs [Demucs](https://github.com/adefossez/demucs) to
   split the track into stems, writing the isolated **guitar** (`htdemucs_6s`) and
   **drums** (`mdx_extra`) stems into `audio/output/`.
3. **`hand_gestures.py`** — the live app. It opens the webcam, runs MediaPipe's pose
   landmarker (`pose_landmarker.task`), measures how fast your **right wrist** moves,
   and maps that speed to the gain of the guitar stem. A background `sounddevice`
   callback streams the audio and applies gain changes **at note onsets** (detected
   with `librosa`) so volume steps land musically. The camera window overlays the
   skeleton plus per-hand speed/angle.
4. **`velocity.py`** — a small `Velocity` helper that turns landmark positions into a
   smoothed, frame-rate-independent (dt-aware) speed and heading.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install opencv-python mediapipe librosa numpy sounddevice demucs yt-dlp
# ffmpeg is required by yt-dlp and demucs — install via your package manager
#   macOS: brew install ffmpeg   |   Debian/Ubuntu: sudo apt install ffmpeg
```

You also need the MediaPipe pose model, `pose_landmarker.task`, in the project root
(included here).

## Usage

```bash
# 1. Grab a track (edit the URL at the bottom of the file first)
python download_audio.py

# 2. Separate the guitar and drum stems (edit the input path in the file)
python music_separation.py

# 3. Jam. Stand back so your torso and arms are in frame, then move your right hand.
python hand_gestures.py     # press 'q' in the camera window to quit
```

> **Note:** the stem path in `hand_gestures.py` is currently hard-coded to the
> AC/DC sample track. Point it at your own separated stem to jam to a different song.


## Repo layout

| File | Role |
| --- | --- |
| `download_audio.py` | Download audio from YouTube (`yt-dlp`) |
| `music_separation.py` | Split a track into stems (`demucs`) |
| `hand_gestures.py` | Live webcam → gesture → audio-gain loop |
| `velocity.py` | Smoothed, dt-aware wrist-velocity estimator |
| `pose_landmarker.task` | MediaPipe pose model asset |

## Future directions — making it feel more *interactive*

Ideas, roughly ordered from quick wins to bigger builds, for turning the current
"one hand controls one fader" demo into something that feels like a real instrument:

**More expressive control**
- **Two-handed mixing** — the left hand is already tracked but unused for audio. Map
  the left wrist to a second stem (drums), a low-pass cutoff, or reverb send, so each
  hand shapes a different voice.
- **Vertical position → pitch/filter** — use wrist *height* (not just speed) to sweep
  a filter or transpose, giving a theremin-like continuous feel on top of the
  onset-gated dynamics.
- **Gesture vocabulary** — recognize discrete poses (fist, open palm, cross-arms) to
  mute/solo stems, trigger one-shots, or switch songs, using the angle/velocity data
  already available.

**Richer feedback loops**
- **On-screen mixer HUD** — draw live meters, the current gain per stem, and the next
  onset marker so players can *see* the beat they're playing into.
- **Beat & tempo sync** — detect the track's tempo and quantize gestures to the grid;
  flash the skeleton or screen edge on the downbeat for a call-and-response feel.
- **Haptic / visual reward** — particle bursts or color shifts when a fast swing lands
  exactly on an onset, reinforcing "good timing."

**Multiplayer & performance**
- **Multi-person pose** — MediaPipe can track several people; assign each player a stem
  so a group can "band" together in front of one camera.
- **Networked jam** — stream control values (not audio) between machines so remote
  players share one mix with low latency.
- **Record & replay** — capture a gesture take and its resulting automation, then let
  users layer passes to build up a full performance.

**Under the hood**
- **Any-song pipeline** — one entry point that takes a URL, runs download → separation
  → live jam, and lets you pick which stem to control from a menu (removing the
  hard-coded paths).
- **Config over code** — move tunables (visibility threshold, speed→gain curve, onset
  backtracking, smoothing `tau`) into a config file or on-screen sliders for live
  tweaking.
- **Latency & robustness** — add stem crossfade-looping, multi-person handling of the
  visibility gate, and an FPS/underrun readout to keep the experience smooth.
