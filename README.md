**Español** | [English](README.en.md) | [Português](README.pt.md)

# Clipper Live

Una skill gratis para Claude Code que **mira directos EN VIVO** y va separando clips verticales mientras el
streamer juega. Hecha para el lanzamiento de GTA 6, pero funciona con cualquier directo.

Mandas el enlace del directo (Twitch, Kick o YouTube), dejas el ordenador encendido y cada 30 minutos recibes:

- clips verticales (1080×1920): cámara del streamer arriba, juego abajo
- título gancho y subtítulos palabra por palabra
- un `.txt` con el texto del post, los hashtags y el crédito del directo

Tú apruebas o rechazas cada clip. El aprobado va a una carpeta; el rechazado se borra.

El sistema viene en **español** y también funciona en **inglés** y **portugués**.

📖 **[Guía paso a paso](docs/GUIA.md)**: instalación, uso, aprobación de clips y solución de problemas.

## Cómo funciona

```
 directo ──► Streamlink graba en trozos de 5 min ──► Whisper escribe lo que se dice + mide los gritos
    └──────► lector de chat (Twitch / YouTube / Kick) ──► marca dónde la gente se emocionó
                              │
          cada 30 min: bloque de texto con [ALTO +12dB] [CHAT 3x] [RISA/HYPE]
                              │
                Claude lo lee, pone nota y elige los momentos
                              │
     clip montado (cámara + juego + título + subtítulos) ──► cola de aprobación
                              │
     limpieza: borra la grabación que ya se convirtió en clip, respetando los GB que reservaste
```

- **Grabación en vivo con [Streamlink](https://github.com/streamlink/streamlink)**: salta los anuncios de Twitch,
  reconecta si el directo se cae y espera a que empiece (hasta 8 h).
- **Escucha en tu ordenador** (faster-whisper). Usa la tarjeta gráfica NVIDIA si hay.
- **Chat en vivo**: Twitch (sin cuenta), YouTube y Kick. Si una plataforma bloquea el chat, sigue con la voz y el
  volumen.
- **Actualización automática y segura**: Streamlink, yt-dlp, Whisper y ffmpeg se actualizan solos cada 12 h. Si
  una versión nueva rompe algo, vuelve a la anterior.
- También corta vídeos que ya terminaron (VOD): basta con mandar el enlace.

## Instalación

Necesitas **Claude Code**: la app de https://claude.com/download, en la pestaña **Code**. También funciona gratis
con Ollama, pero las elecciones salen peores.

Pega en Claude Code:

> instala el clipper live: https://github.com/nexcorsair-create/Clipper-Live

O ejecútalo directamente (sirve también para actualizar):

- **Windows (PowerShell):** `irm https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.ps1 | iex`
- **Mac/Linux:** `curl -fsSL https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.sh | bash`

Revisa Python, instala Streamlink, yt-dlp, ffmpeg y Whisper, prueba todo y avisa cuando esté listo. Después Claude
pregunta **en qué carpeta guardar** y **cuántos GB reservar**. Recomiendo 50 GB: una hora de directo en 720p
ocupa unos 2 GB hasta que se analiza.

### Cambiar el idioma

- Al instalar: pon `$env:CLIPPER_LANG="en";` (o `"pt"`) antes del comando de Windows, o cambia `| bash` por
  `| CLIPPER_LANG=en bash` en Mac/Linux.
- Después: dile a Claude "cambia el idioma a inglés", o ejecuta `clip.py configurar --lengua en` (`es`, `en`, `pt`).

## Uso

- "vigila este directo: https://twitch.tv/fulano"
- "busca los directos de GTA 6 más grandes ahora"
- "aprueba el 3 y el 5" / "rechaza el 4"
- "¿cómo va el directo?" / "deja de vigilar"

Los clips quedan en `TU-CARPETA/cortes/pendientes` y, una vez aprobados, en `TU-CARPETA/cortes/aprobados`.

**Consejo:** cuando Claude pida permiso para ejecutar `clip.py`, elige "permitir siempre". Así trabaja solo durante
todo el directo.

## Requisitos

- Windows, Mac o Linux
- Python 3.10 o más nuevo (el instalador lo resuelve en Windows)
- unos 3 GB para el programa y los modelos, más los GB reservados para las grabaciones
- internet estable (graba el directo mientras tú lo ves)

## Límites

- Los directos solo para miembros o con restricción de edad no se graban (piden iniciar sesión).
- El sistema decide por la voz, el volumen y el chat; no "ve" la imagen. Un momento solo visual entra si el chat
  explota.
- El clip sale entre 30 y 40 min después del momento (es el ciclo de análisis). Se puede cambiar: "analiza cada 20 min".
- No publica solo: tú publicas los aprobados.

## Respeta a los streamers

Corta solo a quien permite clips y mantén el crédito que viene en el `.txt` de cada clip.

## Créditos

Idea del flujo (escuchar el directo, que la IA ponga nota por bloques, cámara arriba y juego abajo) inspirada en
[skill-clips](https://github.com/davixavier-coder/skill-clips) de Davi Xavier. Grabación en vivo con
[Streamlink](https://github.com/streamlink/streamlink); descargas con [yt-dlp](https://github.com/yt-dlp/yt-dlp);
escucha con [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
