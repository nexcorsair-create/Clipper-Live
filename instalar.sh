#!/usr/bin/env bash
# Instala (o actualiza) Clipper Live en Mac/Linux.
# Uso:           curl -fsSL https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.sh | bash
# In English:    curl -fsSL https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.sh | CLIPPER_LANG=en bash
# Em português:  curl -fsSL https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.sh | CLIPPER_LANG=pt bash
set -euo pipefail
REPO="nexcorsair-create/Clipper-Live"
RAMO="main"
SKILL="$HOME/.claude/skills/clipper-live"

L="$(printf '%s' "${CLIPPER_LANG:-es}" | tr '[:upper:]' '[:lower:]')"
case "$L" in es|en|pt) ;; *) L=es ;; esac
export CLIPPER_LANG="$L"
msg() {  # msg "español" "english" "português"
  case "$L" in en) echo "$2" ;; pt) echo "$3" ;; *) echo "$1" ;; esac
}

msg "== Clipper Live: instalando ==" "== Clipper Live: installing ==" "== Clipper Live: instalando =="
TMP="$(mktemp -d)"
msg "  ... descargando la skill de github.com/$REPO" "  ... downloading the skill from github.com/$REPO" \
    "  ... baixando a skill de github.com/$REPO"
curl -fsSL "https://github.com/$REPO/archive/refs/heads/$RAMO.tar.gz" | tar -xz -C "$TMP"
rm -rf "$SKILL"
mkdir -p "$(dirname "$SKILL")"
mv "$TMP"/*/ "$SKILL"
rm -rf "$TMP"
msg "  OK skill en $SKILL" "  OK skill in $SKILL" "  OK skill em $SKILL"

PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo
  msg "FALTA: Python 3.10 o más nuevo (el python3 que trae el Mac es el 3.9)." \
      "MISSING: Python 3.10 or newer (the python3 that ships with macOS is 3.9)." \
      "FALTA: Python 3.10 ou mais novo (o python3 que vem no Mac é o 3.9)."
  if [ "$(uname)" = "Darwin" ]; then
    open "https://www.python.org/downloads/" || true
    msg "Abrí la web de Python: pulsa 'Download Python', instálalo y ejecuta este comando otra vez." \
        "I opened the Python website: click 'Download Python', install it and run this command again." \
        "Abri o site do Python: clique em 'Download Python', instale e rode este comando de novo."
  else
    msg "Instálalo con tu gestor de paquetes (ej.: sudo apt install python3.12 python3.12-venv) y ejecuta otra vez." \
        "Install it with your package manager (e.g. sudo apt install python3.12 python3.12-venv) and run again." \
        "Instale pelo gerenciador de pacotes (ex.: sudo apt install python3.12 python3.12-venv) e rode de novo."
  fi
  exit 1
fi

"$PY" "$SKILL/scripts/clip.py" instalar
