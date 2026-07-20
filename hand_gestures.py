import cv2
import math
import librosa
import numpy as np
import mediapipe as mp
import time as clock
import sounddevice as sd
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python import vision
from mediapipe.tasks import python
from collections import deque
from velocity import Velocity
# Note: Your camera setup and while loop remain exactly the same up to the detector



def draw_landmarks_on_image(rgb_image, detection_result):
    pose_landmarks_list = detection_result.pose_landmarks
    annotated_image = np.copy(rgb_image)

    pose_landmark_style = drawing_styles.get_default_pose_landmarks_style()
    pose_connection_style = drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2)

    for pose_landmarks in pose_landmarks_list:
        drawing_utils.draw_landmarks(
            image=annotated_image,
            landmark_list=pose_landmarks,
            connections=vision.PoseLandmarksConnections.POSE_LANDMARKS,
            landmark_drawing_spec=pose_landmark_style,
            connection_drawing_spec=pose_connection_style)

    return annotated_image


BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode
# Create a pose landmarker instance with the video mode:
options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='pose_landmarker.task'),
    running_mode=VisionRunningMode.VIDEO)

detector = vision.PoseLandmarker.create_from_options(options)
cam = cv2.VideoCapture(0)
frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
rgb = np.empty((frame_height, frame_width, 3), dtype=np.uint8)  # reuse



framerate = cam.get(cv2.CAP_PROP_FPS)

class S:
    pos = 0
    note =0
    gain = 1.0
    target = 1.0
    underrun = 0

 
SR, BLOCK, BASE = 48000, 256, 0.15
stem = librosa.load("audio/output/htdemucs_6s/AC⧸DC - Highway to Hell (Official Video)_guitar.mp3", sr = SR, mono = True)[0].astype(np.float32)
fade = int(0.005 * SR)
stem[:fade]  *= np.linspace(0, 1, fade, dtype=np.float32)
stem[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
onset = librosa.onset.onset_detect(y=stem, sr=SR, units='samples', backtrack=True)
onsets = np.append(onset, len(stem))
ctrl = np.zeros(1, dtype=np.float32)

A = 1-np.exp(-BLOCK/(0.020*SR))
scratch = np.empty(BLOCK, dtype=np.float32)
ramp    = np.linspace(0, 1, BLOCK, dtype=np.float32)
def callback(outdata, frames, t, status):
    if status:
        S.underruns += 1

    end = S.pos + BLOCK

    if end <= len(stem):
        x = stem[S.pos:end]
        while S.note + 1 < len(onsets) and onsets[S.note + 1] <= end:
            S.note += 1
            S.target = float(ctrl[0])
    else:
        n = len(stem) - S.pos
        scratch[:n] = stem[S.pos:]
        scratch[n:] = stem[:BLOCK - n]
        x = scratch
        S.note = 0                        # restart, don't run the while loop
        S.target = float(ctrl[0])

    g0 = S.gain
    S.gain += A * (S.target - S.gain)

    out = outdata[:, 0]
    np.multiply(ramp, S.gain - g0, out=out)   # allocation-free ramp
    np.add(out, g0, out=out)
    np.multiply(out, x, out=out)

    S.pos = end % len(stem)


right, left = Velocity(), Velocity()
t0 = clock.perf_counter()

with sd.OutputStream(samplerate=SR, blocksize=BLOCK, channels=1,
                     dtype='float32', callback=callback):
    while True:
        t_now = clock.perf_counter()                    # ← 1
        ret, frame = cam.read()
        if not ret:
            break

        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, dst=rgb)
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int((t_now - t0) * 1000)         # relative baseline

        detection_result = detector.detect_for_video(img, timestamp_ms)
        has_velocity_data = False

        if res := detection_result.pose_landmarks:
            rw, lw = res[0][16], res[0][15]
            if rw.visibility < 0.5:              # ← model says it can't actually see it
                right.reset()
                ctrl[0] += 0.3 * (BASE - ctrl[0])
            else:
                r_wrist_x, r_wrist_y = rw.x * frame_width, rw.y * frame_height
                l_wrist_x, l_wrist_y = lw.x * frame_width, lw.y * frame_height

                r_speed = right.update(r_wrist_x, r_wrist_y, t_now)
                l_speed = left.update(l_wrist_x, l_wrist_y, t_now)

                ctrl[0] = float(np.clip(r_speed / 800.0, 0.15, 1.0))
                has_velocity_data = True                    # ← 2
        else:
            right.reset(); left.reset()
            ctrl[0] += 0.3 * (BASE - ctrl[0]) 
        annotated_img = draw_landmarks_on_image(img.numpy_view(), detection_result)
        cv2.cvtColor(annotated_img, cv2.COLOR_RGB2BGR, dst=annotated_img)

        if has_velocity_data:
            r_text = f"{r_speed:.0f} px/s | {right.angle:.0f}deg"
            l_text = f"{l_speed:.0f} px/s | {left.angle:.0f}deg"

            cv2.putText(annotated_img, r_text,
                        (int(r_wrist_x) + 15, int(r_wrist_y) - 15),   # ← 3
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(annotated_img, l_text,
                        (int(l_wrist_x) + 15, int(l_wrist_y) - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow('camera', annotated_img)
        if cv2.waitKey(1) == ord('q'):
            break
cam.release()
cv2.destroyAllWindows()
for i in range(4):
    cv2.waitKey(1)
