"""Grava a live com o Streamlink em pedaços de 5 minutos (e acha cada pedaço na linha do tempo).

Live:  streamlink --stdout LINK 720p60 | ffmpeg -f segment  ->  segmentos/seg_20261119-213000.ts
       O nome do pedaço é o horário em que ele começou: assim, se a live cair e voltar, nada se mistura.
VOD:   yt-dlp baixa o vídeo inteiro e o ffmpeg separa em pedaços (segmentos/vod_00000.ts + lista.csv).

Todo tempo do clipper é "tempo da gravação": segundos desde o primeiro pedaço (00:00:00).
"""
import csv
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from comum import (SEM_JANELA, agora, config, duracao, gravar_json, ler_json, log, motivo_trancada, plataforma,
                   streamlink, ytdlp)
from textos import t


# ================================================================ linha do tempo
def _epoch_do_nome(nome):
    try:
        return time.mktime(datetime.strptime(nome[4:19], "%Y%m%d-%H%M%S").timetuple())
    except ValueError:
        return None


def segmentos(pasta, gravando=False):
    """Lista os pedaços em ordem: [{'arquivo', 'inicio', 'fim', 'completo'}] com tempos da gravação."""
    sdir = pasta / "segmentos"
    if not sdir.exists():
        return []
    sessao = ler_json(pasta / "sessao.json", {})
    cache = ler_json(sdir / "indice.json", {})
    mudou = False
    out = []
    arquivos = sorted(sdir.glob("*.ts"))
    vod = {}
    if (sdir / "lista.csv").exists():
        with open(sdir / "lista.csv", encoding="utf-8") as f:
            for linha in csv.reader(f):
                if len(linha) >= 3:
                    vod[linha[0]] = (float(linha[1]), float(linha[2]))
    # Linha do tempo: dentro de uma mesma gravação, cada pedaço começa exatamente onde o anterior terminou (soma
    # das durações reais). O relógio (horário no nome do arquivo) só é usado quando a live caiu e voltou, porque ele
    # oscila alguns segundos (o vídeo chega em rajadas). O início calculado fica guardado no indice.json, então não
    # muda depois que a limpeza apaga os pedaços mais antigos.
    fim_anterior = None
    for i, arq in enumerate(arquivos):
        ultimo = i == len(arquivos) - 1
        # o último pedaço ainda está sendo escrito se a gravação está ligada ou se mudou há menos de 30 s
        completo = not (ultimo and (gravando or time.time() - arq.stat().st_mtime < 30))
        if arq.name in vod:
            ini, fim = vod[arq.name]
        else:
            ep = _epoch_do_nome(arq.name)
            if ep is None or "inicio" not in sessao:
                continue
            guardado = cache.get(arq.name)
            if isinstance(guardado, dict) and completo:
                ini, d = guardado["ini"], guardado["d"]
            else:
                d = duracao(arq) if completo else max(0.0, arq.stat().st_mtime - ep)
                relogio = ep - sessao["inicio"]
                if fim_anterior is None:
                    ini = max(0.0, relogio)
                elif relogio - fim_anterior < 20:      # mesma gravação: emenda no anterior
                    ini = fim_anterior
                else:                                   # a live caiu e voltou: usa o relógio
                    ini = max(fim_anterior, relogio)
                if completo and d > 0:
                    cache[arq.name] = {"ini": round(ini, 3), "d": round(d, 3)}
                    mudou = True
            fim = ini + d
            fim_anterior = fim
        out.append({"arquivo": arq, "inicio": ini, "fim": fim, "completo": completo})
    if mudou:
        gravar_json(sdir / "indice.json", cache)
    return out


# ================================================================ gravador ao vivo
class Gravador(threading.Thread):
    """Mantém a gravação de pé: se a live cair, tenta de novo; se ficar muito tempo fora, considera encerrada."""

    def __init__(self, pasta, url, parar):
        super().__init__(daemon=True, name="gravador")
        self.pasta, self.url, self.parar = pasta, url, parar
        self.cfg = config()
        self.gravando = False        # tem um ffmpeg escrevendo pedaços agora
        self.encerrada = False       # a live acabou (ou desistimos de esperar)
        self.erro = None             # motivo, se não deu pra gravar
        self.procs = []

    # -------------------------------------------------- um ciclo de gravação
    def _comando_fonte(self, usar_ytdlp):
        if usar_ytdlp:
            altura = "".join(c for c in self.cfg["qualidade"].split(",")[0] if c.isdigit())[:4] or "720"
            return ytdlp() + ["-f", f"b[height<={altura}]/bv*[height<={altura}]+ba/b", "--no-part",
                              "--no-warnings", "-q", "-o", "-", self.url]
        return streamlink() + ["--stdout", "--loglevel", "warning", "--twitch-disable-ads",
                               "--hls-live-edge", "3", "--stream-segment-threads", "2",
                               "--stream-timeout", "90", self.url, self.cfg["qualidade"]]

    def _gravar_uma_vez(self, usar_ytdlp=False):
        sdir = self.pasta / "segmentos"
        sdir.mkdir(parents=True, exist_ok=True)
        err = open(self.pasta / "gravador.log", "a", encoding="utf-8", errors="ignore")
        fonte = subprocess.Popen(self._comando_fonte(usar_ytdlp), stdout=subprocess.PIPE, stderr=err,
                                 creationflags=SEM_JANELA)
        # espera chegar o primeiro pedaço de vídeo antes de abrir o ffmpeg (se a live estiver off, nem abre)
        primeiro = fonte.stdout.read(188 * 64)
        if not primeiro:
            fonte.wait()
            err.close()
            return False
        ff = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-fflags", "+genpts+discardcorrupt", "-i", "pipe:0",
             "-map", "0:v:0?", "-map", "0:a:0?", "-c", "copy", "-f", "segment",
             "-segment_time", str(self.cfg["segmento_s"]), "-reset_timestamps", "1", "-strftime", "1",
             str(sdir / "seg_%Y%m%d-%H%M%S.ts")],
            stdin=subprocess.PIPE, stderr=err, creationflags=SEM_JANELA)
        self.procs = [fonte, ff]
        sessao = ler_json(self.pasta / "sessao.json", {})
        if "inicio" not in sessao:
            sessao["inicio"] = int(agora())
            gravar_json(self.pasta / "sessao.json", sessao)
        self.gravando = True
        log(t("grabando", extra=t("con_ytdlp") if usar_ytdlp else ""))
        try:
            ff.stdin.write(primeiro)
            while not self.parar.is_set():
                bloco = fonte.stdout.read(188 * 512)
                if not bloco:
                    break
                ff.stdin.write(bloco)
        except (BrokenPipeError, OSError):
            pass
        finally:
            self.gravando = False
            for p in (fonte, ff):
                try:
                    if p is ff:
                        ff.stdin.close()
                        ff.wait(timeout=30)
                    else:
                        p.terminate()
                        p.wait(timeout=15)
                except Exception:
                    p.kill()
            self.procs = []
            err.close()
        return True

    def _ultima_linha_do_log(self):
        try:
            linhas = (self.pasta / "gravador.log").read_text(encoding="utf-8", errors="ignore").strip().splitlines()
            return linhas[-1] if linhas else ""
        except OSError:
            return ""

    def run(self):
        espera_max = self.cfg["esperar_inicio_h"] * 3600
        fim_max = self.cfg["fim_apos_min"] * 60
        comecou = agora()
        ultimo_sinal = None
        youtube = plataforma(self.url) == "youtube"
        avisou_off = False
        while not self.parar.is_set():
            gravou = self._gravar_uma_vez()
            if not gravou and youtube:            # o plugin de YouTube do Streamlink às vezes quebra: tenta o yt-dlp
                gravou = self._gravar_uma_vez(usar_ytdlp=True)
            if gravou:
                ultimo_sinal = agora()
                avisou_off = False
                if not self.parar.is_set():
                    log(t("reconectando"))
            else:
                linha = self._ultima_linha_do_log()
                motivo = motivo_trancada(linha)
                if motivo:
                    self.erro = motivo
                    log(t("no_se_puede_grabar", motivo=motivo))
                    break
                if not avisou_off:
                    log(t("offline", linea=linha[-200:]))
                    avisou_off = True
                if ultimo_sinal and agora() - ultimo_sinal > fim_max:
                    log(t("terminado_sin_senal", min=self.cfg["fim_apos_min"]))
                    break
                if not ultimo_sinal and agora() - comecou > espera_max:
                    self.erro = t("no_empezo", h=self.cfg["esperar_inicio_h"])
                    log(self.erro)
                    break
                self.parar.wait(60)
        self.encerrada = True

    def interromper(self):
        for p in list(self.procs):
            try:
                p.terminate()
            except Exception:
                pass


# ================================================================ vídeo que já acabou (VOD)
def baixar_vod(pasta, url, parar):
    """Baixa o vídeo inteiro (até 720p) e separa em pedaços. Usado quando o link não está ao vivo."""
    cfg = config()
    sdir = pasta / "segmentos"
    sdir.mkdir(parents=True, exist_ok=True)
    if (sdir / "lista.csv").exists():
        return True
    log(t("vod_descargando"))
    destino = pasta / "video_inteiro.mp4"
    if not destino.exists():
        subprocess.run(ytdlp() + ["-f", "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4",
                                  "--no-playlist", "--no-warnings", "-q", "-o", str(destino), url],
                       check=True, creationflags=SEM_JANELA)
    if parar.is_set():
        return False
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(destino), "-map", "0:v:0?",
                    "-map", "0:a:0?", "-c", "copy", "-f", "segment", "-segment_time", str(cfg["segmento_s"]),
                    "-reset_timestamps", "1", "-segment_list", str(sdir / "lista.csv"), "-segment_list_type", "csv",
                    str(sdir / "vod_%05d.ts")], check=True, creationflags=SEM_JANELA)
    destino.unlink(missing_ok=True)
    sessao = ler_json(pasta / "sessao.json", {})
    sessao.setdefault("inicio", int(agora()))
    sessao["vod"] = True
    gravar_json(pasta / "sessao.json", sessao)
    return True


def cortar_da_gravacao(pasta, inicio, fim, destino):
    """Junta os pedaços que cobrem [inicio, fim] e recorta o trecho exato (em tempo da gravação)."""
    segs = [s for s in segmentos(pasta) if s["fim"] > inicio and s["inicio"] < fim and s["arquivo"].exists()]
    if not segs:
        return False
    primeiro = segs[0]
    if primeiro["inicio"] > inicio + 2:
        inicio = primeiro["inicio"]   # o começo já foi apagado ou caiu a live: começa onde tem gravação
    lista = Path(destino).with_suffix(".lista.txt")
    lista.write_text("".join(f"file '{s['arquivo'].as_posix()}'\n" for s in segs), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lista), "-ss", f"{inicio - primeiro['inicio']:.2f}", "-t", f"{fim - inicio:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "aac", "-b:a", "192k",
                    str(destino)], check=True, creationflags=SEM_JANELA)
    lista.unlink(missing_ok=True)
    return Path(destino).exists() and duracao(destino) > 1
