"""Lê o chat ao vivo e guarda cada mensagem com o tempo da gravação em chat.jsonl.

Twitch:  IRC anônimo (não precisa de conta nem de chave)
YouTube: o próprio yt-dlp acompanha o chat ao vivo (ou o replay, em vídeo que já acabou)
Kick:    websocket público do chat (se a Kick bloquear, o clipper segue só com fala e volume)
"""
import json
import random
import socket
import subprocess
import threading
import time
from pathlib import Path

from comum import SEM_JANELA, agora, canal_do_link, ler_json, log, plataforma, ytdlp
from textos import t


class Chat(threading.Thread):
    def __init__(self, pasta, url, parar):
        super().__init__(daemon=True, name="chat")
        self.pasta, self.url, self.parar = pasta, url, parar
        self.arquivo = pasta / "chat.jsonl"
        self.total = 0
        self.funcionando = False
        self._trava = threading.Lock()

    # -------------------------------------------------- comum
    def _inicio(self):
        return ler_json(self.pasta / "sessao.json", {}).get("inicio")

    def anotar(self, epoch, usuario, texto):
        ini = self._inicio()
        if ini is None or not texto:
            return   # ainda não começou a gravar: mensagem sem lugar na linha do tempo
        linha = json.dumps({"t": round(epoch - ini, 1), "u": usuario, "m": texto[:300]}, ensure_ascii=False)
        with self._trava, open(self.arquivo, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
        self.total += 1
        self.funcionando = True

    def run(self):
        p = plataforma(self.url)
        alvo = {"twitch": self._twitch, "youtube": self._youtube, "kick": self._kick}.get(p)
        if not alvo:
            log(t("chat_sin_lector"))
            return
        falhas = 0
        while not self.parar.is_set():
            try:
                alvo()
                falhas = 0
            except Exception as e:  # chat é bônus: nunca derruba o clipper
                falhas += 1
                log(t("chat_cayo", error=f"{type(e).__name__}: {str(e)[:120]}"))
            if self.parar.wait(min(300, 15 * (falhas + 1))):
                break

    # -------------------------------------------------- Twitch (IRC anônimo)
    def _twitch(self):
        canal = canal_do_link(self.url)
        if not canal:
            raise RuntimeError(t("chat_sin_canal"))
        s = socket.create_connection(("irc.chat.twitch.tv", 6667), timeout=30)
        s.settimeout(30)
        s.sendall(f"NICK justinfan{random.randint(10000, 99999)}\r\nJOIN #{canal}\r\n".encode())
        log(t("chat_leyendo", plataforma="Twitch", canal="#" + canal))
        buf = b""
        ultimo = agora()
        try:
            while not self.parar.is_set():
                try:
                    dado = s.recv(65536)
                except socket.timeout:
                    if agora() - ultimo > 330:
                        raise RuntimeError(t("chat_twitch_mudo"))
                    s.sendall(b"PING :tmi.twitch.tv\r\n")
                    continue
                if not dado:
                    raise RuntimeError(t("chat_twitch_cerro"))
                ultimo = agora()
                buf += dado
                *linhas, buf = buf.split(b"\r\n")
                for l in linhas:
                    linha = l.decode("utf-8", "ignore")
                    if linha.startswith("PING"):
                        s.sendall(b"PONG :tmi.twitch.tv\r\n")
                    elif " PRIVMSG #" in linha:
                        quem = linha[1:linha.find("!")] if linha.startswith(":") else "?"
                        self.anotar(agora(), quem, linha.split(" :", 1)[1] if " :" in linha else "")
        finally:
            s.close()

    # -------------------------------------------------- YouTube (yt-dlp acompanha o chat)
    def _youtube(self):
        cdir = self.pasta / "chat_youtube"
        cdir.mkdir(exist_ok=True)
        log(t("chat_leyendo", plataforma="YouTube", canal=""))
        proc = subprocess.Popen(ytdlp() + ["--skip-download", "--write-subs", "--sub-langs", "live_chat",
                                           "--no-warnings", "-q", "--no-playlist", "-o", str(cdir / "chat"), self.url],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=SEM_JANELA)
        posicao = {}
        try:
            while True:
                fim = proc.poll() is not None
                for arq in cdir.glob("chat*.live_chat.json*"):
                    if "Frag" in arq.name:
                        continue   # pedaço bruto que o yt-dlp ainda está juntando
                    chave = arq.name.replace(".part", "")   # quando .part vira .json, continua de onde parou
                    posicao[chave] = self._ler_youtube(arq, posicao.get(chave, 0))
                if fim or self.parar.wait(5):
                    break
        finally:
            if proc.poll() is None:
                proc.terminate()

    def _ler_youtube(self, arq, desde):
        try:
            with open(arq, "rb") as f:
                f.seek(desde)
                dados = f.read()
        except OSError:
            return desde
        corte = dados.rfind(b"\n") + 1      # só linhas inteiras
        for linha in dados[:corte].splitlines():
            try:
                item = json.loads(linha)
                acao = item.get("replayChatItemAction", {})
                for a in acao.get("actions", []):
                    r = a.get("addChatItemAction", {}).get("item", {})
                    r = r.get("liveChatTextMessageRenderer") or r.get("liveChatPaidMessageRenderer")
                    if not r:
                        continue
                    texto = "".join(run.get("text") or run.get("emoji", {}).get("shortcuts", [""])[0]
                                    for run in r.get("message", {}).get("runs", []))
                    quem = r.get("authorName", {}).get("simpleText", "?")
                    if item.get("isLive") and r.get("timestampUsec"):
                        epoch = int(r["timestampUsec"]) / 1e6
                    else:   # replay de vídeo que já acabou: o tempo vem como posição no vídeo
                        epoch = (self._inicio() or 0) + int(item.get("videoOffsetTimeMsec", 0)) / 1000
                    self.anotar(epoch, quem, texto)
            except (ValueError, KeyError, TypeError, IndexError):
                continue
        return desde + corte

    # -------------------------------------------------- Kick (websocket público)
    KICK_CHAVE = ("34bf7a0ff419a2a775b9", "us2")   # reserva, se o pedido da chave atual falhar

    def _kick_ws(self):
        """A Kick troca a chave do chat de vez em quando: pede a atual toda vez que conecta."""
        import uuid
        from streamlink import Streamlink
        chave, cluster = self.KICK_CHAVE
        try:
            r = Streamlink().http.post(
                "https://web.kick.com/api/v1/realtime/connection", timeout=20, raise_for_status=False,
                json={"client": {"id": str(uuid.uuid4()), "type": "web"},
                      "capabilities": {"accepted_providers": [{"provider": "pusher"}]}})
            for c in r.json()["data"]["connections"]:
                if c.get("provider") == "pusher":
                    chave, cluster = c["credentials"]["app_key"], c["credentials"]["cluster"]
        except Exception:
            pass
        return f"wss://ws-{cluster}.pusher.com/app/{chave}?protocol=7&client=js&version=8.4.0&flash=false"

    def _kick_sala(self, canal):
        """Descobre o número da sala de chat do canal (a Kick às vezes bloqueia esse pedido)."""
        from streamlink import Streamlink
        http = Streamlink().http
        http.headers.update({"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                            "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"),
                             "Accept": "application/json"})
        for url in (f"https://kick.com/api/v2/channels/{canal}", f"https://kick.com/api/v1/channels/{canal}"):
            try:
                r = http.get(url, timeout=20, raise_for_status=False)
                if r.status_code == 200:
                    return r.json()["chatroom"]["id"]
            except Exception:
                continue
        return None

    def _kick(self):
        import websocket
        canal = canal_do_link(self.url)
        sala = self._kick_sala(canal) if canal else None
        if not sala:
            log(t("chat_kick_bloqueo"))
            self.parar.wait(600)
            return
        ws = websocket.create_connection(self._kick_ws(), timeout=60)
        ws.send(json.dumps({"event": "pusher:subscribe", "data": {"auth": "", "channel": f"chatrooms.{sala}.v2"}}))
        log(t("chat_leyendo", plataforma="Kick", canal=canal))
        try:
            while not self.parar.is_set():
                try:
                    msg = json.loads(ws.recv())
                except websocket.WebSocketTimeoutException:
                    ws.send(json.dumps({"event": "pusher:ping", "data": {}}))
                    continue
                if msg.get("event") == "pusher:error":
                    raise RuntimeError(t("chat_kick_rechazo", datos=msg.get("data")))
                if msg.get("event") == "pusher:ping":
                    ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
                elif msg.get("event", "").endswith("ChatMessageEvent"):
                    d = json.loads(msg["data"])
                    self.anotar(agora(), d.get("sender", {}).get("username", "?"), d.get("content", ""))
        finally:
            ws.close()


def ler_mensagens(pasta, ini=None, fim=None):
    arq = Path(pasta) / "chat.jsonl"
    if not arq.exists():
        return []
    out = []
    with open(arq, encoding="utf-8", errors="ignore") as f:
        for linha in f:
            try:
                m = json.loads(linha)
            except ValueError:
                continue
            if (ini is None or m["t"] >= ini) and (fim is None or m["t"] < fim):
                out.append(m)
    return out


if __name__ == "__main__":   # teste rápido: python chat.py LINK  (lê 60 s de chat)
    import sys
    import tempfile
    pasta = Path(tempfile.mkdtemp())
    (pasta / "sessao.json").write_text(json.dumps({"inicio": int(time.time())}))
    parar = threading.Event()
    c = Chat(pasta, sys.argv[1], parar)
    c.start()
    time.sleep(int(sys.argv[2]) if len(sys.argv) > 2 else 60)
    parar.set()
    print(t("chat_prueba", n=c.total, arq=pasta / "chat.jsonl"))
