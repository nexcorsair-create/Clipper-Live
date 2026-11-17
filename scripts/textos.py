"""Todos los textos que ve la persona, en español (por defecto), inglés y portugués.

Cambiar el idioma:  clip.py configurar --lengua en     (es | en | pt)
o, antes de instalar, la variable de entorno CLIPPER_LANG=en
"""
import json
import os
from pathlib import Path

LENGUAS = ("es", "en", "pt")
_cache = {}


def lengua():
    if "l" not in _cache:
        l = os.environ.get("CLIPPER_LANG", "").lower()[:2]
        if l not in LENGUAS:
            app = Path(os.environ.get("CLIPPER_LIVE_APP", Path.home() / ".clipper-live"))
            try:
                l = json.loads((app / "config.json").read_text(encoding="utf-8")).get("lengua", "es")
            except (OSError, ValueError):
                l = "es"
        _cache["l"] = l if l in LENGUAS else "es"
    return _cache["l"]


def fijar(l):
    _cache["l"] = l if l in LENGUAS else "es"


def t(clave, **kw):
    txt = T.get(clave)
    if txt is None:
        return clave
    s = txt.get(lengua()) or txt["es"]
    return s.format(**kw) if kw else s


T = {
    # ------------------------------------------------------------ comum
    "sin_directos": {
        "es": "Todavía no hay ningún directo. Empieza con: clip.py vigilar ENLACE",
        "en": "No streams yet. Start with: clip.py watch LINK",
        "pt": "Nenhuma live ainda. Comece com: clip.py vigiar LINK"},
    "directo_no_encontrado": {
        "es": "No encontré el directo '{nombre}' en {carpeta}.",
        "en": "Couldn't find the stream '{nombre}' in {carpeta}.",
        "pt": "Não achei a live '{nombre}' em {carpeta}."},
    "bloqueo_edad": {
        "es": "este directo tiene restricción de edad (pide iniciar sesión)",
        "en": "this stream is age-restricted (requires login)",
        "pt": "essa live é trancada por idade (pede login pra ver)"},
    "bloqueo_miembros": {
        "es": "este directo es solo para miembros/suscriptores del canal",
        "en": "this stream is members/subscribers only",
        "pt": "essa live é só pra membros/inscritos do canal"},
    "bloqueo_login": {
        "es": "este directo pide iniciar sesión (privado o restringido)",
        "en": "this stream requires login (private or restricted)",
        "pt": "essa live pede login (privada ou restrita)"},

    # ------------------------------------------------------------ grabador
    "grabando": {
        "es": "grabando el directo…{extra}", "en": "recording the stream…{extra}", "pt": "gravando a live…{extra}"},
    "con_ytdlp": {"es": " (con yt-dlp)", "en": " (via yt-dlp)", "pt": " (pelo yt-dlp)"},
    "reconectando": {
        "es": "el directo dejó de enviar vídeo; intentando reconectar…",
        "en": "the stream stopped sending video; trying to reconnect…",
        "pt": "a live parou de mandar vídeo; tentando reconectar…"},
    "no_se_puede_grabar": {
        "es": "NO SE PUEDE GRABAR: {motivo}", "en": "CAN'T RECORD: {motivo}", "pt": "NÃO DÁ PRA GRAVAR: {motivo}"},
    "offline": {
        "es": "el directo está offline (o no encontré el vídeo). Lo intento cada minuto. Último aviso de Streamlink: {linea}",
        "en": "the stream is offline (or no video found). Retrying every minute. Last Streamlink message: {linea}",
        "pt": "a live está offline (ou não achei o vídeo). Vou tentando a cada minuto. Último aviso do Streamlink: {linea}"},
    "terminado_sin_senal": {
        "es": "sin señal desde hace {min} min: doy el directo por TERMINADO",
        "en": "no signal for {min} min: treating the stream as ENDED",
        "pt": "sem sinal há {min} min: considerando a live ENCERRADA"},
    "no_empezo": {
        "es": "el directo no empezó en {h} h", "en": "the stream didn't start within {h} h",
        "pt": "a live não começou em {h} h"},
    "vod_descargando": {
        "es": "este enlace no está en directo: descargando el vídeo entero (hasta 720p) para cortar…",
        "en": "this link isn't live: downloading the whole video (up to 720p) to clip…",
        "pt": "esse link não está ao vivo: baixando o vídeo inteiro (até 720p) pra cortar…"},

    # ------------------------------------------------------------ chat
    "chat_sin_lector": {
        "es": "chat: plataforma sin lector de chat; sigo solo con voz y volumen",
        "en": "chat: no chat reader for this platform; using speech and volume only",
        "pt": "chat: plataforma sem leitor de chat; seguindo só com fala e volume"},
    "chat_cayo": {
        "es": "chat: se cayó ({error}); intentando de nuevo", "en": "chat: dropped ({error}); retrying",
        "pt": "chat: caiu ({error}); tentando de novo"},
    "chat_leyendo": {
        "es": "chat: leyendo el chat de {plataforma} de {canal}", "en": "chat: reading {plataforma} chat of {canal}",
        "pt": "chat: lendo o chat da {plataforma} de {canal}"},
    "chat_sin_canal": {
        "es": "no encontré el nombre del canal en el enlace", "en": "couldn't find the channel name in the link",
        "pt": "não achei o nome do canal no link"},
    "chat_twitch_cerro": {
        "es": "Twitch cerró la conexión", "en": "Twitch closed the connection", "pt": "a Twitch fechou a conexão"},
    "chat_twitch_mudo": {
        "es": "el chat de Twitch se quedó mudo", "en": "Twitch chat went silent", "pt": "chat da Twitch ficou mudo"},
    "chat_kick_bloqueo": {
        "es": "chat: Kick bloqueó la lectura del chat; sigo solo con voz y volumen (lo intento de nuevo luego)",
        "en": "chat: Kick blocked chat reading; using speech and volume only (will retry later)",
        "pt": "chat: a Kick bloqueou a leitura do chat; seguindo só com fala e volume (tento de novo depois)"},
    "chat_kick_rechazo": {
        "es": "Kick rechazó el chat: {datos}", "en": "Kick refused the chat: {datos}",
        "pt": "a Kick recusou o chat: {datos}"},
    "chat_prueba": {
        "es": "{n} mensajes en {arq}", "en": "{n} messages in {arq}", "pt": "{n} mensagens em {arq}"},

    # ------------------------------------------------------------ oyente
    "modelo_en": {
        "es": "escucha: modelo '{modelo}' funcionando en {donde}", "en": "listening: model '{modelo}' running on {donde}",
        "pt": "escuta: modelo '{modelo}' rodando no {donde}"},
    "gpu": {"es": "la tarjeta gráfica", "en": "the graphics card", "pt": "placa de vídeo"},
    "cpu": {"es": "el procesador", "en": "the CPU", "pt": "processador"},
    "trozo_listo": {
        "es": "escucha: {arq} listo ({n} frases)", "en": "listening: {arq} done ({n} lines)",
        "pt": "escuta: {arq} pronto ({n} falas)"},
    "trozo_error": {
        "es": "escucha: error en el trozo {arq}: {error}", "en": "listening: error in chunk {arq}: {error}",
        "pt": "escuta: erro no pedaço {arq}: {error}"},

    # ------------------------------------------------------------ bloques
    "marca_alto": {"es": "ALTO", "en": "LOUD", "pt": "ALTO"},
    "marca_risa": {"es": "RISA/HYPE", "en": "LAUGH/HYPE", "pt": "RISADA/HYPE"},
    "bloque_cab": {
        "es": "# BLOQUE {n:02d} — de {ini} a {fin} (tiempo de grabación)",
        "en": "# BLOCK {n:02d} — from {ini} to {fin} (recording time)",
        "pt": "# BLOCO {n:02d} — de {ini} a {fin} (tempo da gravação)"},
    "bloque_directo": {"es": "# Directo: {titulo} | {canal}", "en": "# Stream: {titulo} | {canal}",
                       "pt": "# Live: {titulo} | {canal}"},
    "bloque_escribe": {
        "es": "# Escribe los momentos de este bloque en: momentos/bloque_{n:02d}.json  (aunque esté vacío: [])",
        "en": "# Write this block's moments to: momentos/bloque_{n:02d}.json  (even if empty: [])",
        "pt": "# Escreva os momentos deste bloco em: momentos/bloque_{n:02d}.json  (mesmo vazio: [])"},
    "bloque_msgs": {
        "es": "# Mensajes en el chat en este bloque: {n}", "en": "# Chat messages in this block: {n}",
        "pt": "# Mensagens no chat neste bloco: {n}"},
    "bloque_vacio": {
        "es": "(nadie habló en este tramo, o la escucha falló)", "en": "(nobody spoke here, or listening failed)",
        "pt": "(ninguém falou neste trecho, ou a escuta falhou)"},
    "picos_cab": {
        "es": "# PICOS DEL CHAT (hora | veces sobre lo normal | % risa/hype | lo que escribió la gente)",
        "en": "# CHAT PEAKS (time | times above normal | % laugh/hype | what people wrote)",
        "pt": "# PICOS DO CHAT (hora | vezes acima do normal | % risada/hype | o que a galera escreveu)"},
    "bloque_listo": {
        "es": "BLOQUE {n:02d} listo ({ini}–{fin}): {frases} frases, {gritos} s de grito, {chats} picos de chat",
        "en": "BLOCK {n:02d} ready ({ini}–{fin}): {frases} lines, {gritos} s of shouting, {chats} chat peaks",
        "pt": "BLOCO {n:02d} pronto ({ini}–{fin}): {frases} falas, {gritos} s de grito, {chats} picos de chat"},

    # ------------------------------------------------------------ clips
    "clip_cab": {
        "es": "\nClip {n:03d}: {titulo}  ({ini}–{fin}, nota {nota})",
        "en": "\nClip {n:03d}: {titulo}  ({ini}–{fin}, score {nota})",
        "pt": "\nCorte {n:03d}: {titulo}  ({ini}–{fin}, nota {nota})"},
    "camara_si": {"es": "      cámara del streamer encontrada", "en": "      streamer camera found",
                  "pt": "      câmera do streamer achada"},
    "camara_no": {"es": "      sin cámara: juego con fondo desenfocado", "en": "      no camera: gameplay on blurred background",
                  "pt": "      sem câmera: jogo com fundo desfocado"},
    "subtitulo_modelo": {
        "es": "      (subtítulos con el modelo '{modelo}' en {donde})",
        "en": "      (captions with model '{modelo}' on {donde})",
        "pt": "      (legenda com o modelo '{modelo}' no {donde})"},
    "clip_listo": {"es": "      LISTO: {arq}", "en": "      DONE: {arq}", "pt": "      PRONTO: {arq}"},
    "clip_fallo": {"es": "      no pude montarlo ({error}); lo salto", "en": "      couldn't build it ({error}); skipping",
                   "pt": "      não consegui montar ({error}); pulando"},
    "clip_sin_grabacion": {
        "es": "      la grabación de ese tramo ya no existe (se borró o se cayó el directo); lo salto",
        "en": "      that part of the recording no longer exists (deleted or stream dropped); skipping",
        "pt": "      a gravação desse trecho não existe mais (já foi apagada ou a live caiu); pulando"},
    "clip_solapa": {
        "es": "  salté '{titulo}' ({ini}): usa el mismo tramo que un clip ya hecho",
        "en": "  skipped '{titulo}' ({ini}): same part as an existing clip",
        "pt": "  pulei '{titulo}' ({ini}): pega o mesmo trecho de um corte já feito"},
    "json_invalido": {
        "es": "ATENCIÓN: {arq} no es un JSON válido. Corrígelo y vuelve a ejecutar 'cortar'.",
        "en": "WARNING: {arq} is not valid JSON. Fix it and run 'cut' again.",
        "pt": "ATENÇÃO: {arq} não é um JSON válido. Corrija e rode 'cortar' de novo."},
    "ningun_clip_nuevo": {
        "es": "\nNingún clip nuevo (ningún momento pasó la nota mínima o ya estaban cortados).",
        "en": "\nNo new clips (no moment passed the minimum score, or they were already cut).",
        "pt": "\nNenhum corte novo (nenhum momento passou da nota mínima ou já estavam cortados)."},
    "clips_nuevos": {
        "es": "\n{n} clip(s) nuevo(s) esperando aprobación en {carpeta}",
        "en": "\n{n} new clip(s) waiting for approval in {carpeta}",
        "pt": "\n{n} corte(s) novo(s) esperando aprovação em {carpeta}"},
    "sin_pendientes": {"es": "Ningún clip esperando aprobación.", "en": "No clips waiting for approval.",
                       "pt": "Nenhum corte esperando aprovação."},
    "pendientes_cab": {"es": "{n} clip(s) esperando aprobación:\n", "en": "{n} clip(s) waiting for approval:\n",
                       "pt": "{n} corte(s) esperando aprovação:\n"},
    "pendiente_linea": {
        "es": "  #{n}  nota {nota}  [{ini}–{fin}]  {titulo}\n        {porque}\n        {arq}\n",
        "en": "  #{n}  score {nota}  [{ini}–{fin}]  {titulo}\n        {porque}\n        {arq}\n",
        "pt": "  #{n}  nota {nota}  [{ini}–{fin}]  {titulo}\n        {porque}\n        {arq}\n"},
    "no_existe": {"es": "  #{n}: no existe", "en": "  #{n}: doesn't exist", "pt": "  #{n}: não existe"},
    "ya_estaba": {"es": "  #{n}: ya estaba {estado}", "en": "  #{n}: already {estado}", "pt": "  #{n}: já estava {estado}"},
    "aprobado": {"es": "  #{n} APROBADO -> {arq}", "en": "  #{n} APPROVED -> {arq}", "pt": "  #{n} APROVADO -> {arq}"},
    "rechazado": {"es": "  #{n} rechazado y borrado", "en": "  #{n} rejected and deleted",
                  "pt": "  #{n} recusado e apagado"},
    "estado_approved": {"es": "aprobado", "en": "approved", "pt": "aprovado"},
    "estado_rejected": {"es": "rechazado", "en": "rejected", "pt": "recusado"},
    "estado_pending": {"es": "pendiente", "en": "pending", "pt": "pendente"},
    "credito": {"es": "Clip del directo de {canal}: {url}", "en": "Clip from {canal}'s stream: {url}",
                "pt": "Corte da live de {canal}: {url}"},
    "el_streamer": {"es": "el streamer", "en": "the streamer", "pt": "o streamer"},

    # ------------------------------------------------------------ entorno
    "revisando": {"es": "Revisando lo que necesita el ordenador…\n", "en": "Checking what this computer needs…\n",
                  "pt": "Conferindo o que o computador precisa…\n"},
    "py_viejo": {"es": "  ✗ Python {v} es antiguo. Hace falta 3.10 o más nuevo.",
                 "en": "  ✗ Python {v} is too old. You need 3.10 or newer.",
                 "pt": "  ✗ Python {v} é antigo. Precisa do 3.10 ou mais novo."},
    "py_winget": {
        "es": "      Instálalo con:  winget install -e --id Python.Python.3.12 --scope user   (luego cierra y abre la terminal)",
        "en": "      Install it with:  winget install -e --id Python.Python.3.12 --scope user   (then reopen the terminal)",
        "pt": "      Instale com:  winget install -e --id Python.Python.3.12 --scope user   (depois feche e abra o terminal)"},
    "py_web": {"es": "      Descárgalo en https://www.python.org/downloads/ y abre el instalador.",
               "en": "      Download it from https://www.python.org/downloads/ and run the installer.",
               "pt": "      Baixe em https://www.python.org/downloads/ e abra o instalador."},
    "py_ok": {"es": "  ✓ Python {v}", "en": "  ✓ Python {v}", "pt": "  ✓ Python {v}"},
    "creando_entorno": {"es": "  … creando el entorno del clipper en {p}", "en": "  … creating the clipper environment in {p}",
                        "pt": "  … criando o ambiente do clipper em {p}"},
    "instalando": {"es": "  … instalando/actualizando: {lista}", "en": "  … installing/updating: {lista}",
                   "pt": "  … instalando/atualizando: {lista}"},
    "pip_fallo": {
        "es": "  ✗ no pude instalar los paquetes. Revisa internet y ejecuta 'clip.py instalar' de nuevo.",
        "en": "  ✗ couldn't install the packages. Check your internet and run 'clip.py install' again.",
        "pt": "  ✗ não consegui instalar os pacotes. Confira a internet e rode 'clip.py instalar' de novo."},
    "paquetes_ok": {"es": "  ✓ paquetes", "en": "  ✓ packages", "pt": "  ✓ pacotes"},
    "bajando_ffmpeg": {"es": "  … descargando ffmpeg (una sola vez)", "en": "  … downloading ffmpeg (only once)",
                       "pt": "  … baixando o ffmpeg (uma vez só)"},
    "bajando_yunet": {"es": "  … descargando el detector de caras (OpenCV YuNet)",
                      "en": "  … downloading the face detector (OpenCV YuNet)",
                      "pt": "  … baixando o detector de rosto (OpenCV YuNet)"},
    "yunet_ok": {"es": "  ✓ detector de caras", "en": "  ✓ face detector", "pt": "  ✓ detector de rosto"},
    "bajando_modelos": {
        "es": "  … descargando los modelos de escucha ({m}; una sola vez)",
        "en": "  … downloading the listening models ({m}; only once)",
        "pt": "  … baixando os modelos de escuta ({m}; uma vez só)"},
    "modelos_ok": {"es": "  ✓ modelos de escucha", "en": "  ✓ listening models", "pt": "  ✓ modelos de escuta"},
    "roto": {"es": "\n  ✗ no funciona: {lista}. Ejecuta 'clip.py instalar' de nuevo.",
             "en": "\n  ✗ not working: {lista}. Run 'clip.py install' again.",
             "pt": "\n  ✗ não está funcionando: {lista}. Rode 'clip.py instalar' de novo."},
    "prueba_ok": {"es": "  ✓ prueba: Streamlink, yt-dlp, ffmpeg y Whisper funcionando",
                  "en": "  ✓ test: Streamlink, yt-dlp, ffmpeg and Whisper working",
                  "pt": "  ✓ teste: Streamlink, yt-dlp, ffmpeg e Whisper funcionando"},
    "falta_config": {
        "es": "\nTODO INSTALADO. Falta elegir la carpeta y cuántos GB reservar: clip.py configurar --carpeta X --gb N",
        "en": "\nALL INSTALLED. Now choose the folder and how many GB to reserve: clip.py configure --folder X --gb N",
        "pt": "\nTUDO INSTALADO. Falta escolher a pasta e quantos GB reservar: clip.py configurar --pasta X --gb N"},
    "todo_listo": {"es": "\nTODO LISTO. Carpeta: {carpeta} | reservado: {gb} GB",
                   "en": "\nALL READY. Folder: {carpeta} | reserved: {gb} GB",
                   "pt": "\nTUDO PRONTO. Pasta: {carpeta} | reservado: {gb} GB"},
    "no_instalado": {"es": "El clipper todavía no está instalado. Ejecuta: clip.py instalar",
                     "en": "The clipper isn't installed yet. Run: clip.py install",
                     "pt": "O clipper ainda não foi instalado. Rode: clip.py instalar"},
    "act_luego": {"es": "  (hay un directo grabándose: dejo la actualización para después, para no molestar)",
                  "en": "  (a stream is being recorded: updating later so nothing is interrupted)",
                  "pt": "  (tem live sendo gravada agora: deixo pra atualizar depois, pra não atrapalhar)"},
    "buscando_act": {"es": "Buscando actualizaciones (Streamlink, yt-dlp, Whisper, ffmpeg)…",
                     "en": "Looking for updates (Streamlink, yt-dlp, Whisper, ffmpeg)…",
                     "pt": "Procurando atualizações (Streamlink, yt-dlp, Whisper, ffmpeg)…"},
    "act_rompio": {
        "es": "  ✗ después de actualizar, dejó de funcionar: {lista}. Volviendo a las versiones anteriores…",
        "en": "  ✗ after updating, this stopped working: {lista}. Rolling back to the previous versions…",
        "pt": "  ✗ depois de atualizar, parou de funcionar: {lista}. Voltando pras versões antigas…"},
    "act_volvi": {"es": "  ✓ volví a las versiones que funcionaban", "en": "  ✓ rolled back to the working versions",
                  "pt": "  ✓ voltei pras versões que funcionavam"},
    "act_sigue_roto": {"es": "  ✗ sigue roto: {lista}", "en": "  ✗ still broken: {lista}",
                       "pt": "  ✗ ainda quebrado: {lista}"},
    "act_hecho": {"es": "  ✓ actualizado: {lista}", "en": "  ✓ updated: {lista}", "pt": "  ✓ atualizado: {lista}"},
    "act_internas": {"es": "dependencias internas", "en": "internal dependencies", "pt": "dependências internas"},
    "act_al_dia": {"es": "  ✓ todo ya estaba en la última versión", "en": "  ✓ everything was already up to date",
                   "pt": "  ✓ tudo já estava na versão mais nova"},
    "cfg_carpeta": {"es": "Carpeta: {p}", "en": "Folder: {p}", "pt": "Pasta: {p}"},
    "cfg_reserva": {
        "es": "Reservado: {gb} GB | libre en el disco ahora: {libre:.0f} GB | ya usado por el clipper: {usado:.1f} GB",
        "en": "Reserved: {gb} GB | free on disk now: {libre:.0f} GB | already used by the clipper: {usado:.1f} GB",
        "pt": "Reservado: {gb} GB | livre no disco agora: {libre:.0f} GB | já usado pelo clipper: {usado:.1f} GB"},
    "cfg_poco": {"es": "ATENCIÓN: el disco solo tiene {libre:.0f} GB libres. Reduce la reserva o libera espacio.",
                 "en": "WARNING: the disk only has {libre:.0f} GB free. Lower the reservation or free up space.",
                 "pt": "ATENÇÃO: o disco só tem {libre:.0f} GB livres. Diminua a reserva ou libere espaço."},
    "cfg_horas": {
        "es": "Eso da para unas {h:.0f} h de grabación en 720p guardadas a la vez (la limpieza borra lo ya analizado).",
        "en": "That fits about {h:.0f} h of 720p recording at once (cleanup deletes what was already analyzed).",
        "pt": "Isso dá uns {h:.0f} h de gravação em 720p guardadas ao mesmo tempo (a limpeza apaga o que já foi analisado)."},
    "cfg_lengua": {"es": "Idioma del sistema: español", "en": "System language: English",
                   "pt": "Idioma do sistema: português"},
    "cfg_guardada": {"es": "Configuración guardada.", "en": "Settings saved.", "pt": "Configuração salva."},
    "ver_instalado": {"es": "Instalado: {v}", "en": "Installed: {v}", "pt": "Instalado: {v}"},
    "si": {"es": "sí", "en": "yes", "pt": "sim"},
    "no_instalar": {"es": "NO (ejecuta clip.py instalar)", "en": "NO (run clip.py install)",
                    "pt": "NÃO (rode clip.py instalar)"},
    "ver_versiones": {"es": "Versiones: {v}", "en": "Versions: {v}", "pt": "Versões: {v}"},
    "ver_ultima": {"es": "Última actualización: {v}", "en": "Last update: {v}", "pt": "Última atualização: {v}"},
    "ver_roto": {"es": "ROTO: {v}", "en": "BROKEN: {v}", "pt": "QUEBRADO: {v}"},
    "ver_config": {"es": "Configurado: {v} | carpeta {p} | {gb} GB reservados | idioma {l}",
                   "en": "Configured: {v} | folder {p} | {gb} GB reserved | language {l}",
                   "pt": "Configurado: {v} | pasta {p} | {gb} GB reservados | idioma {l}"},
    "no_configurar": {"es": "NO (ejecuta clip.py configurar)", "en": "NO (run clip.py configure)",
                      "pt": "NÃO (rode clip.py configurar)"},
    "pkg_python": {"es": "librerías de Python", "en": "Python libraries", "pt": "bibliotecas do Python"},
    "pkg_instalacion": {"es": "instalación de los paquetes", "en": "package installation",
                        "pt": "instalação dos pacotes"},

    # ------------------------------------------------------------ buscar
    "busca_nada": {
        "es": "No encontré directos de GTA 6 ahora. Manda el enlace directo del canal (twitch.tv/…, kick.com/…).",
        "en": "No GTA 6 streams live right now. Send the channel link directly (twitch.tv/…, kick.com/…).",
        "pt": "Não achei lives de GTA 6 ao vivo agora. Mande o link direto do canal (twitch.tv/…, kick.com/…)."},
    "busca_cab": {"es": "Directos de GTA 6 ahora mismo (los {n} más grandes):\n",
                  "en": "GTA 6 streams live right now (top {n}):\n",
                  "pt": "Lives de GTA 6 ao vivo agora (as {n} maiores):\n"},
    "busca_viendo": {"es": "{n} viendo", "en": "{n} watching", "pt": "{n} assistindo"},

    # ------------------------------------------------------------ vigía
    "no_lei_enlace": {"es": "No pude leer ese enlace:\n{error}", "en": "Couldn't read that link:\n{error}",
                      "pt": "Não consegui ler esse link:\n{error}"},
    "es_bloqueo_sitio": {
        "es": "NO SE PUEDE GRABAR: {motivo}. Es un bloqueo del sitio, no un error del clipper.",
        "en": "CAN'T RECORD: {motivo}. That's a restriction of the site, not a clipper error.",
        "pt": "NÃO DÁ PRA GRAVAR: {motivo}. Isso é trava do site, não erro do clipper."},
    "vigilando": {"es": "VIGILANDO {canal} | {titulo} | {plataforma} | modo {modo}",
                  "en": "WATCHING {canal} | {titulo} | {plataforma} | mode {modo}",
                  "pt": "VIGIANDO {canal} | {titulo} | {plataforma} | modo {modo}"},
    "carpeta_log": {"es": "carpeta: {p}", "en": "folder: {p}", "pt": "pasta: {p}"},
    "pidieron_parar": {"es": "pidieron parar: cerrando la grabación…", "en": "stop requested: closing the recording…",
                       "pt": "pediram pra parar: fechando a gravação…"},
    "directo_terminado": {"es": "DIRECTO TERMINADO: último bloque listo. Vigía apagado.",
                          "en": "STREAM ENDED: last block ready. Watcher off.",
                          "pt": "LIVE ENCERRADA: último bloco pronto. Vigia desligado."},
    "limpieza": {"es": "limpieza: borré {n} trozo(s) antiguo(s) de la grabación; usando {uso:.1f} de {cota} GB",
                 "en": "cleanup: deleted {n} old recording chunk(s); using {uso:.1f} of {cota} GB",
                 "pt": "limpeza: apaguei {n} pedaço(s) antigo(s) da gravação; usando {uso:.1f} de {cota} GB"},
    "espacio_aviso": {
        "es": "ESPACIO: borré grabación aún no analizada ({arq}). La IA va atrasada o los GB reservados son pocos.",
        "en": "SPACE: deleted recording not yet analyzed ({arq}). The AI is behind or too few GB are reserved.",
        "pt": "ESPAÇO: apaguei gravação ainda não analisada ({arq}). A IA está atrasada ou os GB reservados são poucos."},

    # ------------------------------------------------------------ clip.py
    "antes_config": {"es": "Antes, elige la carpeta y los GB: clip.py configurar --carpeta X --gb N",
                     "en": "First choose the folder and GB: clip.py configure --folder X --gb N",
                     "pt": "Antes, escolha a pasta e os GB: clip.py configurar --pasta X --gb N"},
    "vigia_encendido": {"es": "Vigía encendido para {enlace}\n  registro: {arq}",
                        "en": "Watcher started for {enlace}\n  log: {arq}",
                        "pt": "Vigia ligado para {enlace}\n  registro: {arq}"},
    "esperando_primeros": {
        "es": "\nEsperando los primeros minutos de grabación… (el primer bloque sale tras {min} min de directo)",
        "en": "\nWaiting for the first minutes of recording… (the first block comes after {min} min of stream)",
        "pt": "\nAguardando os primeiros minutos de gravação… (o primeiro bloco sai depois de {min} min de live)"},
    "vigia_fallo": {
        "es": "EL VIGÍA SE CAYÓ al vigilar {enlace}:\n{error}\nPrueba 'clip.py actualizar' y vuelve a ejecutar 'clip.py vigilar ENLACE'.",
        "en": "THE WATCHER CRASHED while watching {enlace}:\n{error}\nTry 'clip.py update' and run 'clip.py watch LINK' again.",
        "pt": "O VIGIA CAIU ao vigiar {enlace}:\n{error}\nTente 'clip.py atualizar' e rode 'clip.py vigiar LINK' de novo."},
    "bloque_para_leer": {"es": "BLOQUE LISTO PARA LEER:", "en": "BLOCK READY TO READ:", "pt": "BLOCO PRONTO PRA LER:"},
    "escribe_en": {"es": "    -> escribe {arq}", "en": "    -> write {arq}", "pt": "    -> escreva {arq}"},
    "falta_cortar": {"es": "FALTA CORTAR: ejecuta 'clip.py cortar {nombre}'",
                     "en": "NEEDS CUTTING: run 'clip.py cut {nombre}'",
                     "pt": "FALTA CORTAR: rode 'clip.py cortar {nombre}'"},
    "ninguno_vigilado": {
        "es": "NINGÚN DIRECTO VIGILADO: todos terminaron y ya fueron analizados.",
        "en": "NO STREAMS BEING WATCHED: all ended and were already analyzed.",
        "pt": "NENHUMA LIVE SENDO VIGIADA: todas encerraram e já foram analisadas."},
    "aun_no": {"es": "AÚN NO HAY BLOQUE NUEVO. Ejecuta 'clip.py esperar' otra vez.",
               "en": "NO NEW BLOCK YET. Run 'clip.py wait' again.",
               "pt": "AINDA NÃO TEM BLOCO NOVO. Rode 'clip.py esperar' de novo."},
    "pedi_parar": {"es": "Pedí parar: {nombre} (cierra en hasta 1 min; lo ya grabado será el último bloque)",
                   "en": "Stop requested: {nombre} (closes within 1 min; what was recorded becomes the last block)",
                   "pt": "Pedi pra parar: {nombre} (fecha em até 1 min; o que já foi gravado vira o último bloco)"},
    "st_grabando": {"es": "GRABANDO", "en": "RECORDING", "pt": "GRAVANDO"},
    "st_esperando": {"es": "esperando el directo (offline/reconectando)", "en": "waiting for the stream (offline/reconnecting)",
                     "pt": "esperando a live (offline/reconectando)"},
    "st_terminado": {"es": "terminado", "en": "ended", "pt": "encerrada"},
    "st_parado": {"es": "vigía parado", "en": "watcher stopped", "pt": "vigia parado"},
    "st_proximo": {"es": " | próximo bloque en ~{min} min", "en": " | next block in ~{min} min",
                   "pt": " | próximo bloco em ~{min} min"},
    "st_sin_chat": {"es": " (sin chat)", "en": " (no chat)", "pt": " (sem chat)"},
    "st_linea": {
        "es": "  escuchado hasta {hasta} | cola de escucha {cola} trozo(s) | chat: {msgs} msgs{sinchat}{prox}\n"
              "  bloques leídos por la IA: {leidos}/{bloques} | clips: {pend} pendientes, {aprob} aprobados | "
              "disco: {uso}/{cota} GB",
        "en": "  listened up to {hasta} | listening queue {cola} chunk(s) | chat: {msgs} msgs{sinchat}{prox}\n"
              "  blocks read by the AI: {leidos}/{bloques} | clips: {pend} pending, {aprob} approved | "
              "disk: {uso}/{cota} GB",
        "pt": "  escutado até {hasta} | fila de escuta {cola} pedaço(s) | chat: {msgs} msgs{sinchat}{prox}\n"
              "  blocos lidos pela IA: {leidos}/{bloques} | cortes: {pend} pendentes, {aprob} aprovados | "
              "disco: {uso}/{cota} GB"},
    "st_error": {"es": "  ERROR: {e}", "en": "  ERROR: {e}", "pt": "  ERRO: {e}"},
    "st_aviso": {"es": "  AVISO: {e}", "en": "  WARNING: {e}", "pt": "  AVISO: {e}"},
    "st_clips": {"es": "\nClips: {p}", "en": "\nClips: {p}", "pt": "\nCortes: {p}"},
}
