import os
import pickle
import numpy as np
import cv2
import face_recognition


# ---------- ORIGINAL HELPERS (left for compatibility) ----------

def load_known_faces(encodings_file='known_faces.dat'):
    if os.path.exists(encodings_file):
        with open(encodings_file, 'rb') as f:
            known_encodings, known_ids = pickle.load(f)
        return known_encodings, known_ids
    return [], []


def save_known_faces(encodings, ids, encodings_file='known_faces.dat'):
    with open(encodings_file, 'wb') as f:
        pickle.dump((encodings, ids), f)


def compare_faces(known_encodings, unknown_encoding, tolerance=0.6):
    distances = face_recognition.face_distance(known_encodings, unknown_encoding)
    return list(distances <= tolerance)


# ---------- NEW QUALITY + ALIGNMENT + MULTI-FRAME HELPERS ----------

def blur_score(bgr_image: np.ndarray) -> float:
    """Higher value = sharper image."""
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def brightness_score(bgr_image: np.ndarray) -> float:
    """Average brightness in [0, 255]."""
    hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    return float(np.mean(hsv[:, :, 2]))


def align_face_rgb(rgb_image: np.ndarray) -> np.ndarray:
    """
    Aligns a face by rotating so the eyes are horizontal.
    If landmarks can't be found, returns the original image.
    """
    landmarks_list = face_recognition.face_landmarks(rgb_image)
    if not landmarks_list:
        return rgb_image

    landmarks = landmarks_list[0]
    if 'left_eye' not in landmarks or 'right_eye' not in landmarks:
        return rgb_image

    left_eye = np.mean(landmarks['left_eye'], axis=0)
    right_eye = np.mean(landmarks['right_eye'], axis=0)

    dy = right_eye[1] - left_eye[1]
    dx = right_eye[0] - left_eye[0]
    angle = np.degrees(np.arctan2(dy, dx))

    eyes_center = (
        (left_eye[0] + right_eye[0]) / 2.0,
        (left_eye[1] + right_eye[1]) / 2.0,
    )

    M = cv2.getRotationMatrix2D(eyes_center, angle, 1.0)
    aligned = cv2.warpAffine(
        rgb_image,
        M,
        (rgb_image.shape[1], rgb_image.shape[0]),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return aligned


def aggregate_face_encoding_from_bgr_frames(frames_bgr):
    """
    Takes a list of BGR frames from webcam, filters out very blurry / too dark,
    aligns face, and returns ONE aggregated face encoding.

    Returns None if no usable face is detected.
    """
    encodings = []
    qualities = []

    for bgr in frames_bgr:
        if bgr is None:
            continue

        # Quality metrics
        blur = blur_score(bgr)
        brightness = brightness_score(bgr)

        # Filter really bad frames
        if blur < 40:          # very blurry
            continue
        if brightness < 35:    # almost black
            continue

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        aligned = align_face_rgb(rgb)

        locations = face_recognition.face_locations(aligned)
        if not locations:
            continue

        encoding = face_recognition.face_encodings(aligned, locations)[0]

        # Combine blur + brightness into a single "quality" score
        quality = blur + 0.3 * brightness
        encodings.append(encoding)
        qualities.append(quality)

    if not encodings:
        return None

    qualities = np.array(qualities, dtype=np.float32)
    # Normalize to weights
    weights = qualities / qualities.sum()

    enc_stack = np.stack(encodings, axis=0)
    aggregated = np.average(enc_stack, axis=0, weights=weights)

    print(
        f"--- [ML] Using {len(encodings)} good frames for multi-frame "
        f"encoding (best quality={qualities.max():.2f}) ---"
    )

    return aggregated
