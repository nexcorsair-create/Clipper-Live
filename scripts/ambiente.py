"""Instala, confere e atualiza tudo que o Clipper Live usa.

Atualizar é seguro: antes anota as versões que funcionam, atualiza, testa; se o teste falhar, volta pras antigas.
"""
import json
import os
import shutil
import subprocess
import sys
import time

from comum import (APP, CONFIG, MODELOS, SEM_JANELA, VENV, VENV_PY, YUNET, YUNET_URL, agora, config, gb,
                   gravar_json, ler_json, pasta_cortes, pasta_dados, pasta_lives, salvar_config, tem, todas_as_lives,
                   vigia_rodando)
from textos import LENGUAS, fijar, t

# programas que o clipper puxa e mantém sempre atualizados
PACOTES = ["streamlink", "yt-dlp[default]", "faster-whisper", "opencv-python-headless", "numpy",
           "websocket-client", "certifi", "static-ffmpeg", "deno"]
VERSOES = APP / "versoes.json"


def _pip(*args, quieto=True):
    cmd = [str(VENV_PY), "-m", "pip", *args] + (["-q"] if quieto else [])
    return subprocess.run(cmd, creationflags=SEM_JANELA)


def versoes_instaladas():
    r = subprocess.run([str(VENV_PY), "-m", "pip", "list", "--format=json"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=SEM_JANELA)
    try:
        return {p["name"].lower(): p["version"] for p in json.loads(r.stdout)}
    except ValueError:
        return {}


def testar():
    """Confere se cada peça funciona de verdade. Devolve a lista do que está quebrado."""
    quebrado = []
    teste_py = ("import faster_whisper, cv2, numpy, websocket, streamlink, yt_dlp; "
                "from streamlink import Streamlink; Streamlink().resolve_url('https://www.twitch.tv/a')")
    if subprocess.run([str(VENV_PY), "-c", teste_py], capture_output=True, creationflags=SEM_JANELA).returncode:
        quebrado.append(t("pkg_python"))
    for nome in ("streamlink", "yt-dlp"):
        exe = VENV / ("Scripts" if os.name == "nt" else "bin") / (nome + (".exe" if os.name == "nt" else ""))
        if subprocess.run([str(exe), "--version"], capture_output=True, creationflags=SEM_JANELA).returncode:
            quebrado.append(nome)
    r = subprocess.run([str(VENV_PY), "-c", "import sys; sys.path.insert(0, sys.argv[1]); import comum; "
                        "sys.exit(0 if comum.preparar_ffmpeg() else 1)", os.path.dirname(__file__)],
                       capture_output=True, creationflags=SEM_JANELA)
    if r.returncode:
        quebrado.append("ffmpeg")
    return quebrado


def atualizar(forcar=True):
    """Atualiza Streamlink, yt-dlp, Whisper, ffmpeg… e volta atrás se alguma coisa quebrar."""
    if not VENV_PY.exists():
        print(t("no_instalado"))
        return False
    if not forcar and agora() - (ler_json(VERSOES, {}).get("quando") or 0) < config()["atualizar_a_cada_h"] * 3600:
        return True
    if any(vigia_rodando(p) for p in todas_as_lives()):
        print(t("act_luego"))
        return True
    print(t("buscando_act"))
    antes = versoes_instaladas()
    _pip("install", "--upgrade", "pip")
    r = _pip("install", "--upgrade", *PACOTES)
    depois = versoes_instaladas()
    mudou = {k: (antes.get(k), v) for k, v in depois.items() if antes.get(k) != v}
    quebrado = testar() if r.returncode == 0 else [t("pkg_instalacion")]
    if quebrado and antes:
        print(t("act_rompio", lista=", ".join(quebrado)))
        volta = [f"{k}=={v_antes}" for k, (v_antes, _) in mudou.items() if v_antes]
        if volta:
            _pip("install", *volta)
        quebrado = testar()
        print(t("act_volvi") if not quebrado else t("act_sigue_roto", lista=quebrado))
    elif mudou:
        nomes = ("streamlink", "yt-dlp", "faster-whisper", "static-ffmpeg", "deno", "opencv-python-headless")
        lista = ", ".join(f"{k} {a or '-'} → {d}" for k, (a, d) in mudou.items() if k in nomes)
        print(t("act_hecho", lista=lista or t("act_internas")))
    else:
        print(t("act_al_dia"))
    gravar_json(VERSOES, {"quando": agora(), "versoes": versoes_instaladas(), "quebrado": quebrado})
    return not quebrado


def instalar():
    l = os.environ.get("CLIPPER_LANG", "").lower()[:2]   # o instalador pode já vir com o idioma escolhido
    if l in LENGUAS:
        salvar_config(lengua=l)
        fijar(l)
    print(t("revisando"))
    if sys.version_info < (3, 10):
        print(t("py_viejo", v=sys.version.split()[0]))
        print(t("py_winget") if os.name == "nt" else t("py_web"))
        sys.exit(1)
    print(t("py_ok", v=sys.version.split()[0]))
    APP.mkdir(parents=True, exist_ok=True)
    if not VENV_PY.exists():
        print(t("creando_entorno", p=VENV))
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    print(t("instalando", lista=", ".join(p.split("[")[0] for p in PACOTES)))
    _pip("install", "--upgrade", "pip")
    if _pip("install", "--upgrade", *PACOTES).returncode:
        sys.exit(t("pip_fallo"))
    print(t("paquetes_ok"))
    if not (tem("ffmpeg") and tem("ffprobe")):
        print(t("bajando_ffmpeg"))
    if not YUNET.exists():
        print(t("bajando_yunet"))
        MODELOS.mkdir(parents=True, exist_ok=True)
        if tem("curl"):
            subprocess.run(["curl", "-fsSL", "-o", str(YUNET), YUNET_URL], check=True, creationflags=SEM_JANELA)
        else:
            subprocess.run([str(VENV_PY), "-c", "import sys,ssl,certifi,urllib.request as u;"
                            "c=ssl.create_default_context(cafile=certifi.where());"
                            "open(sys.argv[2],'wb').write(u.urlopen(sys.argv[1],context=c).read())",
                            YUNET_URL, str(YUNET)], check=True)
    print(t("yunet_ok"))
    cfg = config()
    print(t("bajando_modelos", a=cfg["modelo_live"], b=cfg["modelo_legenda"]))
    subprocess.run([str(VENV_PY), "-c", "import sys; from faster_whisper import WhisperModel as W; "
                    "[W(m) for m in sys.argv[1:]]", cfg["modelo_live"], cfg["modelo_legenda"]], check=True)
    print(t("modelos_ok"))
    quebrado = testar()
    gravar_json(VERSOES, {"quando": agora(), "versoes": versoes_instaladas(), "quebrado": quebrado})
    if quebrado:
        sys.exit(t("roto", lista=", ".join(quebrado)))
    print(t("prueba_ok"))
    if "pasta" not in (ler_json(CONFIG, {}) or {}):
        print(t("falta_config"))
    else:
        print(t("todo_listo", carpeta=cfg["pasta"], gb=cfg["gb"]))


def configurar(pasta=None, gb_reservado=None, **outros):
    cfg = salvar_config(pasta=str(pasta) if pasta else None, gb=gb_reservado, **outros)
    fijar(cfg["lengua"])
    if not pasta and "pasta" not in (ler_json(CONFIG, {}) or {}):
        salvar_config(pasta=cfg["pasta"])   # grava a pasta padrão pra marcar como configurado
    destino = pasta_dados()
    destino.mkdir(parents=True, exist_ok=True)
    for p in (pasta_lives(), pasta_cortes()):
        p.mkdir(parents=True, exist_ok=True)
    livre = gb(shutil.disk_usage(destino).free)
    usado = gb(sum(f.stat().st_size for f in destino.rglob("*") if f.is_file()))
    print(t("cfg_lengua"))
    print(t("cfg_carpeta", p=destino))
    print(t("cfg_reserva", gb=cfg["gb"], libre=livre, usado=usado))
    if livre + usado < cfg["gb"]:
        print(t("cfg_poco", libre=livre))
    print(t("cfg_horas", h=cfg["gb"] / 2.0))
    print(t("cfg_guardada"))


def verificar():
    """Resumo rápido: está instalado? atualizado? quanto espaço?"""
    cfg = config()
    v = ler_json(VERSOES, {})
    print(t("ver_instalado", v=t("si") if VENV_PY.exists() else t("no_instalar")))
    if v:
        vs = v.get("versoes", {})
        print(t("ver_versiones", v=", ".join(f"{k} {vs.get(k, '?')}" for k in ("streamlink", "yt-dlp",
                                                                                 "faster-whisper"))))
        print(t("ver_ultima", v=time.strftime("%d/%m %H:%M", time.localtime(v.get("quando", 0)))))
        if v.get("quebrado"):
            print(t("ver_roto", v=v["quebrado"]))
    configurado = "pasta" in (ler_json(CONFIG, {}) or {})
    print(t("ver_config", v=t("si") if configurado else t("no_configurar"), p=cfg["pasta"], gb=cfg["gb"],
            l=cfg["lengua"]))
