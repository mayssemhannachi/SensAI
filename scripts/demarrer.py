"""Démarre la plateforme SensAI : backend (8000), dashboard thérapeute (8501), site (3000).

    Windows      : double-clic sur demarrer.bat — chaque service s'ouvre dans sa fenêtre
                   (fermer une fenêtre arrête le service correspondant).
    Mac / Linux  : ./demarrer.sh — Ctrl+C arrête les trois services.

Le navigateur s'ouvre ensuite sur http://localhost:3000.
"""

from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IS_WINDOWS = os.name == "nt"
VENV_PY = ROOT / ".venv" / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")
RUN_DIR = ROOT / ".run"


def port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def pids_on_port(port: int) -> set[int]:
    """Processus qui écoutent sur ``port`` (Windows : netstat ; Mac/Linux : lsof)."""
    pids: set[int] = set()
    try:
        if IS_WINDOWS:
            out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True).stdout
            for line in out.splitlines():
                parts = line.split()
                # Socket en écoute : adresse distante nulle (indépendant de la langue de Windows)
                if (len(parts) >= 5 and parts[1].endswith(f":{port}")
                        and parts[2] in {"0.0.0.0:0", "[::]:0", "*:*"}):
                    pids.add(int(parts[4]))
        else:
            out = subprocess.run(["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
                                 capture_output=True, text=True).stdout
            pids = {int(x) for x in out.split()}
            if not pids and shutil.which("fuser"):
                out = subprocess.run(["fuser", f"{port}/tcp"], capture_output=True, text=True).stdout
                pids = {int(x) for x in out.split() if x.isdigit()}
    except (OSError, ValueError):
        pass
    pids.discard(0)
    return pids


def _parent(pid: int) -> tuple[int, str]:
    """(PID parent, nom du parent) — pour arrêter aussi « npm run dev » qui relance le serveur."""
    try:
        if IS_WINDOWS:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}';"
                 "$q=Get-CimInstance Win32_Process -Filter ('ProcessId='+$p.ParentProcessId);"
                 "Write-Output ([string]$p.ParentProcessId+' '+$q.Name)"],
                capture_output=True, text=True, timeout=15).stdout.split()
        else:
            ppid = subprocess.run(["ps", "-o", "ppid=", "-p", str(pid)],
                                  capture_output=True, text=True).stdout.strip()
            name = subprocess.run(["ps", "-o", "args=", "-p", ppid],
                                  capture_output=True, text=True).stdout.strip()
            out = [ppid, name]
        return int(out[0]), " ".join(out[1:]).lower()
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        return 0, ""


def _kill(pid: int) -> None:
    if IS_WINDOWS:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def free_port(port: int) -> bool:
    """Arrête l'ancien service qui occupe ``port`` (ancienne version, autre dossier…)."""
    for pid in pids_on_port(port):
        # Remonte les parents node / npm (sinon « next dev » relance aussitôt son serveur).
        chain, current = [pid], pid
        for _ in range(3):
            parent, name = _parent(current)
            if parent <= 1 or not any(word in name for word in ("node", "npm", "next")):
                break
            chain.append(parent)
            current = parent
        for target in reversed(chain):
            _kill(target)
    for _ in range(20):
        if not port_busy(port):
            return True
        time.sleep(0.5)
    return False


def wait_for(url: str, seconds: int) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3):
                return True
        except Exception:  # noqa: BLE001
            time.sleep(1)
    return False


def services() -> list[dict]:
    npm = shutil.which("npm") or "npm"
    return [
        {"name": "Backend (API)", "port": 8000, "cwd": ROOT,
         "cmd": [str(VENV_PY), "-m", "uvicorn", "app.main:app", "--port", "8000"]},
        {"name": "Dashboard therapeute", "port": 8501, "cwd": ROOT / "data_analysis",
         "cmd": [str(VENV_PY), "-m", "streamlit", "run", "dashboard/app.py",
                 "--server.headless", "true", "--server.port", "8501"]},
        {"name": "Site SensAI", "port": 3000, "cwd": ROOT / "frontend",
         "cmd": [npm, "run", "dev"]},
    ]


def start_windows(service: dict) -> None:
    """Une fenêtre par service, qui reste ouverte si le service s'arrête (pour lire l'erreur)."""
    RUN_DIR.mkdir(exist_ok=True)
    script = RUN_DIR / f"{service['port']}.cmd"
    command = " ".join(f'"{part}"' if " " in part or "\\" in part else part for part in service["cmd"])
    if service["port"] == 3000:
        command = "call " + command  # npm est un script .cmd
    script.write_text(
        "@echo off\r\n"
        f"title SensAI - {service['name']} (port {service['port']})\r\n"
        f'cd /d "{service["cwd"]}"\r\n'
        f"{command}\r\n"
        "echo.\r\n"
        "echo Le service s'est arrete. Appuyez sur une touche pour fermer cette fenetre.\r\n"
        "pause >nul\r\n",
        encoding="ascii", errors="replace",
    )
    subprocess.Popen(["cmd", "/c", str(script)], creationflags=subprocess.CREATE_NEW_CONSOLE)


def main() -> int:
    if not VENV_PY.exists() or not (ROOT / "frontend" / "node_modules").exists() or not (ROOT / ".env").exists():
        print("Première utilisation : installation de la plateforme …\n")
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "installer.py")], cwd=ROOT)
        if result.returncode != 0:
            print("L'installation n'a pas abouti : corrigez l'erreur ci-dessus puis relancez demarrer.")
            return 1
        print()

    children: list[subprocess.Popen] = []
    for service in services():
        if port_busy(service["port"]):
            # Peut être une ancienne version (autre dossier) : on la remplace par celle-ci.
            print(f"  ~ {service['name']} : un ancien service occupe le port {service['port']}, arrêt …")
            if not free_port(service["port"]):
                print(f"  ! Impossible de libérer le port {service['port']} : fermez l'application qui l'utilise.")
                continue
        print(f"  > {service['name']} : démarrage (port {service['port']})")
        if IS_WINDOWS:
            start_windows(service)
        else:
            children.append(subprocess.Popen(service["cmd"], cwd=service["cwd"]))
        if service["port"] == 8000 and not wait_for("http://127.0.0.1:8000/health", 40):
            print("  ! Le backend ne répond pas : vérifiez que PostgreSQL est démarré.")

    print("\nPréparation du site (la première ouverture peut prendre une minute) …")
    if wait_for("http://localhost:3000/login", 180):
        webbrowser.open("http://localhost:3000")
        print("\nSensAI est prêt : http://localhost:3000")
        print("  Thérapeute de démo : demo@sensai.tn / demo1234")
        print("  Parent de démo     : salma.parent@sensai.tn / demo1234")
    else:
        print("Le site ne répond pas encore : ouvrez http://localhost:3000 dans quelques instants.")

    if IS_WINDOWS:
        print("\nPour arrêter : fermez les 3 fenêtres « SensAI - … ».")
        return 0

    print("\nCtrl+C pour tout arrêter.")
    try:
        while all(child.poll() is None for child in children):
            time.sleep(1)
        print("Un service s'est arrêté : arrêt des autres.")
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:
                child.send_signal(signal.SIGINT)
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
