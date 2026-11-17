"""O vigia: roda em segundo plano enquanto a live acontece.

  gravador  ->  grava em pedaços de 5 min (Streamlink)
  chat      ->  guarda cada mensagem do chat
  ouvinte   ->  escreve a fala e mede o volume de cada pedaço
  a cada 30 min de live escutada -> bloco_NN.txt pra IA ler
  a cada minuto -> limpeza (respeita os GB reservados)

Pra parar: clip.py parar  (cria o arquivo 'parar' na pasta da live)
"""
import json
import subprocess
import threading
import time
from datetime import datetime

from blocos import talvez_novo_bloco
from chat import Chat
from comum import (SEM_JANELA, agora, canal_do_link, config, gb, gravar_json, ler_json, log, motivo_trancada,
                   pasta_dados, pasta_lives, plataforma, slug, streamlink, tamanho, todas_as_lives, vigia_rodando,
                   ytdlp)
from gravador import Gravador, baixar_vod, segmentos
from ouvinte import Ouvinte, horizonte_escutado
from textos import t


# ================================================================ descobrir o que é o link
def ler_link(url):
    """Devolve info da live: canal, título, plataforma e se é ao vivo ('live') ou vídeo pronto ('vod')."""
    p = plataforma(url)
    info = {"url": url, "plataforma": p, "canal": canal_do_link(url), "titulo": "", "modo": "live"}
    if p in ("twitch", "kick") and "/videos/" not in url and "/video/" not in url:
        r = subprocess.run(streamlink() + ["--json", url], capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=SEM_JANELA)
        try:
            meta = json.loads(r.stdout).get("metadata") or {}
            info["titulo"] = meta.get("title") or ""
            info["canal"] = meta.get("author") or info["canal"]
            info["categoria"] = meta.get("category") or ""
        except (ValueError, AttributeError, TypeError):
            pass
        return info
    r = subprocess.run(ytdlp() + ["-J", "--no-playlist", "--no-warnings", url], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=SEM_JANELA)
    if r.returncode != 0:
        motivo = motivo_trancada(r.stderr)
        if motivo:
            raise SystemExit(t("es_bloqueo_sitio", motivo=motivo))
        if p == "youtube" and "will begin" in r.stderr.lower():
            info["titulo"] = "(live agendada)"
            return info   # live agendada: o gravador fica esperando ela começar
        raise SystemExit(t("no_lei_enlace", error=r.stderr[-800:]))
    meta = json.loads(r.stdout)
    info["titulo"] = meta.get("title") or ""
    info["canal"] = meta.get("channel") or meta.get("uploader") or info["canal"]
    info["webpage_url"] = meta.get("webpage_url")
    status = meta.get("live_status")
    info["modo"] = "live" if status in ("is_live", "is_upcoming", "post_live") or meta.get("is_live") else "vod"
    if info["modo"] == "live" and meta.get("webpage_url"):
        info["url"] = meta["webpage_url"]   # /@canal/live vira o link fixo da live
    return info


def pasta_para(info):
    nome = slug(info.get("canal") or "live", 30)
    if info["modo"] == "live":
        nome += "-" + datetime.now().strftime("%Y-%m-%d")
    else:
        nome += "-" + slug(info.get("titulo") or "video", 30)
    return pasta_lives() / nome


# ================================================================ limpeza
def analisado_ate(pasta):
    """Tempo da gravação até onde a IA já leu E os cortes já foram montados (em sequência, sem buraco)."""
    estado = ler_json(pasta / "estado.json", {"blocos": []})
    feitos = set(estado.get("cortados", []))
    ate = 0.0
    for b in estado["blocos"]:
        if b["n"] not in feitos:
            break
        ate = b["fim"]
    return ate


def limpeza(aviso):
    cfg = config()
    cota = cfg["gb"] * 1024 ** 3
    uso = tamanho(pasta_dados())
    guardar = cfg["guardar_min"] * 60
    apagados = 0
    candidatos = []   # (prioridade, inicio, segmento)
    for p in todas_as_lives():
        ate = analisado_ate(p)
        for s in segmentos(p, gravando=vigia_rodando(p)):
            if not s["completo"]:
                continue
            escutado = (p / "escuta" / (s["arquivo"].stem + ".json")).exists()
            if s["fim"] <= ate:
                candidatos.append((0 if s["fim"] < ate - guardar else 1, s["inicio"], s, p))
            elif escutado:
                candidatos.append((2, s["inicio"], s, p))   # só em último caso: ainda não foi analisado
    candidatos.sort(key=lambda c: (c[0], c[1]))
    for prioridade, _, s, p in candidatos:
        if prioridade == 1 and uso < cota * 0.85:
            continue
        if prioridade == 2 and uso < cota * 0.95:
            continue
        try:
            tam = s["arquivo"].stat().st_size
            s["arquivo"].unlink()
            uso -= tam
            apagados += 1
            if prioridade == 2:
                aviso(t("espacio_aviso", arq=f"{p.name}/{s['arquivo'].name}"))
        except OSError:
            pass
    if apagados:
        log(t("limpieza", n=apagados, uso=gb(uso), cota=cfg["gb"]))
    return uso


# ================================================================ o vigia
def vigiar(url):
    info = ler_link(url)
    pasta = pasta_para(info)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "parar").unlink(missing_ok=True)
    antigo = ler_json(pasta / "info.json", {})
    info["comecou"] = antigo.get("comecou") or datetime.now().strftime("%Y-%m-%d %H:%M")
    gravar_json(pasta / "info.json", info)
    b = ler_json(pasta / "batimento.json", {})   # avisa logo que ligou (apaga o "encerrado" de uma parada anterior)
    b.update(t=agora(), encerrado=False, gravando=False, erro=None)
    gravar_json(pasta / "batimento.json", b)
    log(t("vigilando", canal=info.get("canal"), titulo=info.get("titulo"), plataforma=info["plataforma"],
          modo=info["modo"]))
    log(t("carpeta_log", p=pasta))

    parar = threading.Event()
    avisos = []

    def aviso(msg):
        log(msg)
        avisos.append(msg)
        avisos[:] = avisos[-5:]

    gravador = None
    if info["modo"] == "live":
        gravador = Gravador(pasta, info["url"], parar)
        gravador.start()
    else:
        baixar_vod(pasta, info["url"], parar)
    chat = Chat(pasta, info["url"], parar)
    chat.start()
    ouvinte = Ouvinte(pasta, parar, gravador)
    ouvinte.start()

    estado = {"ultima_limpeza": 0, "uso": 0}

    def volta():
        """Uma volta do vigia (a cada 10 s). Devolve True quando a live acabou e tudo foi escutado."""
        if (pasta / "parar").exists() and not parar.is_set():
            log(t("pidieron_parar"))
            parar.set()
            if gravador:
                gravador.interromper()
        acabou_gravacao = gravador is None or gravador.encerrada
        horizonte = horizonte_escutado(pasta)
        pendentes = [s for s in segmentos(pasta, bool(gravador and gravador.gravando))
                     if s["completo"] and not (pasta / "escuta" / (s["arquivo"].stem + ".json")).exists()]
        terminou = acabou_gravacao and not pendentes and ouvinte.horizonte >= horizonte - 1
        if parar.is_set() and acabou_gravacao:
            terminou = True
        talvez_novo_bloco(pasta, horizonte, encerrada=terminou)
        if agora() - estado["ultima_limpeza"] > 60:
            estado["uso"] = limpeza(aviso)
            estado["ultima_limpeza"] = agora()
        gravar_json(pasta / "batimento.json", {
            "t": agora(), "gravando": bool(gravador and gravador.gravando), "horizonte": horizonte,
            "fila_escuta": len(pendentes), "chat_mensagens": chat.total, "chat_ok": chat.funcionando,
            "erro": gravador.erro if gravador else None, "avisos": avisos, "uso_gb": round(gb(estado["uso"]), 1),
            "cota_gb": config()["gb"], "encerrado": terminou, "modo": info["modo"]})
        if terminou:
            log(t("directo_terminado"))
            parar.set()
        return terminou

    try:
        while True:
            try:
                if volta():
                    break
            except Exception as e:   # um erro solto numa volta não pode derrubar a gravação
                log(f"vigia: {type(e).__name__}: {str(e)[:200]}")
            time.sleep(10)
    except KeyboardInterrupt:
        parar.set()
        if gravador:
            gravador.interromper()
        b = ler_json(pasta / "batimento.json", {})
        b.update(encerrado=True, t=agora())
        gravar_json(pasta / "batimento.json", b)
