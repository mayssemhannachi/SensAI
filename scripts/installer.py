"""Installation complète de la plateforme SensAI (backend, dashboard, site).

À lancer une seule fois après le clonage, depuis la racine du projet :
    Windows      : double-clic sur installer.bat   (ou : python scripts/installer.py)
    Mac / Linux  : ./installer.sh                  (ou : python3 scripts/installer.py)

Étapes : environnement Python + dépendances, fichier .env (connexion PostgreSQL),
création de la base, migrations, dépendances du site, données de démonstration.
Le script peut être relancé sans risque : il ne refait que ce qui manque.

Options :
    --password MOT_DE_PASSE  mot de passe PostgreSQL (sinon demandé)
    --db-name NOM            nom de la base (défaut : sensai_db)
    --yes                    répondre « oui » à tout (ex. données de démo)
    --no-demo                ne pas créer les données de démonstration
"""

from __future__ import annotations

import argparse
import getpass
import os
import secrets
import shutil
import subprocess
import sys
import time
import urllib.request
from urllib.parse import quote, unquote
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
DASHBOARD = ROOT / "data_analysis"
VENV = ROOT / ".venv"
IS_WINDOWS = os.name == "nt"
VENV_PY = VENV / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


# ─── Affichage ────────────────────────────────────────────────────────────────
def title(text: str) -> None:
    print(f"\n=== {text} ===", flush=True)


def ok(text: str) -> None:
    print(f"  [OK] {text}", flush=True)


def warn(text: str) -> None:
    print(f"  [!]  {text}", flush=True)


def fail(text: str) -> None:
    print(f"\n  [ERREUR] {text}\n", flush=True)
    sys.exit(1)


def run(cmd: list[str], cwd: Path = ROOT, quiet: bool = False) -> None:
    result = subprocess.run(
        cmd, cwd=cwd,
        stdout=subprocess.DEVNULL if quiet else None,
        stderr=subprocess.STDOUT if quiet else None,
    )
    if result.returncode != 0:
        fail(f"La commande a échoué : {' '.join(map(str, cmd))}")


def ask_yes(question: str, default: bool, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    suffix = " [O/n] " if default else " [o/N] "
    answer = input(question + suffix).strip().lower()
    return default if not answer else answer in {"o", "oui", "y", "yes"}


# ─── Étapes ───────────────────────────────────────────────────────────────────
def check_tools() -> str:
    title("1/6 Vérification des outils")
    if sys.version_info < (3, 11):
        fail(f"Python 3.11 ou plus récent est requis (version actuelle : {sys.version.split()[0]}).")
    ok(f"Python {sys.version.split()[0]}")
    npm = shutil.which("npm")
    if not npm:
        fail("Node.js n'est pas installé (npm introuvable). Installez la version LTS : https://nodejs.org")
    version = subprocess.run([npm, "--version"], capture_output=True, text=True).stdout.strip()
    ok(f"Node.js / npm {version}")
    return npm


def python_env() -> None:
    title("2/6 Environnement Python et dépendances")
    if not VENV_PY.exists():
        print("  Création de l'environnement .venv …", flush=True)
        run([sys.executable, "-m", "venv", str(VENV)])
    ok("Environnement .venv")
    print("  Installation des dépendances (quelques minutes la première fois) …", flush=True)
    run([str(VENV_PY), "-m", "pip", "install", "--upgrade", "pip"], quiet=True)
    run([str(VENV_PY), "-m", "pip", "install", "-r", "requirements.txt"], quiet=True)
    run([str(VENV_PY), "-m", "pip", "install", "-r", str(DASHBOARD / "requirements.txt")], quiet=True)
    ok("Dépendances du backend et du dashboard")


DB_CHECK = r"""
import sys, psycopg2
from psycopg2 import sql
host, port, user, password, name = sys.argv[1:6]
try:
    conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")
except Exception as error:
    print("CONNEXION:" + str(error).strip().splitlines()[0])
    sys.exit(2)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
if cur.fetchone():
    print("EXISTE")
else:
    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    print("CREEE")
"""


def database(args) -> None:
    title("3/6 Base de données PostgreSQL")
    env_file = ROOT / ".env"
    if env_file.exists():
        ok("Fichier .env déjà présent : il est conservé")
        url = next((line.split("=", 1)[1].strip() for line in env_file.read_text(encoding="utf-8").splitlines()
                    if line.startswith("DATABASE_URL=")), "")
        try:
            creds, location = url.split("://", 1)[1].rsplit("@", 1)
            user, password = creds.split(":", 1)
            password = unquote(password)
            hostport, name = location.split("/", 1)
            host, port = (hostport.split(":", 1) + ["5432"])[:2]
        except ValueError:
            fail("DATABASE_URL du fichier .env illisible. Supprimez .env et relancez l'installation.")
    else:
        host, port, user, name = "localhost", "5432", "postgres", args.db_name
        password = args.password
        if password is None:
            print("  PostgreSQL doit être installé et démarré (https://www.postgresql.org/download/).")
            password = getpass.getpass("  Mot de passe de l'utilisateur « postgres » : ")
        name = name.strip() or "sensai_db"

    result = subprocess.run([str(VENV_PY), "-c", DB_CHECK, host, port, user, password, name],
                            capture_output=True, text=True)
    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        detail = output.replace("CONNEXION:", "")
        fail("Connexion à PostgreSQL impossible.\n"
             f"           Détail : {detail}\n"
             "           Vérifiez que PostgreSQL est démarré et que le mot de passe est correct.")
    ok(f"Base « {name} » {'existante' if 'EXISTE' in output else 'créée'}")

    if not env_file.exists():
        example = (ROOT / ".env.example").read_text(encoding="utf-8")
        cors = next((line for line in example.splitlines() if line.startswith("CORS_ORIGINS=")),
                    'CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]')
        env_file.write_text(
            "# Généré par scripts/installer.py — ne pas publier ce fichier (il est ignoré par git)\n"
            f"DATABASE_URL=postgresql+psycopg2://{user}:{quote(password, safe='')}@{host}:{port}/{name}\n"
            f"SECRET_KEY={secrets.token_urlsafe(48)}\n"
            f"{cors}\n",
            encoding="utf-8",
        )
        ok("Fichier .env créé (avec une clé secrète aléatoire)")

    run([str(VENV_PY), "-m", "alembic", "upgrade", "head"], quiet=True)
    ok("Tables et catalogue de jeux à jour (migrations)")


def frontend(npm: str) -> None:
    title("4/6 Site SensAI (frontend)")
    print("  Installation des dépendances du site (quelques minutes la première fois) …", flush=True)
    run([npm, "install", "--no-audit", "--no-fund"], cwd=FRONTEND, quiet=True)
    ok("Dépendances du site")
    env_local = FRONTEND / ".env.local"
    if not env_local.exists():
        shutil.copyfile(FRONTEND / ".env.example", env_local)
        ok("Fichier frontend/.env.local créé")
    else:
        ok("Fichier frontend/.env.local déjà présent")


def wait_for(url: str, seconds: int) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2):
                return True
        except Exception:  # noqa: BLE001
            time.sleep(1)
    return False


def demo_data(args) -> None:
    title("5/6 Données de démonstration")
    if args.no_demo or not ask_yes("  Créer le compte de démonstration (thérapeute + 15 patients) ?", True, args.yes):
        warn("Ignoré. Vous pourrez le faire plus tard : voir le README.")
        return
    already_running = wait_for("http://127.0.0.1:8000/health", 1)
    server = None
    if not already_running:
        server = subprocess.Popen([str(VENV_PY), "-m", "uvicorn", "app.main:app", "--port", "8000"],
                                  cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_for("http://127.0.0.1:8000/health", 40):
            fail("Le backend n'a pas démarré. Lancez-le à la main pour voir l'erreur : voir le README.")
        run([str(VENV_PY), "scripts/seed_backend.py", "--register"], cwd=DASHBOARD)
    finally:
        if server:
            server.terminate()
            server.wait(timeout=15)


def done() -> None:
    title("6/6 Installation terminée")
    launcher = "demarrer.bat (double-clic)" if IS_WINDOWS else "./demarrer.sh"
    print(f"""
  Pour lancer la plateforme : {launcher}
  Puis ouvrir http://localhost:3000

  Compte thérapeute de démo : demo@sensai.tn / demo1234
  Compte parent de démo     : salma.parent@sensai.tn / demo1234
""")


def main() -> int:
    parser = argparse.ArgumentParser(description="Installation de la plateforme SensAI")
    parser.add_argument("--password", help="mot de passe PostgreSQL")
    parser.add_argument("--db-name", default="sensai_db")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--no-demo", action="store_true")
    args = parser.parse_args()

    print("SensAI — installation de la plateforme complète")
    npm = check_tools()
    python_env()
    database(args)
    frontend(npm)
    demo_data(args)
    done()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInstallation interrompue.")
        sys.exit(1)
