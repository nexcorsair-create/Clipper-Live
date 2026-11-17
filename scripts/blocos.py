"""A cada 30 min de live escutada, monta um bloco de texto pra IA ler: a fala com marcas de grito e de chat agitado.

Marcas em cada linha:
  [ALTO +12dB]   o streamer ficou muito mais alto que o normal dos 5 min em volta (grito, surto, susto)
  [CHAT 3.4x]    o chat andou 3,4 vezes mais rápido que o normal
  [RISADA/HYPE]  no pico do chat, a maioria das mensagens era KKKK, KEKW, CLIPA, ????, etc.
No fim do bloco vai a lista dos picos do chat com exemplos do que a galera escreveu.
"""
import re
from collections import Counter

import numpy as np

from chat import ler_mensagens
from comum import config, gravar_json, hms, ler_json, log
from ouvinte import escuta_entre
from textos import t

HYPE = re.compile(r"(k{4,}|(?:ha|ah|hs|rs|sk|ja|aj|js|sj){3,}|xd+|kekw|lul|lmao|lmfao|pog|clip|corta|no mames|joder|hostia|dios mio|que locura|\?{3,}|!{3,}|😂|🤣|😱|💀|"
                  r"wtf|omg|caralho|cacete|mds|meu deus|nossa|insano|absurdo|gg|f+\b)", re.I)


# ---------------------------------------------------------------- sinais
def picos_de_volume(db, ini, fim):
    """{segundo: dB acima do normal} para os segundos em que o streamer gritou."""
    if not db:
        return {}
    seg = np.array(sorted(db))
    val = np.array([db[s] for s in seg])
    falando = val > np.percentile(val, 20)
    picos = {}
    excessos = []
    for s, v in zip(seg, val):
        janela = val[(np.abs(seg - s) <= 150) & falando]
        base = np.median(janela) if len(janela) else np.median(val)
        excessos.append(v - base)
    excessos = np.array(excessos)
    corte = max(8.0, float(np.percentile(excessos, 98)))
    for s, e in zip(seg, excessos):
        if ini <= s < fim and e >= corte:
            picos[int(s)] = round(float(e), 1)
    return picos


def picos_do_chat(msgs, ini, fim):
    """[(segundo, vezes acima do normal, % de hype, exemplos)] a cada 10 s em que o chat acelerou."""
    if len(msgs) < 30:
        return []
    caixas = {}
    for m in msgs:
        caixas.setdefault(int(m["t"] // 10), []).append(m["m"])
    # o "normal" só conta de onde o chat começou a ser lido (senão o começo da live parece um pico gigante)
    k0, k1 = max(int((ini - 300) // 10), min(caixas) + 1), int(fim // 10)
    contagem = np.array([len(caixas.get(k, [])) for k in range(k0, k1 + 1)])
    picos = []
    for i, k in enumerate(range(k0, k1 + 1)):
        if k * 10 < ini:
            continue
        viz = contagem[max(0, i - 30): i + 30]
        normal = max(1.0, float(np.median(viz)))
        c = contagem[i]
        if c >= 6 and c / normal >= 2.5:
            textos = caixas.get(k, [])
            hype = sum(bool(HYPE.search(t)) for t in textos) / max(1, len(textos))
            curtos = Counter(t.strip()[:40] for t in textos if t.strip()).most_common(6)
            picos.append((k * 10, round(c / normal, 1), round(hype * 100), [t for t, _ in curtos]))
    return picos


# ---------------------------------------------------------------- bloco
def escrever_bloco(pasta, n, ini, fim):
    fala, db = escuta_entre(pasta, ini, fim)
    _, db_contexto = escuta_entre(pasta, ini - 300, fim)
    vol = picos_de_volume(db_contexto, ini, fim)
    msgs = ler_mensagens(pasta, ini - 300, fim)
    chat = picos_do_chat(msgs, ini, fim)
    linhas = []
    for s, e, frase in fala:
        marca = ""
        alto = max((vol.get(x, 0) for x in range(int(s), int(e) + 1)), default=0)
        if alto:
            marca += f"  [{t('marca_alto')} +{alto:.0f}dB]"
        perto = [p for p in chat if s - 15 <= p[0] <= e + 5]   # o chat reage uns segundos depois
        if perto:
            p = max(perto, key=lambda p: p[1])
            marca += f"  [CHAT {p[1]}x]" + (f"  [{t('marca_risa')}]" if p[2] >= 50 else "")
        linhas.append(f"[{hms(s)}] {frase}{marca}")
    info = ler_json(pasta / "info.json", {})
    cab = [t("bloque_cab", n=n, ini=hms(ini), fin=hms(fim)),
           t("bloque_directo", titulo=info.get("titulo", ""), canal=info.get("canal", "")),
           t("bloque_escribe", n=n),
           t("bloque_msgs", n=sum(1 for m in msgs if m["t"] >= ini)), ""]
    corpo = linhas or [t("bloque_vacio")]
    rodape = []
    if chat:
        rodape = ["", t("picos_cab")]
        for seg, x, h, ex in sorted(chat, key=lambda p: -p[1])[:15]:
            rodape.append(f"[{hms(seg)}] {x}x | {h}% | " + " · ".join(ex))
    bdir = pasta / "bloques"
    bdir.mkdir(exist_ok=True)
    (pasta / "momentos").mkdir(exist_ok=True)
    (bdir / f"bloque_{n:02d}.txt").write_text("\n".join(cab + corpo + rodape) + "\n", encoding="utf-8")
    return len(linhas), len(vol), len(chat)


def talvez_novo_bloco(pasta, horizonte, encerrada=False):
    """Fecha um bloco quando já tem 30 min escutados depois do último (ou o que sobrou, se a live acabou)."""
    cfg = config()
    passo = cfg["bloco_min"] * 60
    estado = ler_json(pasta / "estado.json", {"blocos": []})
    ultimo_fim = estado["blocos"][-1]["fim"] if estado["blocos"] else 0.0
    novos = []
    while horizonte - ultimo_fim >= passo or (encerrada and horizonte - ultimo_fim >= 30):
        fim = min(ultimo_fim + passo, horizonte)
        n = len(estado["blocos"]) + 1
        falas, gritos, chats = escrever_bloco(pasta, n, ultimo_fim, fim)
        estado["blocos"].append({"n": n, "ini": ultimo_fim, "fim": fim})
        gravar_json(pasta / "estado.json", estado)
        log(t("bloque_listo", n=n, ini=hms(ultimo_fim), fin=hms(fim), frases=falas, gritos=gritos, chats=chats))
        novos.append(n)
        ultimo_fim = fim
    return novos


def blocos_sem_momentos(pasta):
    estado = ler_json(pasta / "estado.json", {"blocos": []})
    return [b for b in estado["blocos"] if not (pasta / "momentos" / f"bloque_{b['n']:02d}.json").exists()]
