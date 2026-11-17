"""Acha as maiores lives de GTA 6 ao vivo AGORA na Twitch e no YouTube."""
import json
import re
import subprocess

from comum import SEM_JANELA, ytdlp
from textos import t

GTA6 = re.compile(r"gta\s*-?\s*(6|vi)(?![0-9a-z])", re.I)
GTA_ANTIGO = re.compile(r"gta\s*-?\s*(5|v|iv|4|rp|online)(?![0-9a-z])", re.I)
TWITCH_JOGO = "Grand Theft Auto VI"
TWITCH_CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"   # o mesmo cliente público que o site da Twitch usa


def twitch(jogo=TWITCH_JOGO, quantas=10):
    """Lives da categoria do jogo, das mais vistas pras menos (pode falhar se a Twitch mudar a API)."""
    from streamlink import Streamlink
    http = Streamlink().http
    consulta = {"query": "query($n:String!,$q:Int){game(name:$n){streams(first:$q){edges{node{"
                         "title viewersCount broadcaster{login displayName} language}}}}}",
                "variables": {"n": jogo, "q": quantas}}
    try:
        r = http.post("https://gql.twitch.tv/gql", json=consulta, headers={"Client-ID": TWITCH_CLIENT_ID},
                      timeout=20)
        arestas = ((r.json().get("data") or {}).get("game") or {}).get("streams", {}).get("edges", [])
    except Exception:
        return []
    return [{"plataforma": "Twitch", "titulo": e["node"]["title"], "canal": e["node"]["broadcaster"]["displayName"],
             "assistindo": e["node"]["viewersCount"], "idioma": e["node"].get("language"),
             "url": f"https://www.twitch.tv/{e['node']['broadcaster']['login']}"} for e in arestas]


def youtube(termos=("GTA 6 en vivo", "GTA 6 en directo", "GTA 6 live", "GTA 6 ao vivo"), quantas=10):
    filtro = "EgJAAQ%3D%3D"   # filtro "Ao vivo" da busca do YouTube
    achadas = {}
    for termo in termos:
        url = f"https://www.youtube.com/results?search_query={termo.replace(' ', '+')}&sp={filtro}"
        r = subprocess.run(ytdlp() + ["--flat-playlist", "-J", "--playlist-end", "30", "--no-warnings", url],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=SEM_JANELA)
        try:
            itens = json.loads(r.stdout).get("entries", [])
        except ValueError:
            itens = []
        for v in itens:
            t = v.get("title") or ""
            if v.get("id") and GTA6.search(t) and not GTA_ANTIGO.search(t):
                achadas[v["id"]] = {"plataforma": "YouTube", "titulo": t,
                                    "canal": v.get("channel") or v.get("uploader") or "?",
                                    "assistindo": v.get("concurrent_view_count") or v.get("view_count") or 0,
                                    "url": f"https://www.youtube.com/watch?v={v['id']}"}
    return sorted(achadas.values(), key=lambda v: -(v["assistindo"] or 0))[:quantas]


def buscar(quantas=7, jogo=TWITCH_JOGO, idioma=None):
    lista = twitch(jogo, 30) + youtube()
    if idioma:
        lista = [v for v in lista if (v.get("idioma") or idioma).lower() == idioma.lower()]
    lista.sort(key=lambda v: -(v["assistindo"] or 0))
    if not lista:
        print(t("busca_nada"))
        return []
    print(t("busca_cab", n=min(quantas, len(lista))))
    for i, v in enumerate(lista[:quantas], 1):
        viendo = t("busca_viendo", n=f"{v['assistindo']:,}".replace(",", "."))
        print(f"  {i}. [{v['plataforma']}] {v['canal']} — {v['titulo'][:80]}\n     {viendo} | {v['url']}\n")
    return lista[:quantas]
