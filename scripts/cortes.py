"""Transforma os momentos que a IA escolheu em cortes verticais e cuida da fila de aprovação.

Cada corte: câmera do streamer em cima, jogo embaixo, título de gancho, legenda palavra por palavra
e um .txt com a legenda do post, as hashtags e o crédito da live.

Fila:  cortes/pendientes/007_canal.mp4  ->  aprobar  ->  cortes/aprobados/<live>/007_canal.mp4
                                        ->  recusar ->  apagado
"""
import shutil
import subprocess
from pathlib import Path

from comum import (SEM_JANELA, YUNET, config, duracao, gravar_json, hms, ler_json, pasta_cortes,
                   segundos, todas_as_lives)
from gravador import cortar_da_gravacao
from textos import t

L, A = 1080, 1920      # vídeo vertical
CAM_H = 768            # faixa da câmera em cima
JOGO_H = A - CAM_H     # faixa do jogo embaixo


# ================================================================ registro dos cortes
def registro():
    return ler_json(pasta_cortes() / "cortes.json", {"proximo": 1, "cortes": []})


def salvar_registro(r):
    gravar_json(pasta_cortes() / "cortes.json", r)


# ================================================================ escolher momentos de um bloco
def momentos_do_bloco(arq, cfg):
    dados = ler_json(arq)
    if dados is None:
        return None
    lista = dados if isinstance(dados, list) else dados.get("momentos", [])
    bons = []
    for m in lista:
        try:
            s, e = segundos(m["inicio"]), segundos(m["fim"])
            nota = float(m.get("nota", 0))
        except (KeyError, ValueError, TypeError):
            continue
        if nota < cfg["nota_minima"] or e <= s:
            continue
        e = min(max(e, s + 15), s + 90)          # corte de 15 a 90 s
        bons.append(dict(m, _s=s, _e=e, nota=nota))
    bons.sort(key=lambda m: -m["nota"])
    return bons


def sobrepoe(m, outros):
    return any(m["_s"] < o["fim_s"] and o["inicio_s"] < m["_e"] for o in outros)


# ================================================================ câmera do streamer
def achar_camera(video):
    """Procura rostos em 16 quadros do trecho; devolve (largura, altura, caixa do rosto mais constante)."""
    import cv2
    import numpy as np
    try:
        cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)   # sem avisos técnicos na tela
    except AttributeError:
        pass
    cap = cv2.VideoCapture(str(video))
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    if not W or not YUNET.exists():
        cap.release()
        return W or 1920, H or 1080, None
    esc = 960 / W
    det = cv2.FaceDetectorYN.create(str(YUNET), "", (960, int(H * esc)), 0.75)
    caixas = []
    for k in range(16):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * (k + 0.5) / 16))
        ok, quadro = cap.read()
        if not ok:
            continue
        _, rostos = det.detect(cv2.resize(quadro, (960, int(H * esc))))
        for r in rostos if rostos is not None else []:
            if r[14] >= 0.75 and r[3] / esc > H * 0.05:   # rosto confiável e não minúsculo
                caixas.append([v / esc for v in r[:4]])
    cap.release()
    if len(caixas) < 4:
        return W, H, None
    c = np.array(caixas)
    centros = c[:, :2] + c[:, 2:] / 2
    meio = np.median(centros, axis=0)
    perto = c[np.linalg.norm(centros - meio, axis=1) < W * 0.08]
    if len(perto) < 4:
        return W, H, None
    return W, H, np.median(perto, axis=0)


def _par(v):
    return int(v) // 2 * 2


def filtro_video(W, H, rosto):
    if rosto is None:   # sem câmera: jogo inteiro no meio, fundo desfocado
        return ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:3[bg];"
                "[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p,ass=legenda.ass[v]")
    fx, fy, fw, fh = rosto
    cw = min(W, max(fw * 3.2, 200))
    ch = cw * CAM_H / L
    if ch > H:
        ch, cw = H, H * L / CAM_H
    cx = min(max(fx + fw / 2 - cw / 2, 0), W - cw)
    cy = min(max(fy + fh * 0.65 - ch / 2, 0), H - ch)
    gw = min(W, H * L / JOGO_H)
    gx = (W - gw) / 2
    return (f"[0:v]crop={_par(cw)}:{_par(ch)}:{_par(cx)}:{_par(cy)},scale={L}:{CAM_H},setsar=1[cam];"
            f"[0:v]crop={_par(gw)}:{_par(H)}:{_par(gx)}:0,scale={L}:{JOGO_H},setsar=1[jogo];"
            f"[cam][jogo]vstack=inputs=2,format=yuv420p,ass=legenda.ass[v]")


# ================================================================ legenda
def _t(t):
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _limpo(txt):
    return txt.replace("{", "(").replace("}", ")").replace("\\", "/").strip()


def escrever_ass(caminho, titulo, palavras, dur, com_camera):
    y_titulo = CAM_H if com_camera else 520
    y_leg = CAM_H + int(JOGO_H * 0.62) if com_camera else 1480
    linhas = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {L}", f"PlayResY: {A}", "WrapStyle: 0", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding",
        "Style: Gancho,Arial,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,3,18,0,5,60,60,0,1",
        "Style: Leg,Arial,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,3,5,40,40,0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 1,{_t(0)},{_t(dur)},Gancho,,0,0,0,,{{\\pos(540,{y_titulo})}}{_limpo(titulo).upper()}",
    ]
    grupos = [palavras[i:i + 3] for i in range(0, len(palavras), 3)]   # 3 palavras por vez, a falada em amarelo
    for g, grupo in enumerate(grupos):
        prox = grupos[g + 1][0][0] if g + 1 < len(grupos) else dur
        for k, (s, e, _) in enumerate(grupo):
            fim = grupo[k + 1][0] if k + 1 < len(grupo) else (prox if prox - e < 0.6 else e + 0.25)
            txt = " ".join(("{\\c&H00E5FF&}" if j == k else "{\\c&HFFFFFF&}") + _limpo(w).upper()
                           for j, (_, _, w) in enumerate(grupo))
            linhas.append(f"Dialogue: 0,{_t(s)},{_t(fim)},Leg,,0,0,0,,{{\\pos(540,{y_leg})}}{txt}")
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


# ================================================================ montar um corte
class Montador:
    def __init__(self):
        self.cfg = config()
        self.whisper = None

    def palavras(self, video, idioma):
        if self.whisper is None:
            from ouvinte import carregar_whisper
            self.whisper, onde = carregar_whisper(self.cfg["modelo_legenda"])
            print(t("subtitulo_modelo", modelo=self.cfg["modelo_legenda"], donde=onde))
        from ouvinte import audio_16k, ler_wav
        wav = Path(video).with_suffix(".wav")
        audio_16k(video, wav)
        audio = ler_wav(wav)
        wav.unlink(missing_ok=True)
        partes, _ = self.whisper.transcribe(audio, language=idioma, word_timestamps=True, vad_filter=True,
                                            condition_on_previous_text=False)
        return [(w.start, w.end, w.word.strip()) for p in partes for w in (p.words or []) if w.word.strip()]

    def montar(self, pasta, m, numero):
        info = ler_json(pasta / "info.json", {})
        idioma = ler_json(pasta / "sessao.json", {}).get("idioma")
        tdir = pasta / "montagem" / f"{numero:03d}"
        tdir.mkdir(parents=True, exist_ok=True)
        trecho = tdir / "trecho.mp4"
        if not trecho.exists() or duracao(trecho) < 1:
            if not cortar_da_gravacao(pasta, m["_s"], m["_e"], trecho):
                return None
        dur = duracao(trecho)
        W, H, rosto = achar_camera(trecho)
        print(t("camara_si") if rosto is not None else t("camara_no"))
        escrever_ass(tdir / "legenda.ass", m.get("titulo", ""), self.palavras(trecho, idioma), dur,
                     rosto is not None)
        destino = pasta_cortes() / "pendientes"
        destino.mkdir(parents=True, exist_ok=True)
        saida = destino / f"{numero:03d}_{pasta.name[:40]}.mp4"
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", "trecho.mp4", "-filter_complex",
                        filtro_video(W, H, rosto), "-map", "[v]", "-map", "0:a?", "-c:v", "libx264",
                        "-preset", "medium", "-crf", "19", "-r", "30", "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart", str(saida.resolve())],
                       check=True, cwd=tdir, creationflags=SEM_JANELA)
        canal = info.get("canal") or t("el_streamer")
        saida.with_suffix(".txt").write_text(
            f"{m.get('titulo', '')}\n\n{m.get('post', '').strip()}\n\n"
            + t("credito", canal=canal, url=info.get("url", "")) + "\n", encoding="utf-8")
        shutil.rmtree(tdir, ignore_errors=True)
        return saida


def cortar(pasta):
    """Monta os cortes de todos os blocos que a IA já leu e ainda não viraram corte."""
    cfg = config()
    estado = ler_json(pasta / "estado.json", {"blocos": []})
    feitos = set(estado.get("cortados", []))
    reg = registro()
    da_live = [c for c in reg["cortes"] if c["live"] == pasta.name]
    montador = Montador()
    novos = []
    for b in estado["blocos"]:
        arq = pasta / "momentos" / f"bloque_{b['n']:02d}.json"
        if b["n"] in feitos or not arq.exists():
            continue
        momentos = momentos_do_bloco(arq, cfg)
        if momentos is None:
            print(t("json_invalido", arq=arq.name))
            continue
        escolhidos = []
        for m in momentos:
            if len(escolhidos) >= cfg["max_por_bloco"]:
                break
            if sobrepoe(m, da_live):
                print(t("clip_solapa", titulo=m.get("titulo", ""), ini=hms(m["_s"])))
                continue
            numero = reg["proximo"]
            print(t("clip_cab", n=numero, titulo=m.get("titulo", ""), ini=hms(m["_s"]), fin=hms(m["_e"]),
                    nota=f"{m['nota']:.0f}"))
            try:
                saida = montador.montar(pasta, m, numero)
            except subprocess.CalledProcessError as e:
                print(t("clip_fallo", error=e))
                saida = None
            if not saida:
                print(t("clip_sin_grabacion"))
                continue
            c = {"numero": numero, "live": pasta.name, "bloco": b["n"], "inicio_s": m["_s"], "fim_s": m["_e"],
                 "inicio": hms(m["_s"]), "fim": hms(m["_e"]), "nota": m["nota"], "titulo": m.get("titulo", ""),
                 "tipo": m.get("tipo", ""), "porque": m.get("porque", ""), "arquivo": str(saida),
                 "status": "pending"}
            reg["cortes"].append(c)
            reg["proximo"] = numero + 1
            salvar_registro(reg)
            da_live.append(c)
            escolhidos.append(c)
            novos.append(c)
            print(t("clip_listo", arq=saida))
        feitos.add(b["n"])
        estado = ler_json(pasta / "estado.json", {"blocos": []})   # o vigia pode ter aberto bloco novo
        estado["cortados"] = sorted(feitos)
        gravar_json(pasta / "estado.json", estado)
    if not novos:
        print(t("ningun_clip_nuevo"))
    else:
        print(t("clips_nuevos", n=len(novos), carpeta=pasta_cortes() / "pendientes"))
    return novos


# ================================================================ aprovação
def listar_pendentes():
    return [c for c in registro()["cortes"] if c["status"] == "pending"]


def mostrar_pendentes():
    p = listar_pendentes()
    if not p:
        print(t("sin_pendientes"))
        return
    print(t("pendientes_cab", n=len(p)))
    for c in p:
        print(t("pendiente_linea", n=c["numero"], nota=f"{c['nota']:.0f}", ini=c["inicio"], fin=c["fim"],
                titulo=c["titulo"], porque=c.get("porque", ""), arq=c["arquivo"]))


def decidir(numeros, aprovar):
    reg = registro()
    for n in numeros:
        c = next((c for c in reg["cortes"] if c["numero"] == int(n)), None)
        if not c:
            print(t("no_existe", n=n))
            continue
        if c["status"] != "pending":
            print(t("ya_estaba", n=n, estado=t("estado_" + c["status"])))
            continue
        video = Path(c["arquivo"])
        if aprovar:
            destino = pasta_cortes() / "aprobados" / c["live"]
            destino.mkdir(parents=True, exist_ok=True)
            for arq in (video, video.with_suffix(".txt")):
                if arq.exists():
                    shutil.move(str(arq), str(destino / arq.name))
            c.update(status="approved", arquivo=str(destino / video.name))
            print(t("aprobado", n=n, arq=destino / video.name))
        else:
            for arq in (video, video.with_suffix(".txt")):
                arq.unlink(missing_ok=True)
            c.update(status="rejected")
            print(t("rechazado", n=n))
    salvar_registro(reg)


def lives_com_cortes():
    return {c["live"] for c in registro()["cortes"]} & {p.name for p in todas_as_lives()}
