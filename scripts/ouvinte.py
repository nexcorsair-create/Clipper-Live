"""Escuta cada pedaço novo da gravação: escreve a fala (Whisper, no computador) e mede o volume segundo a segundo.

Resultado de cada pedaço em escuta/<pedaço>.json:
  {"inicio": 1800.0, "fala": [[ini, fim, "texto"], …], "db": [-31.2, -29.8, …]}   (tempos da gravação)
"""
import subprocess
import threading
import wave

import numpy as np

from comum import SEM_JANELA, config, gravar_json, ler_json, log
from textos import t
from gravador import segmentos


def carregar_whisper(modelo):
    """Usa a placa de vídeo NVIDIA se der; senão, o processador."""
    from faster_whisper import WhisperModel
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            m = WhisperModel(modelo, device="cuda", compute_type="float16")
            list(m.transcribe(np.zeros(16000, dtype=np.float32))[0])   # testa de verdade (falta cuBLAS = cai aqui)
            return m, t("gpu")
    except Exception:
        pass
    return WhisperModel(modelo, device="cpu", compute_type="int8"), t("cpu")


def audio_16k(video, wav):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1",
                    "-ar", "16000", str(wav)], check=True, creationflags=SEM_JANELA)


def ler_wav(wav):
    """Áudio já decodificado pro Whisper (assim não depende do PyAV, que muda de versão e quebra)."""
    with wave.open(str(wav)) as f:
        return np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0


def volume_por_segundo(wav):
    with wave.open(str(wav)) as f:
        sr, n = f.getframerate(), f.getnframes()
        a = np.frombuffer(f.readframes(n), dtype=np.int16).astype(np.float32)
    seg = len(a) // sr
    if seg == 0:
        return []
    rms = np.sqrt(np.mean(a[: seg * sr].reshape(seg, sr) ** 2, axis=1) + 1e-6)
    return [round(float(v), 1) for v in 20 * np.log10(rms / 32768 + 1e-9)]


class Ouvinte(threading.Thread):
    def __init__(self, pasta, parar, gravador=None):
        super().__init__(daemon=True, name="ouvinte")
        self.pasta, self.parar, self.gravador = pasta, parar, gravador
        self.cfg = config()
        self.modelo = None
        self.horizonte = 0.0        # até onde (tempo da gravação) a live já foi escutada
        self.atraso = 0             # pedaços esperando pra ser escutados

    def escutar(self, seg):
        edir = self.pasta / "escuta"
        edir.mkdir(exist_ok=True)
        saida = edir / (seg["arquivo"].stem + ".json")
        if saida.exists():
            return ler_json(saida)
        wav = edir / (seg["arquivo"].stem + ".wav")
        try:
            audio_16k(seg["arquivo"], wav)
            db = volume_por_segundo(wav)
            if self.modelo is None:
                self.modelo, onde = carregar_whisper(self.cfg["modelo_live"])
                log(t("modelo_en", modelo=self.cfg["modelo_live"], donde=onde))
            idioma = self.cfg["idioma"] or ler_json(self.pasta / "sessao.json", {}).get("idioma")
            partes, info = self.modelo.transcribe(ler_wav(wav), language=idioma, vad_filter=True, beam_size=1,
                                                  condition_on_previous_text=False)
            fala = [[round(seg["inicio"] + p.start, 2), round(seg["inicio"] + p.end, 2), p.text.strip()]
                    for p in partes if p.text.strip()]
            if not idioma and fala:   # fixa o idioma descoberto no primeiro pedaço com fala
                sessao = ler_json(self.pasta / "sessao.json", {})
                sessao["idioma"] = info.language
                gravar_json(self.pasta / "sessao.json", sessao)
            dados = {"inicio": seg["inicio"], "fim": seg["fim"], "fala": fala, "db": db}
            gravar_json(saida, dados)
            return dados
        finally:
            wav.unlink(missing_ok=True)

    def run(self):
        falhas = {}
        while True:
            try:   # a escuta nunca pode morrer: um erro solto só pula pra próxima volta
                gravando = bool(self.gravador and self.gravador.gravando)
                pendentes = [s for s in segmentos(self.pasta, gravando) if s["completo"]
                             and not (self.pasta / "escuta" / (s["arquivo"].stem + ".json")).exists()]
                self.atraso = len(pendentes)
                for s in pendentes:
                    if self.parar.is_set():
                        return
                    try:
                        d = self.escutar(s)
                        log(t("trozo_listo", arq=s["arquivo"].name, n=len(d["fala"])))
                    except Exception as e:
                        log(t("trozo_error", arq=s["arquivo"].name, error=f"{type(e).__name__}: {str(e)[:200]}"))
                        falhas[s["arquivo"].name] = falhas.get(s["arquivo"].name, 0) + 1
                        if falhas[s["arquivo"].name] >= 3 or not s["arquivo"].exists():   # desiste do pedaço
                            gravar_json(self.pasta / "escuta" / (s["arquivo"].stem + ".json"),
                                        {"inicio": s["inicio"], "fim": s["fim"], "fala": [], "db": [],
                                         "erro": str(e)[:300]})
                    self.atraso -= 1
                self.horizonte = horizonte_escutado(self.pasta)
            except Exception as e:
                log(t("trozo_error", arq="-", error=f"{type(e).__name__}: {str(e)[:200]}"))
            if self.parar.wait(15):
                return


def horizonte_escutado(pasta):
    """Até onde a live já foi escutada sem buracos (fim do último pedaço escutado em sequência)."""
    h = 0.0
    for s in segmentos(pasta):
        if not s["completo"]:
            break
        d = ler_json(pasta / "escuta" / (s["arquivo"].stem + ".json"))
        if d is None:
            break
        h = d.get("fim", s["fim"])
    return h


def escuta_entre(pasta, ini, fim):
    """Junta fala e volume de todos os pedaços escutados entre ini e fim (tempo da gravação)."""
    fala, db = [], {}
    for arq in sorted((pasta / "escuta").glob("*.json")):
        d = ler_json(arq)
        if not d or d.get("fim", 0) < ini - 400 or d.get("inicio", 0) > fim:
            continue
        fala += [f for f in d["fala"] if ini <= f[0] < fim]
        base = int(d["inicio"])
        for i, v in enumerate(d["db"]):
            db[base + i] = v
    return fala, db
