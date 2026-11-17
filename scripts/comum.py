"""Coisas que todas as partes do Clipper Live usam: pastas, configuração, tempo e chamadas de programas."""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------- onde fica cada coisa
APP = Path(os.environ.get("CLIPPER_LIVE_APP", Path.home() / ".clipper-live"))   # programa (ambiente, modelos)
CONFIG = APP / "config.json"
VENV = APP / "ambiente"
VENV_BIN = VENV / ("Scripts" if os.name == "nt" else "bin")
VENV_PY = VENV_BIN / ("python.exe" if os.name == "nt" else "python")
MODELOS = APP / "modelos"
YUNET = MODELOS / "face_detection_yunet_2023mar.onnx"
YUNET_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
             "face_detection_yunet_2023mar.onnx")

PADRAO = {
    "lengua": "es",              # idioma do sistema: es (padrão), en, pt
    "pasta": str(Path.home() / "clipper-live"),  # onde ficam gravações e cortes
    "gb": 50,                    # espaço reservado (gravação + cortes)
    "qualidade": "720p60,720p,best",
    "segmento_s": 300,           # a gravação é salva em pedaços de 5 min
    "bloco_min": 30,             # a IA analisa a live a cada 30 min
    "nota_minima": 70,           # momento abaixo disso não vira corte
    "max_por_bloco": 3,          # no máximo 3 cortes por bloco de 30 min
    "guardar_min": 60,           # gravação já analisada fica mais 60 min antes de ser apagada
    "modelo_live": "small",      # Whisper que escuta a live inteira (base = mais rápido, pior em espanhol)
    "modelo_legenda": "small",   # Whisper da legenda palavra por palavra
    "idioma": None,              # None = descobre sozinho
    "fim_apos_min": 20,          # live sem sinal por 20 min = acabou
    "esperar_inicio_h": 8,       # espera até 8 h a live começar
    "atualizar_a_cada_h": 12,
}


def config():
    c = dict(PADRAO)
    c.update(ler_json(CONFIG, {}) or {})
    return c


def salvar_config(**mudancas):
    c = ler_json(CONFIG, {}) or {}
    c.update({k: v for k, v in mudancas.items() if v is not None})
    gravar_json(CONFIG, c)
    return config()


def pasta_dados():
    return Path(config()["pasta"]).expanduser()


def pasta_lives():
    return pasta_dados() / "lives"


def pasta_cortes():
    return pasta_dados() / "cortes"


# ---------------------------------------------------------------- texto e tempo
def slug(texto, limite=50):
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return t[:limite].strip("-") or "live"


def hms(seg):
    seg = max(0, int(round(seg)))
    return f"{seg // 3600:02d}:{seg % 3600 // 60:02d}:{seg % 60:02d}"


def segundos(valor):
    """Aceita 3723, '3723', '1:02:03' ou '62:03'."""
    if isinstance(valor, (int, float)):
        return float(valor)
    total = 0.0
    for p in str(valor).strip().split(":"):
        total = total * 60 + float(p)
    return total


def agora():
    return time.time()


def log(msg):
    print(time.strftime("[%H:%M:%S] ") + str(msg), flush=True)


# ---------------------------------------------------------------- arquivos
def ler_json(caminho, padrao=None):
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return padrao


def gravar_json(caminho, dados):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    # temporário próprio de cada processo/thread: duas partes do vigia podem gravar o mesmo arquivo ao mesmo tempo
    import threading
    tmp = caminho.with_name(f"{caminho.name}.{os.getpid()}-{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    for tentativa in range(20):   # troca de uma vez: quem lê nunca pega o arquivo pela metade
        try:
            os.replace(tmp, caminho)
            return
        except PermissionError:   # no Windows, falha se alguém estiver lendo naquele instante
            time.sleep(0.1 * (tentativa + 1))
    tmp.unlink(missing_ok=True)
    raise PermissionError(f"não consegui gravar {caminho}")


def tamanho(pasta):
    total = 0
    for raiz, _, arquivos in os.walk(pasta):
        for a in arquivos:
            try:
                total += os.path.getsize(os.path.join(raiz, a))
            except OSError:
                pass
    return total


def gb(bytes_):
    return bytes_ / 1024 ** 3


# ---------------------------------------------------------------- programas
SEM_JANELA = 0x08000000 if os.name == "nt" else 0   # no Windows, não abre janela preta pra cada programa


def tem(programa):
    return shutil.which(programa) is not None


def programa_do_ambiente(nome):
    p = VENV_BIN / (nome + (".exe" if os.name == "nt" else ""))
    return str(p) if p.exists() else (shutil.which(nome) or nome)


def preparar_ffmpeg():
    """Usa o ffmpeg do computador; se não tiver, o que vem no pacote static-ffmpeg."""
    if tem("ffmpeg") and tem("ffprobe"):
        return True
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths(weak=True)
    except Exception:
        return False
    return tem("ffmpeg") and tem("ffprobe")


def ytdlp():
    cmd = [programa_do_ambiente("yt-dlp")]
    deno = VENV_BIN / ("deno.exe" if os.name == "nt" else "deno")   # o YouTube pede um JavaScript pra liberar formatos
    if deno.exists():
        cmd += ["--js-runtimes", f"deno:{deno}"]
    elif tem("deno"):
        cmd += ["--js-runtimes", "deno"]
    elif tem("node"):
        cmd += ["--js-runtimes", "node"]
    return cmd


def streamlink():
    return [programa_do_ambiente("streamlink")]


def rodar(cmd, **kw):
    kw.setdefault("creationflags", SEM_JANELA)
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def duracao(arquivo):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        str(arquivo)], capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=SEM_JANELA)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


# ---------------------------------------------------------------- plataformas
def plataforma(url):
    u = url.lower()
    if "twitch.tv" in u:
        return "twitch"
    if "kick.com" in u:
        return "kick"
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    return "outra"


def canal_do_link(url):
    m = re.search(r"(?:twitch\.tv|kick\.com)/([A-Za-z0-9_\-]+)", url)
    if m and m.group(1).lower() not in ("videos", "video", "clip"):
        return m.group(1).lower()
    m = re.search(r"youtube\.com/@([A-Za-z0-9_.\-]+)", url)
    return m.group(1) if m else None


TRANCADA = ("confirm your age", "inappropriate for some users", "members-only", "join this channel",
            "subscriber", "private video", "requires authentication", "sign in to confirm")


def motivo_trancada(erro):
    from textos import t as tr
    t = (erro or "").lower()
    if not any(k in t for k in TRANCADA):
        return None
    if "age" in t or "inappropriate" in t:
        return tr("bloqueo_edad")
    if "member" in t or "join this channel" in t or "subscriber" in t:
        return tr("bloqueo_miembros")
    return tr("bloqueo_login")


# ---------------------------------------------------------------- lives
def pasta_da_live(nome=None):
    """Aceita o nome da pasta, um pedaço dele ou o link. Sem nome: a live mais recente."""
    raiz = pasta_lives()
    lives = sorted([p for p in raiz.glob("*") if p.is_dir()], key=lambda p: p.stat().st_mtime) if raiz.exists() else []
    from textos import t
    if not lives:
        sys.exit(t("sin_directos"))
    if not nome:
        return lives[-1]
    if (raiz / nome).is_dir():
        return raiz / nome
    for p in reversed(lives):
        info = ler_json(p / "info.json", {})
        if nome in (info.get("url"), info.get("webpage_url")) or nome.lower() in p.name:
            return p
    sys.exit(t("directo_no_encontrado", nombre=nome, carpeta=raiz))


def todas_as_lives():
    raiz = pasta_lives()
    return sorted([p for p in raiz.glob("*") if p.is_dir()], key=lambda p: p.stat().st_mtime) if raiz.exists() else []


def vigia_rodando(pasta):
    """O vigia escreve um 'batimento' a cada poucos segundos; mais de 2 min sem batimento = parado."""
    b = ler_json(pasta / "batimento.json", {})
    return bool(b) and agora() - b.get("t", 0) < 120 and not b.get("encerrado")
