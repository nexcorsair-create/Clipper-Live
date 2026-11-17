#!/usr/bin/env python3
"""Clipper Live: mira directos EN VIVO y va separando clips verticales mientras el streamer juega.

Comandos (español | english | português):
  instalar   | install   | instalar     instala/revisa todo (Streamlink, yt-dlp, ffmpeg, Whisper)
  configurar | configure | configurar   --carpeta X --gb 50 --lengua es|en|pt
  actualizar | update    | atualizar    actualiza todo (y vuelve atrás si algo se rompe)
  verificar  | check     | verificar    muestra qué está instalado
  buscar     | search    | buscar       directos de GTA 6 en vivo ahora (Twitch + YouTube)
  vigilar    | watch     | vigiar       empieza a grabar/escuchar el directo en segundo plano
  esperar    | wait      | esperar      espera al próximo bloque de 30 min para que la IA lo lea
  cortar     | cut       | cortar       monta los clips de los bloques que la IA ya leyó
  pendientes | pending   | pendentes    clips esperando aprobación
  aprobar    | approve   | aprovar      N [N…] aprueba (va a aprobados/)
  rechazar   | reject    | recusar      N [N…] rechaza (se borra)
  estado     | status    | status       cómo va cada directo
  detener    | stop      | parar        deja de vigilar
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from comum import (APP, CONFIG, SEM_JANELA, VENV, VENV_PY, agora, config, gravar_json, hms, ler_json,  # noqa: E402
                   pasta_cortes, pasta_da_live, preparar_ffmpeg, todas_as_lives, vigia_rodando)
from textos import LENGUAS, t  # noqa: E402

ALIAS = {   # comando en español (principal) -> otros nombres que también funcionan
    "instalar": ["install"], "configurar": ["configure", "config"], "actualizar": ["update", "atualizar"],
    "verificar": ["check"], "buscar": ["search"], "vigilar": ["watch", "vigiar"], "esperar": ["wait"],
    "cortar": ["cut"], "pendientes": ["pending", "pendentes"], "aprobar": ["approve", "aprovar"],
    "rechazar": ["reject", "recusar"], "estado": ["status"], "detener": ["stop", "parar"],
}


def no_ambiente():
    """Roda sempre com o Python do próprio clipper (criado no instalar)."""
    instalar = sys.argv[1:2] and sys.argv[1] in ["instalar"] + ALIAS["instalar"]
    if VENV_PY.exists() and Path(sys.prefix).resolve() != VENV.resolve() and not instalar:
        r = subprocess.run([str(VENV_PY), __file__, *sys.argv[1:]])
        sys.exit(r.returncode)


def certificados():
    try:
        import certifi
        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
        os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
    except ImportError:
        pass


def configurado():
    return "pasta" in (ler_json(CONFIG, {}) or {})


# ================================================================ comandos
def c_instalar(a):
    from ambiente import instalar
    instalar()


def c_configurar(a):
    from ambiente import configurar
    extras = {k: getattr(a, k) for k in ("lengua", "bloco_min", "nota_minima", "max_por_bloco", "qualidade",
                                         "idioma", "modelo_live", "modelo_legenda") if getattr(a, k) is not None}
    configurar(a.pasta, a.gb, **extras)


def c_actualizar(a):
    from ambiente import atualizar
    sys.exit(0 if atualizar(forcar=True) else 1)


def c_verificar(a):
    from ambiente import verificar
    verificar()


def c_buscar(a):
    from buscar import buscar
    buscar(a.cuantos, a.juego, a.idioma)


def c_vigilar(a):
    if not configurado():
        sys.exit(t("antes_config"))
    from ambiente import atualizar
    atualizar(forcar=False)   # atualiza Streamlink/yt-dlp se faz tempo (e se nenhuma live está gravando)
    logs = APP / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    for link in a.enlaces:
        arq = logs / f"vigia-{time.strftime('%Y%m%d-%H%M%S')}-{abs(hash(link)) % 10000}.log"
        f = open(arq, "a", encoding="utf-8")
        opcoes = dict(stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=str(AQUI))
        if os.name == "nt":   # processo independente: continua mesmo se fechar o terminal/Claude
            opcoes["creationflags"] = 0x00000008 | 0x00000200 | SEM_JANELA   # DETACHED | NEW_PROCESS_GROUP
        else:
            opcoes["start_new_session"] = True
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        subprocess.Popen([sys.executable, str(AQUI / "clip.py"), "_vigilar", link], env=env, **opcoes)
        print(t("vigia_encendido", enlace=link, arq=arq))
    print(t("esperando_primeros", min=config()["bloco_min"]))
    lanzado = agora()
    limite = lanzado + 90   # espera o vigia ler o link e criar a pasta da live
    while agora() < limite and not any(vigia_rodando(p) for p in todas_as_lives()) and not _error_vigia(lanzado):
        time.sleep(5)
    time.sleep(10)
    if not _mostrar_error_vigia(lanzado):
        c_estado(a)


ERROR_VIGIA = APP / "logs" / "ultimo_error.json"


def _error_vigia(desde):
    e = ler_json(ERROR_VIGIA, {})
    return e if e and e.get("t", 0) >= desde else None


def _mostrar_error_vigia(desde):
    e = _error_vigia(desde)
    if e:
        print(t("vigia_fallo", enlace=e.get("enlace"), error=e.get("error")))
    return bool(e)


def c__vigilar(a):
    from vigia import vigiar
    try:
        vigiar(a.enlace)
    except (Exception, SystemExit) as e:   # deixa o motivo anotado pro 'vigilar'/'esperar' mostrarem
        import traceback
        if isinstance(e, SystemExit) and not isinstance(e.code, str):
            raise
        msg = e.code if isinstance(e, SystemExit) else traceback.format_exc(limit=3)[-800:]
        gravar_json(ERROR_VIGIA, {"t": agora(), "enlace": a.enlace, "error": msg})
        raise


def _momentos(p, n):
    return p / "momentos" / f"bloque_{n:02d}.json"


def _bloques_sin_cortar(p):
    estado = ler_json(p / "estado.json", {"blocos": []})
    feitos = set(estado.get("cortados", []))
    return [b for b in estado["blocos"] if b["n"] not in feitos and _momentos(p, b["n"]).exists()]


def c_esperar(a):
    """Espera até ter bloco novo pra IA ler (ou até --max segundos). Feito pra ser chamado em loop."""
    from blocos import blocos_sem_momentos
    fim = agora() + a.max
    while True:
        lives = [pasta_da_live(a.directo)] if a.directo else todas_as_lives()
        prontos = [(p, b) for p in lives for b in blocos_sem_momentos(p)]
        if prontos:
            print(t("bloque_para_leer"))
            for p, b in prontos:
                print(f"  {p / 'bloques' / ('bloque_%02d.txt' % b['n'])}")
                print(t("escribe_en", arq=_momentos(p, b["n"])))
            return
        sem_cortar = [p for p in lives if _bloques_sin_cortar(p)]
        if sem_cortar:
            print(t("falta_cortar", nombre=sem_cortar[0].name))
            return
        ativas = [p for p in lives if vigia_rodando(p)]
        if not ativas:
            ultimo = max((ler_json(p / "batimento.json", {}).get("t", 0) for p in lives), default=0)
            if _mostrar_error_vigia(max(ultimo, agora() - 6 * 3600)):
                return
            print(t("ninguno_vigilado") if lives else t("sin_directos"))
            _resumo(lives)
            return
        if agora() >= fim:
            print(t("aun_no"))
            _resumo(ativas)
            return
        time.sleep(15)


def c_cortar(a):
    from cortes import cortar, mostrar_pendentes
    lives = [pasta_da_live(a.directo)] if a.directo else [p for p in todas_as_lives() if _bloques_sin_cortar(p)]
    for p in lives:
        print(f"== {p.name}")
        cortar(p)
    print()
    mostrar_pendentes()


def c_pendientes(a):
    from cortes import mostrar_pendentes
    mostrar_pendentes()


def c_aprobar(a):
    from cortes import decidir
    decidir(a.numeros, True)


def c_rechazar(a):
    from cortes import decidir
    decidir(a.numeros, False)


def c_detener(a):
    alvo = todas_as_lives() if a.directo in (None, "todas", "todos", "all") else [pasta_da_live(a.directo)]
    for p in alvo:
        if vigia_rodando(p):
            (p / "parar").write_text("ok")
            print(t("pedi_parar", nombre=p.name))


def _resumo(lives):
    from cortes import registro
    reg = registro()["cortes"]
    cfg = config()
    for p in lives:
        info = ler_json(p / "info.json", {})
        b = ler_json(p / "batimento.json", {})
        estado = ler_json(p / "estado.json", {"blocos": []})
        leidos = sum(1 for x in estado["blocos"] if _momentos(p, x["n"]).exists())
        clips = [c for c in reg if c["live"] == p.name]
        rodando = vigia_rodando(p)
        if rodando:
            situacion = t("st_grabando") if b.get("gravando") else t("st_esperando")
        else:
            situacion = t("st_terminado") if b.get("encerrado") else t("st_parado")
        prox = ""
        if rodando:
            ult = estado["blocos"][-1]["fim"] if estado["blocos"] else 0
            falta = cfg["bloco_min"] * 60 - (b.get("horizonte", 0) - ult)
            prox = t("st_proximo", min=max(1, int((falta + cfg["segmento_s"]) // 60) + 1))
        print(f"{p.name}: {situacion}\n  {info.get('titulo', '')[:90]}")
        print(t("st_linea", hasta=hms(b.get("horizonte", 0)), cola=b.get("fila_escuta", 0),
                msgs=b.get("chat_mensagens", 0), sinchat="" if b.get("chat_ok") else t("st_sin_chat"), prox=prox,
                leidos=leidos, bloques=len(estado["blocos"]),
                pend=sum(c["status"] == "pending" for c in clips), aprob=sum(c["status"] == "approved" for c in clips),
                uso=b.get("uso_gb", "?"), cota=cfg["gb"]))
        if b.get("erro"):
            print(t("st_error", e=b["erro"]))
        for av in b.get("avisos", [])[-2:]:
            print(t("st_aviso", e=av))


def c_estado(a):
    lives = todas_as_lives()
    if not lives:
        print(t("sin_directos"))
        return
    ativas = [p for p in lives if vigia_rodando(p)]
    _resumo(ativas or lives[-3:])
    print(t("st_clips", p=pasta_cortes()))


# ================================================================ main
def main():
    no_ambiente()
    certificados()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Clipper Live")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def cmd(nombre, funcion):
        p = sub.add_parser(nombre, aliases=ALIAS.get(nombre, []))
        p.set_defaults(f=funcion)
        return p

    cmd("instalar", c_instalar)
    c = cmd("configurar", c_configurar)
    c.add_argument("--carpeta", "--folder", "--pasta", dest="pasta")
    c.add_argument("--gb", type=float)
    c.add_argument("--lengua", "--language", "--lingua", dest="lengua", choices=LENGUAS)
    c.add_argument("--bloque-min", "--block-min", "--bloco-min", dest="bloco_min", type=int)
    c.add_argument("--nota-minima", "--min-score", dest="nota_minima", type=int)
    c.add_argument("--max-por-bloque", "--max-per-block", "--max-por-bloco", dest="max_por_bloco", type=int)
    c.add_argument("--calidad", "--quality", "--qualidade", dest="qualidade")
    c.add_argument("--idioma-directo", "--stream-language", "--idioma", dest="idioma")
    c.add_argument("--modelo-directo", "--live-model", "--modelo-live", dest="modelo_live")
    c.add_argument("--modelo-subtitulos", "--caption-model", "--modelo-legenda", dest="modelo_legenda")
    cmd("actualizar", c_actualizar)
    cmd("verificar", c_verificar)
    b = cmd("buscar", c_buscar)
    b.add_argument("--cuantos", "--count", "--quantas", dest="cuantos", type=int, default=7)
    b.add_argument("--juego", "--game", "--jogo", dest="juego", default="Grand Theft Auto VI")
    b.add_argument("--idioma", "--language", dest="idioma", default=None, help="es, en, pt… (Twitch)")
    v = cmd("vigilar", c_vigilar)
    v.add_argument("enlaces", nargs="+")
    vi = sub.add_parser("_vigilar", aliases=["_vigiar"])
    vi.add_argument("enlace")
    vi.set_defaults(f=c__vigilar)
    e = cmd("esperar", c_esperar)
    e.add_argument("directo", nargs="?")
    e.add_argument("--max", type=int, default=540)
    k = cmd("cortar", c_cortar)
    k.add_argument("directo", nargs="?")
    cmd("pendientes", c_pendientes)
    for nombre, f in (("aprobar", c_aprobar), ("rechazar", c_rechazar)):
        x = cmd(nombre, f)
        x.add_argument("numeros", nargs="+", type=int)
    cmd("estado", c_estado)
    d = cmd("detener", c_detener)
    d.add_argument("directo", nargs="?")
    a = ap.parse_args()
    if a.f not in (c_instalar, c_configurar, c_verificar):
        preparar_ffmpeg()
    a.f(a)


if __name__ == "__main__":
    main()
