"""
KineKids AI - Le Hibou (rotation du cou) - version 100% Python (Optimisee)

Installation :
    pip install opencv-python mediapipe numpy

Lancement (exemples) :
    python hibou.py
    python hibou.py --cible 40 --limite 60 --maintien 3 --reps 8 --cote both
    python hibou.py --kb            # test sans camera (touches A / D)
    python hibou.py --inv           # si le hibou tourne a l'envers
    python hibou.py --api http://localhost:8000/sessions   # envoi du bilan au backend

Touches : C = recalibrer | S = "J'ai mal / Stop" | Q = quitter
"""
import argparse
import json
import math
import os
import time
import urllib.request
from datetime import datetime

import cv2
import numpy as np

# ------------------------------------------------------------------ PRESCRIPTION
ap = argparse.ArgumentParser()
ap.add_argument("--cible", type=float, default=35, help="amplitude cible (deg)")
ap.add_argument("--limite", type=float, default=55, help="limite de securite (deg)")
ap.add_argument("--maintien", type=float, default=3, help="temps de maintien (s)")
ap.add_argument("--reps", type=int, default=6, help="repetitions au total")
ap.add_argument("--vmax", type=float, default=40, help="vitesse max (deg/s)")
ap.add_argument("--cote", choices=["droite", "gauche", "both"], default="both")
ap.add_argument("--camera", type=int, default=0, help="index de la camera")
ap.add_argument("--gain", type=float, default=1.25, help="gain de l'angle de rotation")
ap.add_argument("--seuil-epaule", type=float, default=18.0, help="seuil de rotation des epaules pour compensation (deg)")
ap.add_argument("--inv", action="store_true", help="inverser le sens")
ap.add_argument("--kb", action="store_true", help="mode clavier (A/D) sans camera")
ap.add_argument("--api", type=str, default=None, help="URL du backend (POST JSON)")
P = ap.parse_args()

W, H = 960, 600
TOL = 4          # tolerance sur la cible (deg)
NEUTRAL_ZONE = 7  # zone "tete droite" (deg)


# ------------------------------------------------------------------ DETECTION
class HeadTracker:
    """Estime la rotation gauche/droite (yaw) de la tete avec MediaPipe Face Mesh."""

    def __init__(self):
        import mediapipe as mp
        self.mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def yaw(self, frame_bgr, rgb=None):
        if rgb is None:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self.mesh.process(rgb)
        if not res.multi_face_landmarks:
            return None
        lm = res.multi_face_landmarks[0].landmark
        nose, left, right = lm[1], lm[234], lm[454]       # bout du nez, bords du visage
        mid = (left.x + right.x) / 2
        half = abs(right.x - left.x) / 2
        if half < 1e-6:
            return None
        ratio = (nose.x - mid) / half * P.gain
        return math.degrees(math.asin(max(-1, min(1, ratio))))


class ShoulderTracker:
    """Detecte la rotation et l'inclinaison des epaules avec MediaPipe Pose."""

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
        l_sh = lm[11]  # epaule gauche
        r_sh = lm[12]  # epaule droite

        if getattr(l_sh, "visibility", 1.0) < 0.35 or getattr(r_sh, "visibility", 1.0) < 0.35:
            return None

        h, w = frame_bgr.shape[:2]
        dx = max(1e-4, abs(l_sh.x - r_sh.x))
        dz = l_sh.z - r_sh.z
        yaw = math.degrees(math.atan2(dz, dx))
        tilt = math.degrees(math.atan2(r_sh.y - l_sh.y, dx))

        return {
            "yaw": yaw,
            "tilt": tilt,
            "left_pt": (int(l_sh.x * w), int(l_sh.y * h)),
            "right_pt": (int(r_sh.x * w), int(r_sh.y * h)),
        }


class HandTracker:
    """Detecte les gestes de la main (pouce pour douleur/stop, comptage de doigts) avec MediaPipe Hands."""

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
        """Detecte si l'enfant montre un pouce (vers le bas ou franc) pour dire 'J'ai mal / Stop'."""
        if not res or not res.multi_hand_landmarks:
            return False, None
        lm = res.multi_hand_landmarks[0].landmark
        wrist = lm[0]
        h, w = shape[:2]

        folded = 0
        for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
            d_tip = math.hypot(lm[tip].x - wrist.x, lm[tip].y - wrist.y)
            d_pip = math.hypot(lm[pip].x - wrist.x, lm[pip].y - wrist.y)
            if d_tip < d_pip * 1.25:
                folded += 1

        thumb_down = (lm[4].y > lm[3].y) and (lm[4].y > lm[2].y) and (lm[4].y > wrist.y)
        pos = (int(lm[9].x * w), int(lm[9].y * h))

        if folded >= 2 and thumb_down:
            return True, pos
        if thumb_down and (lm[4].y - wrist.y > 0.07):
            return True, pos
        thumb_extended = (math.hypot(lm[4].x - wrist.x, lm[4].y - wrist.y) > 0.18)
        if folded >= 3 and thumb_extended:
            return True, pos
        return False, pos

    def count_fingers(self, res):
        """Compte 1 a 5 doigts leves pour l'echelle de douleur."""
        if not res or not res.multi_hand_landmarks:
            return None
        lm = res.multi_hand_landmarks[0].landmark
        n = 0
        for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
            if lm[tip].y < lm[pip].y:
                n += 1
        if lm[4].y < lm[2].y:
            n += 1
        return n if n >= 1 else None

    def count(self, frame_bgr):
        res = self.process(frame_bgr)
        return self.count_fingers(res)


# ------------------------------------------------------------------ DESSIN
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

    # texte
    if S.get("shoulder_warn", False):
        cv2.rectangle(img, (20, 15), (W - 270, 70), (40, 40, 220), -1)
        cv2.rectangle(img, (20, 15), (W - 270, 70), (255, 255, 255), 2)
        cv2.putText(img, S["msg"], (30, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.92, (255, 255, 255), 2, cv2.LINE_AA)
    elif S.get("thumb_hold", 0.0) > 0.0:
        frac = min(1.0, S["thumb_hold"] / 0.7)
        cv2.rectangle(img, (20, 15), (W - 270, 70), (30, 110, 230), -1)
        cv2.rectangle(img, (20, 15), (W - 270, 70), (255, 255, 255), 2)
        cv2.putText(img, f"Pouce : J'ai mal / Stop ! {int(frac * 100)}%", (30, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.92, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.rectangle(img, (20, 66), (int(20 + (W - 290) * frac), 70), (255, 255, 255), -1)
    else:
        cv2.putText(img, S["msg"], (30, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3, cv2.LINE_AA)
    cv2.putText(img, f"Rep {S['rep']}/{P.reps}   Angle {S['yaw']:+.0f} deg   Cible {P.cible:.0f} deg",
                (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(img, "Pouce main : J'ai mal/Stop | C: recalibrer | Q: quitter", (30, H - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    # miniature camera
    if thumb is not None:
        t = cv2.resize(thumb, (240, 180))
        img[10:190, W - 250:W - 10] = t
        if "sh_dev" in S:
            dev_sh = S["sh_dev"]
            is_warn = S.get("shoulder_warn", False)
            col_sh = (60, 60, 240) if is_warn else (100, 220, 100)
            status = "ATTENTION" if is_warn else "STABLE"
            cv2.putText(img, f"Epaules : {dev_sh:.0f} deg [{status}]", (W - 245, 210),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, col_sh, 2, cv2.LINE_AA)
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
    """Echelle de douleur : l'enfant montre 1 a 5 doigts (maintenir 1,5 s)."""
    values = [0, 2, 5, 8, 10]
    counter = tracker if tracker is not None else (HandTracker() if cap is not None else None)
    HOLD = 1.5
    cand, since = None, time.time()
    while True:
        thumb, n = None, None
        if cap is not None:
            ok, frame = cap.read()
            if ok:
                thumb = cv2.flip(frame, 1)
                n = counter.count(thumb)
        if n is not None and n == cand:
            held = time.time() - since
        else:
            cand, since, held = n, time.time(), 0.0
        if cand is not None and held >= HOLD:
            return values[cand - 1]

        img = np.full((H, W, 3), (70, 50, 38), np.uint8)
        cv2.putText(img, "As-tu eu mal ?", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(img, "Montre avec tes doigts : 1 = pas mal ... 5 = tres mal", (40, 125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        for i in range(5):
            x = 130 + i * 175
            if cand == i + 1:
                cv2.circle(img, (x, 360), 88, (3, 183, 255), -1)
                cv2.ellipse(img, (x, 360), (100, 100), -90, 0, 360 * min(1, held / HOLD), (255, 255, 255), 8)
            draw_face(img, x, 360, 65, i)
            cv2.putText(img, str(i + 1), (x - 12, 490), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 3, cv2.LINE_AA)
        if thumb is not None:
            img[150:330, W - 260:W - 20] = cv2.resize(thumb, (240, 180))
        if cap is None:
            cv2.putText(img, "Mode clavier : appuie sur 1 a 5", (40, 560), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow("KineKids - Hibou", img)

        k = cv2.waitKey(1) & 0xFF
        if ord("1") <= k <= ord("5"):
            return values[k - ord("1")]
        if k == ord("q"):
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
            print("Camera introuvable. Essaie --camera 1 ou le mode clavier --kb.")
            return
        tracker = HeadTracker()
        shoulder_tracker = ShoulderTracker()
        hand_tracker = HandTracker()

    S = dict(
        phase="calib", msg="", yaw=0.0, prev=0.0, speed=0.0, raw=0.0, neutral=0.0,
        calib=[], calib_t=time.time(),
        sh_yaw=0.0, sh_tilt=0.0, neutral_sh_yaw=0.0, neutral_sh_tilt=0.0,
        calib_sh_yaw=[], calib_sh_tilt=[], sh_dev=0.0,
        shoulder_warn=False, shoulder_warn_t=0.0, shoulder_comp=0, was_shoulder_warn=False,
        thumb_hold=0.0,
        rep=0, side=next_side(0), hold=0.0, neutral_t=0.0,
        rep_max=0.0, max_r=0.0, max_l=0.0, fast=0, over=0, log=[], stopped=False
    )
    last = time.time()

    while True:
        now = time.time()
        dt = max(1e-3, min(now - last, 0.1))
        last = now
        thumb, face_ok = None, True
        sh_data = None

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
            y = tracker.yaw(frame, rgb=rgb)
            sh_data = shoulder_tracker.track(frame, rgb=rgb)
            h_res = hand_tracker.process(frame, rgb=rgb)
            thumb_pain, thumb_pos = hand_tracker.detect_thumb_pain(h_res, frame.shape)

            # Detection du geste de pouce (douleur / stop)
            if thumb_pain:
                S["thumb_hold"] += dt
                if thumb_pos:
                    cv2.circle(frame, thumb_pos, 22, (30, 110, 230), -1)
                    cv2.putText(frame, "STOP", (thumb_pos[0] - 18, thumb_pos[1] + 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2)
                if S["thumb_hold"] >= 0.7:
                    S["stopped"] = True
                    break
            else:
                S["thumb_hold"] = max(0.0, S["thumb_hold"] - dt * 2.5)

            if y is None:
                face_ok = False
            else:
                S["raw"] = -y if P.inv else y

            # Lissage des epaules pour eliminer le bruit
            if sh_data is not None:
                if len(S["calib_sh_yaw"]) == 0 and S["phase"] == "calib":
                    S["sh_yaw"] = sh_data["yaw"]
                    S["sh_tilt"] = sh_data["tilt"]
                else:
                    S["sh_yaw"] += (sh_data["yaw"] - S["sh_yaw"]) * 0.25
                    S["sh_tilt"] += (sh_data["tilt"] - S["sh_tilt"]) * 0.25

            # Analyse de compensation des epaules avec confirmation temporelle
            shoulder_warn = False
            if sh_data is not None and S["phase"] != "calib":
                dev_yaw = abs(S["sh_yaw"] - S["neutral_sh_yaw"])
                dev_tilt = abs(S["sh_tilt"] - S["neutral_sh_tilt"])
                S["sh_dev"] = max(dev_yaw, dev_tilt)

                is_deviating = (dev_yaw > P.seuil_epaule or dev_tilt > 16.0)
                if is_deviating:
                    S["shoulder_warn_t"] += dt
                    if S["shoulder_warn_t"] >= 0.35:
                        shoulder_warn = True
                else:
                    S["shoulder_warn_t"] = max(0.0, S["shoulder_warn_t"] - dt * 2.5)
                    if S["shoulder_warn_t"] > 0.15:
                        shoulder_warn = S["shoulder_warn"]
            else:
                S["sh_dev"] = 0.0

            if shoulder_warn and not S["was_shoulder_warn"]:
                S["shoulder_comp"] += 1
            S["was_shoulder_warn"] = shoulder_warn
            S["shoulder_warn"] = shoulder_warn

            # Retour visuel sur les epaules
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
            S.update(phase="calib", calib=[], calib_sh_yaw=[], calib_sh_tilt=[],
                     shoulder_warn=False, shoulder_warn_t=0.0, calib_t=now)

        if face_ok:
            if S["phase"] == "calib":
                S["calib"].append(S["raw"])
                if sh_data is not None:
                    S["calib_sh_yaw"].append(S["sh_yaw"])
                    S["calib_sh_tilt"].append(S["sh_tilt"])
            a = S["raw"] - S["neutral"]
            S["yaw"] += (a - S["yaw"]) * 0.3                         # lissage
            inst = abs(S["yaw"] - S["prev"]) / dt
            S["speed"] += (inst - S["speed"]) * 0.2                  # vitesse lissee
            S["prev"] = S["yaw"]
        else:
            S["hold"] = 0.0                                          # reset si visage perdu

        # ---- logique du jeu
        d = 1 if S["side"] == "droite" else -1
        ang = S["yaw"] * d
        if not face_ok:
            S["msg"] = "Je ne vois pas ton visage"
        elif S["phase"] == "calib":
            left = 2 - (now - S["calib_t"])
            S["msg"] = f"Regarde droit devant toi... {max(0, math.ceil(left))}"
            if left <= 0:
                S["neutral"] = float(np.mean(S["calib"])) if S["calib"] else 0.0
                S["neutral_sh_yaw"] = float(np.median(S["calib_sh_yaw"])) if S["calib_sh_yaw"] else S["sh_yaw"]
                S["neutral_sh_tilt"] = float(np.median(S["calib_sh_tilt"])) if S["calib_sh_tilt"] else S["sh_tilt"]
                S["shoulder_warn"] = False
                S["shoulder_warn_t"] = 0.0
                S.update(yaw=0.0, prev=0.0, speed=0.0, phase="neutral", neutral_t=0.0)
        elif S["shoulder_warn"]:
            S["hold"] = 0.0                                          # bloque le maintien en cas de triche
            S["msg"] = "Attention : garde tes epaules fixes !"
        elif S["speed"] > P.vmax:
            S["fast"] += 1
            S["hold"] = 0.0
            S["msg"] = "Doucement !"
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
                S["hold"] += dt
                S["msg"] = f"Super, ne bouge plus ! {max(0, P.maintien - S['hold']):.1f} s"
                if S["hold"] >= P.maintien:
                    S["rep"] += 1
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
    report(S, pain, cap, hand_tracker)
    if cap:
        cap.release()
    cv2.destroyAllWindows()


def report(S, pain, cap=None, hand_tracker=None):
    mr, ml = S["max_r"], S["max_l"]
    max_val = max(mr, ml)
    sym = round(100 * min(mr, ml) / max_val) if max_val > 0 else 0
    
    rep = dict(
        date=datetime.now().isoformat(timespec="seconds"),
        prescription=dict(cible=P.cible, limite=P.limite, maintien=P.maintien,
                          reps=P.reps, vmax=P.vmax, cote=P.cote, seuil_epaule=P.seuil_epaule),
        repetitions_reussies=S["rep"], amplitude_max_droite=round(mr, 1), amplitude_max_gauche=round(ml, 1),
        symetrie_pct=sym, mouvements_trop_rapides=S["fast"], depassements_limite=S["over"],
        compensations_epaules=S["shoulder_comp"],
        douleur=pain, detail=S["log"])

    # bilan a l'ecran
    img = np.full((H, W, 3), (70, 50, 38), np.uint8)
    lines = ["BILAN DE SEANCE",
             f"Repetitions : {S['rep']}/{P.reps}",
             f"Droite max : {mr:.0f} deg   Gauche max : {ml:.0f} deg",
             f"Symetrie : {sym} %",
             f"Trop rapide : {S['fast']}   Depassements : {S['over']}",
             f"Compensations epaules : {S['shoulder_comp']}",
             f"Douleur : {pain}", "", "Montre ta main ou appuie sur une touche pour fermer"]
    for i, t in enumerate(lines):
        cv2.putText(img, t, (80, 120 + i * 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

    # sauvegarde JSON
    os.makedirs("sessions", exist_ok=True)
    path = os.path.join("sessions", f"seance_{datetime.now():%Y%m%d_%H%M%S}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    print(f"\nSeance enregistree : {path}")

    # envoi optionnel au backend
    if P.api:
        try:
            req = urllib.request.Request(P.api, data=json.dumps(rep).encode(),
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
            print("Bilan envoye au backend.")
        except Exception as e:
            print("Envoi impossible :", e)

    # Fermeture sans forcer a toucher au clavier
    t0 = time.time()
    while True:
        cv2.imshow("KineKids - Hibou", img)
        k = cv2.waitKey(30) & 0xFF
        if k != 255:
            break
        if cap is not None and hand_tracker is not None and (time.time() - t0 > 1.2):
            ok, f = cap.read()
            if ok:
                f_flip = cv2.flip(f, 1)
                res = hand_tracker.process(f_flip)
                if res and res.multi_hand_landmarks:
                    time.sleep(0.3)
                    break


if __name__ == "__main__":
    main()