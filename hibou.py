"""
KineKids AI - Le Hibou (rotation du cou) - version 100% Python (Optimisee)

Installation :
    pip install opencv-python mediapipe numpy

Lancement (exemples) :
    python hibou.py
    python hibou.py --seuil-epaule 18
    python hibou.py --cible 40 --limite 60 --maintien 3 --reps 8
    python hibou.py --kb            # test sans camera (touches A / D)
    python hibou.py --api http://localhost:8000/sessions/   # envoi du bilan au backend FastAPI

Touches : C = cadrage/recalibrer | S = "J'ai mal / Stop" | ESPACE = forcer depart | Q = quitter
"""
import os
import sys
import warnings

# Suppression des avertissements TensorFlow / Protobuf dans la console
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GLOG_minloglevel"] = "3"
warnings.filterwarnings("ignore")

import argparse
import json
import math
import subprocess
import threading
import time
import urllib.request
from datetime import datetime

import cv2
import numpy as np

# ------------------------------------------------------------------ PRESCRIPTION & CONFIG
ap = argparse.ArgumentParser()
ap.add_argument("--cible", type=float, default=35, help="amplitude cible (deg)")
ap.add_argument("--limite", type=float, default=55, help="limite de securite (deg)")
ap.add_argument("--maintien", type=float, default=3, help="temps de maintien (s)")
ap.add_argument("--reps", type=int, default=6, help="repetitions au total")
ap.add_argument("--vmax", type=float, default=40, help="vitesse max (deg/s)")
ap.add_argument("--cote", choices=["droite", "gauche", "both"], default="both")
ap.add_argument("--camera", type=int, default=0, help="index de la camera")
ap.add_argument("--gain", type=float, default=1.25, help="gain de l'angle de rotation")
ap.add_argument("--seuil-epaule", type=float, default=18.0, help="seuil de compensation des epaules (deg)")
ap.add_argument("--inv", action="store_true", help="inverser le sens")
ap.add_argument("--kb", action="store_true", help="mode clavier (A/D) sans camera")
ap.add_argument("--sans-son", action="store_true", help="desactiver les retours sonores")
ap.add_argument("--api", type=str, default=None, help="URL du backend FastAPI (POST /sessions/)")
ap.add_argument("--token", type=str, default=None, help="Token JWT pour l'authentification backend")
ap.add_argument("--patient-game-id", type=int, default=1, help="ID association patient-jeu pour l'API backend")
P = ap.parse_args()

W, H = 960, 600
TOL = 4          # tolerance sur la cible (deg)
NEUTRAL_ZONE = 7  # zone "tete droite" (deg)


# ------------------------------------------------------------------ AUDIO BIOFEEDBACK (macOS)
def play_sound(name):
    """Joue un son systeme macOS en arriere-plan (non bloquant)."""
    if P.sans_son:
        return
    def _play():
        path = f"/System/Library/Sounds/{name}.aiff"
        if os.path.exists(path):
            try:
                subprocess.run(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            except Exception:
                pass
    threading.Thread(target=_play, daemon=True).start()


# ------------------------------------------------------------------ DETECTION
class HeadTracker:
    """Estime la rotation gauche/droite (yaw) et position de la tete avec MediaPipe Face Mesh."""

    def __init__(self):
        import mediapipe as mp
        self.mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def track_info(self, frame_bgr, rgb=None):
        if rgb is None:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self.mesh.process(rgb)
        if not res.multi_face_landmarks:
            return None
        lm = res.multi_face_landmarks[0].landmark
        nose, left, right = lm[1], lm[234], lm[454]
        mid = (left.x + right.x) / 2
        half = abs(right.x - left.x) / 2
        if half < 1e-6:
            return None
        ratio = (nose.x - mid) / half * P.gain
        yaw = math.degrees(math.asin(max(-1, min(1, ratio))))
        h, w = frame_bgr.shape[:2]
        return {
            "yaw": yaw,
            "nose_pt": (int(nose.x * w), int(nose.y * h)),
            "nose_x": nose.x,
            "nose_y": nose.y,
            "face_width": abs(right.x - left.x),
        }

    def yaw(self, frame_bgr, rgb=None):
        info = self.track_info(frame_bgr, rgb)
        return info["yaw"] if info else None


class ShoulderTracker:
    """Detecte la stabilite des epaules en 2D (inclinaison, centrage et largeur) sans bruit de profondeur."""

    def __init__(self):
        import mediapipe as mp
        self.pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def track(self, frame_bgr, rgb=None):
        if rgb is None:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self.pose.process(rgb)
        if not res.pose_landmarks:
            return None
        lm = res.pose_landmarks.landmark
        l_sh = lm[11]  # epaule gauche anatomique
        r_sh = lm[12]  # epaule droite anatomique

        if getattr(l_sh, "visibility", 1.0) < 0.35 or getattr(r_sh, "visibility", 1.0) < 0.35:
            return None

        h, w = frame_bgr.shape[:2]
        lx_px, ly_px = l_sh.x * w, l_sh.y * h
        rx_px, ry_px = r_sh.x * w, r_sh.y * h
        dx_px = rx_px - lx_px
        dy_px = ry_px - ly_px

        # Inclinaison 2D en degres (calcul trigonometrique reel sur pixels)
        tilt = math.degrees(math.atan2(dy_px, max(1e-3, abs(dx_px))))
        cx = (l_sh.x + r_sh.x) / 2.0
        cy = (l_sh.y + r_sh.y) / 2.0
        width = abs(l_sh.x - r_sh.x)

        return {
            "tilt": tilt,
            "cx": cx,
            "cy": cy,
            "width": width,
            "left_pt": (int(lx_px), int(ly_px)),
            "right_pt": (int(rx_px), int(ry_px)),
        }


class HandTracker:
    """Detecte les gestes de la main (pouce stop, comptage de doigts) avec MediaPipe Hands."""

    def __init__(self):
        import mediapipe as mp
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.5
        )

    def process(self, frame_bgr, rgb=None):
        if rgb is None:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return self.hands.process(rgb)

    def detect_thumb_pain(self, res, shape):
        """Detecte si l'enfant montre un pouce franc vers le bas pour dire 'J'ai mal / Stop'."""
        if not res or not res.multi_hand_landmarks:
            return False, None
        lm = res.multi_hand_landmarks[0].landmark
        wrist = lm[0]
        h, w = shape[:2]

        folded = 0
        for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
            d_tip = math.hypot(lm[tip].x - wrist.x, lm[tip].y - wrist.y)
            d_pip = math.hypot(lm[pip].x - wrist.x, lm[pip].y - wrist.y)
            if d_tip < d_pip * 1.2:
                folded += 1

        thumb_down = (lm[4].y > lm[3].y) and (lm[4].y > lm[2].y) and (lm[4].y > wrist.y + 0.02)
        pos = (int(lm[9].x * w), int(lm[9].y * h))

        if folded >= 3 and thumb_down:
            return True, pos
        return False, pos

    def count_fingers(self, res):
        """Compte 0 a 5 doigts leves pour l'echelle de douleur."""
        if not res or not res.multi_hand_landmarks:
            return None
        lm = res.multi_hand_landmarks[0].landmark
        wrist = lm[0]
        n = 0
        for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
            if lm[tip].y < lm[pip].y:
                n += 1
        if lm[4].y < lm[2].y or (math.hypot(lm[4].x - wrist.x, lm[4].y - wrist.y) > 0.18):
            n += 1
        return n

    def count(self, frame_bgr):
        res = self.process(frame_bgr)
        return self.count_fingers(res)


# ------------------------------------------------------------------ ECRAN DE CADRAGE
def draw_cadrage_screen(frame, head_info, sh_data, align_progress, status_msg, is_aligned):
    """Affiche un grand cadre guide pour positionner la tete et les epaules."""
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = (35, 25, 20)  # Fond sombre élégant

    CW, CH = 580, 435
    CX, CY = (W - CW) // 2, 80

    if frame is not None:
        cam_view = cv2.resize(frame, (CW, CH))
    else:
        cam_view = np.zeros((CH, CW, 3), np.uint8)

    col_guide = (80, 235, 80) if is_aligned else (40, 180, 240)
    col_guide_dark = (40, 140, 40) if is_aligned else (20, 100, 140)

    # Silhouette cible (Gabarit tête + épaules)
    tgt_hx, tgt_hy = CW // 2, int(CH * 0.35)
    tgt_rx, tgt_ry = 50, 68
    cv2.ellipse(cam_view, (tgt_hx, tgt_hy), (tgt_rx, tgt_ry), 0, 0, 360, col_guide_dark, 2, cv2.LINE_AA)

    tgt_sy = int(CH * 0.72)
    tgt_sl, tgt_sr = int(CW * 0.22), int(CW * 0.78)
    cv2.line(cam_view, (tgt_sl, tgt_sy), (tgt_sr, tgt_sy), col_guide_dark, 2, cv2.LINE_AA)
    cv2.circle(cam_view, (tgt_sl, tgt_sy), 14, col_guide_dark, 2, cv2.LINE_AA)
    cv2.circle(cam_view, (tgt_sr, tgt_sy), 14, col_guide_dark, 2, cv2.LINE_AA)

    # Repères détectés
    if head_info is not None:
        hx = int(head_info["nose_x"] * CW)
        hy = int(head_info["nose_y"] * CH)
        cv2.circle(cam_view, (hx, hy), 10, col_guide, -1, cv2.LINE_AA)

    if sh_data is not None:
        sx1 = int(sh_data["left_pt"][0] * CW / frame.shape[1])
        sy1 = int(sh_data["left_pt"][1] * CH / frame.shape[0])
        sx2 = int(sh_data["right_pt"][0] * CW / frame.shape[1])
        sy2 = int(sh_data["right_pt"][1] * CH / frame.shape[0])
        cv2.line(cam_view, (sx1, sy1), (sx2, sy2), col_guide, 3, cv2.LINE_AA)
        cv2.circle(cam_view, (sx1, sy1), 10, col_guide, -1, cv2.LINE_AA)
        cv2.circle(cam_view, (sx2, sy2), 10, col_guide, -1, cv2.LINE_AA)

    thick = 4 if is_aligned else 2
    cv2.rectangle(cam_view, (0, 0), (CW - 1, CH - 1), col_guide, thick)

    if align_progress > 0:
        bar_w = int(CW * align_progress)
        cv2.rectangle(cam_view, (0, CH - 12), (bar_w, CH), (80, 235, 80), -1)

    img[CY:CY + CH, CX:CX + CW] = cam_view

    cv2.putText(img, "POSITIONNEMENT : PLACE TES EPAULES ET TA TETE", (CX - 40, 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.82, (255, 255, 255), 2, cv2.LINE_AA)

    bg_msg = (40, 140, 40) if is_aligned else (40, 40, 180)
    cv2.rectangle(img, (CX, CY + CH + 12), (CX + CW, CY + CH + 55), bg_msg, -1)
    cv2.rectangle(img, (CX, CY + CH + 12), (CX + CW, CY + CH + 55), (255, 255, 255), 1)
    cv2.putText(img, status_msg, (CX + 20, CY + CH + 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.putText(img, "Reste immobile pour calibrer | ESPACE : forcer | Q : quitter", (CX + 40, H - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 180, 180), 1, cv2.LINE_AA)

    return img


# ------------------------------------------------------------------ DESSIN JEU PRINCIPAL
def draw_scene(S, thumb):
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = (230, 202, 142)                                         # ciel (BGR)
    cv2.rectangle(img, (0, int(H * .8)), (W, H), (43, 62, 90), -1)   # sol
    cx = W // 2
    scale = 330 / P.limite                                           # px par degre
    cv2.rectangle(img, (cx - 14, 260), (cx + 14, int(H * .8)), (49, 74, 107), -1)  # tronc

    # souris cible
    if S["phase"] in ("reach", "neutral"):
        d = 1 if S["side"] == "droite" else -1
        mx = int(cx + d * P.cible * scale)
        col = (60, 60, 60) if S["phase"] == "reach" else (150, 150, 150)
        cv2.ellipse(img, (mx, 455), (28, 18), 0, 0, 360, col, -1)
        cv2.circle(img, (mx + d * 22, 448), 12, col, -1)
        cv2.circle(img, (mx + d * 28, 445), 3, (255, 255, 255), -1)
        cv2.line(img, (mx - d * 28, 458), (mx - d * 55, 470), col, 3)
        if S["phase"] == "reach" and S["hold"] > 0:
            frac = min(1, S["hold"] / P.maintien)
            cv2.ellipse(img, (mx, 440), (45, 45), -90, 0, 360 * frac, (3, 183, 255), 7)

    # hibou : la tete suit la rotation
    k = max(-1, min(1, S["yaw"] / P.limite))
    hx = int(cx + k * 80)
    cv2.ellipse(img, (cx, 340), (85, 110), 0, 0, 360, (72, 113, 164), -1)       # corps
    cv2.circle(img, (hx, 225), 78, (88, 138, 192), -1)                          # tete
    for s in (-1, 1):                                                           # oreilles
        pts = np.array([[hx + s * 68, 175], [hx + s * 42, 140], [hx + s * 25, 170]])
        cv2.fillPoly(img, [pts], (88, 138, 192))
    for s in (-1, 1):                                                           # yeux
        ex = int(hx + s * 32 + k * 12)
        cv2.circle(img, (ex, 220), 26, (255, 255, 255), -1)
        cv2.circle(img, (int(ex + k * 10), 220), 12, (20, 20, 20), -1)
    bx = int(hx + k * 12)
    cv2.fillPoly(img, [np.array([[bx - 10, 245], [bx + 10, 245], [bx, 270]])], (3, 183, 255))

    # jauge d'angle
    gy = 560
    cv2.rectangle(img, (int(cx - P.limite * scale), gy - 7), (int(cx + P.limite * scale), gy + 7), (90, 70, 40), -1)
    cv2.rectangle(img, (int(cx - P.limite * scale) - 50, gy - 7), (int(cx - P.limite * scale), gy + 7), (57, 70, 230), -1)
    cv2.rectangle(img, (int(cx + P.limite * scale), gy - 7), (int(cx + P.limite * scale) + 50, gy + 7), (57, 70, 230), -1)
    for s in (-1, 1):
        x = int(cx + s * P.cible * scale)
        cv2.rectangle(img, (x - 4, gy - 16), (x + 4, gy + 16), (143, 157, 42), -1)
    cv2.circle(img, (int(cx + S["yaw"] * scale), gy), 11, (255, 255, 255), -1)

    # texte d'instruction / alertes
    if S.get("shoulder_warn", False):
        cv2.rectangle(img, (20, 15), (W - 270, 70), (40, 40, 220), -1)
        cv2.rectangle(img, (20, 15), (W - 270, 70), (255, 255, 255), 2)
        cv2.putText(img, S["msg"], (30, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.88, (255, 255, 255), 2, cv2.LINE_AA)
    elif S.get("is_too_fast", False):
        cv2.rectangle(img, (20, 15), (W - 270, 70), (40, 140, 220), -1)
        cv2.rectangle(img, (20, 15), (W - 270, 70), (255, 255, 255), 2)
        cv2.putText(img, S["msg"], (30, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.88, (255, 255, 255), 2, cv2.LINE_AA)
    elif S.get("thumb_hold", 0.0) > 0.0:
        frac = min(1.0, S["thumb_hold"] / 1.2)
        cv2.rectangle(img, (20, 15), (W - 270, 70), (30, 110, 230), -1)
        cv2.rectangle(img, (20, 15), (W - 270, 70), (255, 255, 255), 2)
        cv2.putText(img, f"Pouce : J'ai mal / Stop ! {int(frac * 100)}%", (30, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.rectangle(img, (20, 66), (int(20 + (W - 290) * frac), 70), (255, 255, 255), -1)
    else:
        cv2.putText(img, S["msg"], (30, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.05, (255, 255, 255), 3, cv2.LINE_AA)

    cv2.putText(img, f"Rep {S['rep']}/{P.reps}   Angle {S['yaw']:+.0f} deg   Cible {P.cible:.0f} deg",
                (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(img, "Pouce bas : Stop | C: cadrage | S: J'ai mal | Q: quitter", (30, H - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    # miniature camera avec cadre de surveillance des epaules
    if thumb is not None:
        tw, th = 240, 180
        t = cv2.resize(thumb, (tw, th))
        is_warn = S.get("shoulder_warn", False)
        col_box = (40, 40, 240) if is_warn else (60, 220, 60)

        cv2.rectangle(t, (10, 10), (tw - 10, th - 10), col_box, 2)
        img[10:190, W - 250:W - 10] = t

        dev_sh = S.get("sh_dev", 0.0)
        status = "ATTENTION" if is_warn else "STABLE"
        cv2.putText(img, f"Epaules : {dev_sh:.0f} deg [{status}]", (W - 245, 210),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, col_box, 2, cv2.LINE_AA)
    return img


def draw_face(img, cx, cy, r, level):
    """Visage de l'echelle de douleur : level 0 (content) -> 4 (tres mal)."""
    cv2.circle(img, (cx, cy), r, (255, 255, 255), -1)
    cv2.circle(img, (cx, cy), r, (60, 60, 60), 3)
    cv2.circle(img, (cx - r // 3, cy - r // 4), 6, (0, 0, 0), -1)
    cv2.circle(img, (cx + r // 3, cy - r // 4), 6, (0, 0, 0), -1)
    my = cy + r // 2
    if level <= 1:      # sourire
        cv2.ellipse(img, (cx, cy + r // 6), (r // 2, r // 3 + (6 if level == 0 else 0)), 0, 10, 170, (0, 0, 0), 3)
    elif level == 2:    # neutre
        cv2.line(img, (cx - r // 3, my), (cx + r // 3, my), (0, 0, 0), 3)
    else:               # triste
        cv2.ellipse(img, (cx, my + r // 4), (r // 2, r // 4 + (8 if level == 4 else 0)), 0, 190, 350, (0, 0, 0), 3)


def pain_screen(cap, tracker=None):
    """Echelle de douleur : l'enfant montre 1 a 5 doigts (maintenir 1,4 s) ou touche 0 a 5."""
    values = [0, 2, 5, 8, 10]
    counter = tracker if tracker is not None else (HandTracker() if cap is not None else None)
    HOLD = 1.4
    cand, since = None, time.time()
    while True:
        thumb, n = None, None
        if cap is not None:
            ok, frame = cap.read()
            if ok:
                thumb = cv2.flip(frame, 1)
                n = counter.count(thumb)

        if n is not None and 1 <= n <= 5 and n == cand:
            held = time.time() - since
        else:
            cand, since, held = (n if n is not None and 1 <= n <= 5 else None), time.time(), 0.0

        if cand is not None and held >= HOLD:
            play_sound("Glass")
            return values[cand - 1]

        img = np.full((H, W, 3), (70, 50, 38), np.uint8)
        cv2.putText(img, "As-tu eu mal ?", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(img, "Montre avec tes doigts (1 = pas mal ... 5 = tres mal) ou touche 0 a 5", (40, 125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        for i in range(5):
            x = 130 + i * 175
            if cand == i + 1:
                cv2.circle(img, (x, 360), 88, (3, 183, 255), -1)
                cv2.ellipse(img, (x, 360), (100, 100), -90, 0, 360 * min(1, held / HOLD), (255, 255, 255), 8)
            draw_face(img, x, 360, 65, i)
            cv2.putText(img, str(i + 1), (x - 12, 490), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 3, cv2.LINE_AA)
        if thumb is not None:
            img[150:330, W - 260:W - 20] = cv2.resize(thumb, (240, 180))
        cv2.imshow("KineKids - Hibou", img)

        k = cv2.waitKey(10) & 0xFF
        if k == ord("0"):
            return 0
        if ord("1") <= k <= ord("5"):
            return values[k - ord("1")]
        if k in (ord("q"), 27):
            return None


# ------------------------------------------------------------------ JEU
def next_side(i):
    if P.cote == "both":
        return "droite" if i % 2 == 0 else "gauche"
    return P.cote


def main():
    tracker = None
    shoulder_tracker = None
    hand_tracker = None
    cap = None
    if not P.kb:
        cap = cv2.VideoCapture(P.camera)
        if not cap.isOpened():
            print("Camera introuvable. Verifie l'index avec --camera ou utilise le mode clavier --kb.")
            return
        tracker = HeadTracker()
        shoulder_tracker = ShoulderTracker()
        hand_tracker = HandTracker()

    start_time = time.time()
    frame_count = 0

    init_phase = "reach" if P.kb else "cadrage"
    S = dict(
        phase=init_phase, msg="", yaw=0.0, prev=0.0, speed=0.0, raw=0.0, neutral=0.0,
        calib=[],
        sh_tilt=0.0, sh_cx=0.5, sh_width=0.35,
        neutral_sh_tilt=0.0, neutral_sh_cx=0.5, neutral_sh_width=0.35,
        calib_sh_tilt=[], calib_sh_cx=[], calib_sh_width=[],
        sh_dev=0.0,
        align_hold=0.0,
        shoulder_warn=False, shoulder_warn_t=0.0, shoulder_comp=0, was_shoulder_warn=False,
        thumb_hold=0.0, last_thumb_pain=False, last_thumb_pos=None,
        rep=0, side=next_side(0), hold=0.0, neutral_t=0.0,
        rep_max=0.0, max_r=0.0, max_l=0.0, fast=0, was_fast=False, is_too_fast=False,
        over=0, log=[], stopped=False
    )
    last = time.time()

    while True:
        now = time.time()
        dt = max(1e-3, min(now - last, 0.1))
        last = now
        thumb, face_ok = None, True
        head_info = None
        sh_data = None
        frame_count += 1

        # ---- lecture de l'angle
        if P.kb:
            k = cv2.waitKey(1) & 0xFF
            if k == ord("a"): S["raw"] -= 1.2
            elif k == ord("d"): S["raw"] += 1.2
            else: S["raw"] *= 0.97
        else:
            ok, frame = cap.read()
            if not ok:
                print("Lecture camera impossible.")
                break
            frame = cv2.flip(frame, 1)          # effet miroir
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            head_info = tracker.track_info(frame, rgb=rgb)
            y = head_info["yaw"] if head_info else None
            sh_data = shoulder_tracker.track(frame, rgb=rgb)

            # Optimisation CPU : evaluation de la main 1 image sur 3 en jeu
            if frame_count % 3 == 0:
                h_res = hand_tracker.process(frame, rgb=rgb)
                thumb_pain, thumb_pos = hand_tracker.detect_thumb_pain(h_res, frame.shape)
                S["last_thumb_pain"] = thumb_pain
                S["last_thumb_pos"] = thumb_pos
            else:
                thumb_pain = S.get("last_thumb_pain", False)
                thumb_pos = S.get("last_thumb_pos", None)

            # Geste Pouce d'arret / douleur (maintien franc de 1.2s hors phase de cadrage)
            if thumb_pain and S["phase"] != "cadrage":
                S["thumb_hold"] += dt
                if thumb_pos:
                    cv2.circle(frame, thumb_pos, 22, (30, 110, 230), -1)
                    cv2.putText(frame, "STOP", (thumb_pos[0] - 18, thumb_pos[1] + 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2)
                if S["thumb_hold"] >= 1.2:
                    play_sound("Sosumi")
                    S["stopped"] = True
                    break
            else:
                S["thumb_hold"] = max(0.0, S["thumb_hold"] - dt * 2.5)

            if y is None:
                face_ok = False
            else:
                S["raw"] = -y if P.inv else y

            # Lissage des epaules en 2D pour une stabilite clinique absolue
            if sh_data is not None:
                if len(S["calib_sh_tilt"]) == 0 and S["phase"] == "cadrage":
                    S["sh_tilt"] = sh_data["tilt"]
                    S["sh_cx"] = sh_data["cx"]
                    S["sh_width"] = sh_data["width"]
                else:
                    S["sh_tilt"] += (sh_data["tilt"] - S["sh_tilt"]) * 0.20
                    S["sh_cx"] += (sh_data["cx"] - S["sh_cx"]) * 0.20
                    S["sh_width"] += (sh_data["width"] - S["sh_width"]) * 0.20

            # Analyse de compensation reelle des epaules pendant le jeu
            shoulder_warn = False
            if sh_data is not None and S["phase"] not in ("cadrage", "calib"):
                # 1. Haussement / inclinaison de la ligne d'epaules (en degres)
                dev_tilt = abs(S["sh_tilt"] - S["neutral_sh_tilt"])
                # 2. Bascule laterale du buste
                dev_shift = abs(S["sh_cx"] - S["neutral_sh_cx"]) * 100 * 1.5
                # 3. Rotation du buste (retrecissement perspectif 2D)
                ref_w = max(1e-4, S["neutral_sh_width"])
                ratio = min(1.0, max(0.4, S["sh_width"] / ref_w))
                dev_rot = math.degrees(math.acos(ratio))

                S["sh_dev"] = max(dev_tilt, dev_shift, dev_rot)

                is_deviating = (S["sh_dev"] > P.seuil_epaule)
                if is_deviating:
                    S["shoulder_warn_t"] += dt
                    if S["shoulder_warn_t"] >= 0.45:
                        shoulder_warn = True
                else:
                    S["shoulder_warn_t"] = max(0.0, S["shoulder_warn_t"] - dt * 2.0)
                    if S["shoulder_warn_t"] > 0.15:
                        shoulder_warn = S["shoulder_warn"]
            else:
                S["sh_dev"] = 0.0

            if shoulder_warn and not S["was_shoulder_warn"]:
                S["shoulder_comp"] += 1
                play_sound("Basso")
            S["was_shoulder_warn"] = shoulder_warn
            S["shoulder_warn"] = shoulder_warn

            # Dessin des reperes epaules sur l'image
            if sh_data is not None:
                sh_col = (40, 40, 240) if shoulder_warn else (60, 220, 60)
                cv2.line(frame, sh_data["left_pt"], sh_data["right_pt"], sh_col, 3)
                cv2.circle(frame, sh_data["left_pt"], 7, sh_col, -1)
                cv2.circle(frame, sh_data["right_pt"], 7, sh_col, -1)
            thumb = frame
            k = cv2.waitKey(1) & 0xFF

        if k == ord("q"):
            return
        if k == ord("s"):
            S["stopped"] = True
            break
        if k == ord("c"):
            # Retour au cadrage
            S.update(phase="cadrage", align_hold=0.0, calib=[], calib_sh_tilt=[], calib_sh_cx=[], calib_sh_width=[],
                     shoulder_warn=False, shoulder_warn_t=0.0)

        # ------------------------------------------------------------- PHASE DE CADRAGE
        if S["phase"] == "cadrage":
            is_aligned = False
            status_msg = "Place-toi devant la camera"

            if not face_ok:
                status_msg = "Place ton visage face a l'ecran"
            elif sh_data is None:
                status_msg = "Recule un peu pour montrer tes epaules"
            else:
                w_sh = sh_data["width"]
                cx_sh = sh_data["cx"]
                ny = head_info["nose_y"]

                if w_sh < 0.22:
                    status_msg = "Avance un peu vers la camera"
                elif w_sh > 0.60:
                    status_msg = "Recule un peu de l'ecran"
                elif cx_sh < 0.38:
                    status_msg = "Decale-toi un peu vers la droite"
                elif cx_sh > 0.62:
                    status_msg = "Decale-toi un peu vers la gauche"
                elif ny < 0.16:
                    status_msg = "Baisse la camera ou incline l'ecran"
                elif ny > 0.55:
                    status_msg = "Redresse-toi bien droit"
                else:
                    is_aligned = True

            # Progression du maintien dans le cadre
            if is_aligned:
                S["align_hold"] += dt
                S["calib"].append(S["raw"])
                if sh_data is not None:
                    S["calib_sh_tilt"].append(S["sh_tilt"])
                    S["calib_sh_cx"].append(S["sh_cx"])
                    S["calib_sh_width"].append(S["sh_width"])
                left_s = max(0.0, 1.3 - S["align_hold"])
                status_msg = f"Parfait ! Reste immobile... {left_s:.1f} s"
                if S["align_hold"] >= 1.3 or k == 32:  # ESPACE pour forcer
                    S["neutral"] = float(np.mean(S["calib"])) if S["calib"] else 0.0
                    if S["calib_sh_tilt"]:
                        S["neutral_sh_tilt"] = float(np.median(S["calib_sh_tilt"]))
                    if S["calib_sh_cx"]:
                        S["neutral_sh_cx"] = float(np.median(S["calib_sh_cx"]))
                    if S["calib_sh_width"]:
                        S["neutral_sh_width"] = float(np.median(S["calib_sh_width"]))
                    S["phase"] = "neutral"
                    S["neutral_t"] = 0.0
                    play_sound("Tink")
            else:
                S["align_hold"] = max(0.0, S["align_hold"] - dt * 2.0)
                if k == 32:  # Touche ESPACE pour forcer le demarrage
                    S["neutral"] = S["raw"]
                    if sh_data is not None:
                        S["neutral_sh_tilt"] = S["sh_tilt"]
                        S["neutral_sh_cx"] = S["sh_cx"]
                        S["neutral_sh_width"] = S["sh_width"]
                    S["phase"] = "neutral"
                    play_sound("Tink")

            frac = min(1.0, S["align_hold"] / 1.3)
            cadrage_img = draw_cadrage_screen(thumb, head_info, sh_data, frac, status_msg, is_aligned)
            cv2.imshow("KineKids - Hibou", cadrage_img)
            continue

        # ------------------------------------------------------------- PHASES DU JEU
        if face_ok:
            a = S["raw"] - S["neutral"]
            S["yaw"] += (a - S["yaw"]) * 0.3                         # lissage
            inst = abs(S["yaw"] - S["prev"]) / dt
            S["speed"] += (inst - S["speed"]) * 0.2                  # vitesse lissee
            S["prev"] = S["yaw"]
        else:
            S["hold"] = 0.0                                          # reset si visage perdu

        # Gestion propre de la vitesse (front montant)
        is_too_fast = (S["speed"] > P.vmax) and (S["phase"] == "reach")
        if is_too_fast and not S["was_fast"]:
            S["fast"] += 1
            play_sound("Pop")
        S["was_fast"] = is_too_fast
        S["is_too_fast"] = is_too_fast

        # Logique de jeu
        d = 1 if S["side"] == "droite" else -1
        ang = S["yaw"] * d

        if not face_ok:
            S["msg"] = "Je ne vois pas ton visage"
        elif S["shoulder_warn"]:
            S["hold"] = 0.0                                          # bloque le maintien en cas de triche
            S["msg"] = "Attention : garde tes epaules fixes !"
        elif is_too_fast:
            S["hold"] = 0.0
            S["msg"] = "Doucement ! Tourne lentement"
        elif S["phase"] == "neutral":
            S["msg"] = "Remets la tete droite"
            if abs(S["yaw"]) < NEUTRAL_ZONE:
                S["neutral_t"] += dt
                if S["neutral_t"] > 0.6:
                    S.update(phase="reach", hold=0.0, rep_max=0.0)
            else:
                S["neutral_t"] = 0.0
        elif S["phase"] == "reach":
            S["rep_max"] = max(S["rep_max"], ang)
            if ang > P.limite:
                S["over"] += 1
                S["hold"] = 0.0
                S["msg"] = "Trop loin, reviens un peu"
            elif ang >= P.cible - TOL:
                if S["hold"] == 0.0:
                    play_sound("Ping")                               # signal audio : cible atteinte !
                S["hold"] += dt
                S["msg"] = f"Super, ne bouge plus ! {max(0, P.maintien - S['hold']):.1f} s"
                if S["hold"] >= P.maintien:
                    S["rep"] += 1
                    play_sound("Hero")                               # signal audio : repetition reussie !
                    m = min(S["rep_max"], P.limite)
                    if S["side"] == "droite": S["max_r"] = max(S["max_r"], m)
                    else: S["max_l"] = max(S["max_l"], m)
                    S["log"].append(dict(rep=S["rep"], cote=S["side"], amplitude=round(m, 1)))
                    if S["rep"] >= P.reps:
                        break
                    S.update(side=next_side(S["rep"]), phase="neutral", neutral_t=0.0)
            else:
                S["hold"] = 0.0
                S["msg"] = "Tourne doucement vers la souris " + ("->" if d == 1 else "<-")

        cv2.imshow("KineKids - Hibou", draw_scene(S, thumb))

    # ---- fin de seance
    pain = pain_screen(cap, hand_tracker) if not P.kb else None
    if pain is None and S["stopped"]:
        pain = "arret (J'ai mal)"
    report(S, pain, start_time, cap, hand_tracker)
    if cap:
        cap.release()
    cv2.destroyAllWindows()


def report(S, pain, start_time, cap=None, hand_tracker=None):
    mr, ml = S["max_r"], S["max_l"]
    max_val = max(mr, ml)
    if P.cote in ("droite", "gauche"):
        sym = None
        sym_str = "N/A (unilateral)"
    else:
        sym = round(100 * min(mr, ml) / max_val) if max_val > 0 else 0
        sym_str = f"{sym} %"

    duration_sec = max(1, int(time.time() - start_time))

    rep = dict(
        date=datetime.now().isoformat(timespec="seconds"),
        duree_sec=duration_sec,
        prescription=dict(cible=P.cible, limite=P.limite, maintien=P.maintien,
                          reps=P.reps, vmax=P.vmax, cote=P.cote, seuil_epaule=P.seuil_epaule),
        repetitions_reussies=S["rep"], amplitude_max_droite=round(mr, 1), amplitude_max_gauche=round(ml, 1),
        symetrie_pct=sym, mouvements_trop_rapides=S["fast"], depassements_limite=S["over"],
        compensations_epaules=S["shoulder_comp"],
        douleur=pain, detail=S["log"])

    # bilan a l'ecran
    img = np.full((H, W, 3), (70, 50, 38), np.uint8)
    lines = [
        "BILAN DE SEANCE",
        f"Duree : {duration_sec}s | Repetitions : {S['rep']}/{P.reps}",
        f"Droite max : {mr:.0f} deg   Gauche max : {ml:.0f} deg",
        f"Symetrie : {sym_str}",
        f"Mouvements trop rapides : {S['fast']}   Depassements limite : {S['over']}",
        f"Compensations epaules : {S['shoulder_comp']}",
        f"Douleur evaluee : {pain}",
        "",
        "Appuie sur une touche pour fermer"
    ]
    for i, t in enumerate(lines):
        cv2.putText(img, t, (70, 110 + i * 48), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)

    # sauvegarde JSON locale
    os.makedirs("sessions", exist_ok=True)
    path = os.path.join("sessions", f"seance_{datetime.now():%Y%m%d_%H%M%S}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    print(f"\nSeance enregistree : {path}")

    # envoi backend FastAPI conforme schema SessionCreate
    if P.api:
        try:
            payload = {
                "patient_game_id": P.patient_game_id,
                "duration_sec": duration_sec,
                "metrics": rep
            }
            req_headers = {"Content-Type": "application/json"}
            if P.token:
                req_headers["Authorization"] = f"Bearer {P.token}"
            req = urllib.request.Request(P.api, data=json.dumps(payload).encode(),
                                         headers=req_headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                print(f"Bilan envoye au backend FastAPI (status {response.status}).")
        except Exception as e:
            print("Envoi backend impossible :", e)

    # Affichage du bilan avec temporisation minimale pour laisser le temps de lire
    t0 = time.time()
    while True:
        cv2.imshow("KineKids - Hibou", img)
        k = cv2.waitKey(40) & 0xFF
        if k != 255:
            break
        # Fermeture par geste de main autorisee uniquement apres 3.0s de lecture
        if cap is not None and hand_tracker is not None and (time.time() - t0 > 3.0):
            ok, f = cap.read()
            if ok:
                f_flip = cv2.flip(f, 1)
                res = hand_tracker.process(f_flip)
                if res and res.multi_hand_landmarks:
                    time.sleep(0.4)
                    break


if __name__ == "__main__":
    main()