---
name: clipper-live
description: Clipper Live — mira directos EN VIVO (Twitch, Kick o YouTube) y va separando clips verticales mientras el streamer juega, con la cámara arriba, el juego abajo, título gancho, subtítulos palabra por palabra y texto del post. Graba con Streamlink, escucha la voz, mide los gritos y lee el chat; cada 30 min la IA elige los momentos y los clips van a una cola de aprobación. Úsala cuando la persona diga "instala el clipper live", "vigila este directo", "corta este directo", "busca directos de GTA 6", "aprueba el clip 3" (o lo mismo en inglés o portugués: "watch this stream", "vigia essa live"), o pegue un enlace de directo pidiendo clips.
---

# Clipper Live

Tú (la IA) haces una sola parte: **leer lo que se dice en el directo y elegir los momentos**. Grabar, escuchar,
leer el chat, encontrar la cámara, montar el vídeo y los subtítulos y borrar archivos viejos es trabajo de los
scripts de esta carpeta, en el ordenador de la persona.

## Idioma

El sistema viene en **español**. También funciona en **inglés** y **portugués**.
- Habla con la persona en el idioma configurado (`clip.py verificar` lo muestra). Si la persona te escribe en
  otro idioma, cámbialo sin preguntar: `clip.py configurar --lengua en` (o `pt`, o `es`).
- Los comandos también aceptan nombres en inglés y portugués (`watch`/`vigiar`, `approve`/`aprovar`…), pero usa
  los de español que aparecen aquí.
- La persona no es programadora: explica qué está pasando en una frase, sin jerga.

## Cómo ejecutar los comandos

Siempre `clip.py`, dentro de la carpeta `scripts/` de esta skill:

- Windows: `python "<carpeta de la skill>\scripts\clip.py" COMANDO`
- Mac / Linux: `python3 "<carpeta de la skill>/scripts/clip.py" COMANDO`

Después de `instalar`, `clip.py` usa solo su propio entorno (`~/.clipper-live/ambiente`).

## 0. "Instala el clipper live" / "actualízalo"

Ejecuta **un solo comando**, con tiempo límite largo (hasta 30 min). Descarga la skill, encuentra Python y ejecuta
`clip.py instalar`:

- Windows (PowerShell): `irm https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.ps1 | iex`
- Mac/Linux: `curl -fsSL https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.sh | bash`

Para instalar en otro idioma, pon antes la variable `CLIPPER_LANG` (`$env:CLIPPER_LANG="en"; irm … | iex` en
Windows, `CLIPPER_LANG=en bash` en vez de `bash` en Mac/Linux).

Si falta Python (hace falta 3.10+): en Windows el comando ya lo instala con winget (pide cerrar y abrir la
terminal/app y ejecuta otra vez); en Mac abre la web de Python (botón amarillo "Download", instalar, ejecutar otra vez).

**Después de instalar, pregunta dos cosas** (obligatorio antes del primer directo):
1. "¿En qué carpeta guardo las grabaciones y los clips?" (sugiere `<carpeta del usuario>\clipper-live`; un disco
   externo o con espacio es mejor)
2. "¿Cuántos GB puedo usar?" Explica: cada hora de directo en 720p ocupa unos 2 GB mientras no se analiza; la
   limpieza borra sola lo que ya se convirtió en clip. **Recomienda 50 GB** (mínimo 15).

Luego ejecuta `clip.py configurar --carpeta "CARPETA" --gb N` y muestra lo que responde (espacio libre, etc.).

La actualización es automática: cada `vigilar` revisa si pasaron más de 12 h desde la última y actualiza
Streamlink, yt-dlp, Whisper y ffmpeg; si algo se rompe, vuelve solo a la versión anterior. `clip.py actualizar`
lo fuerza ahora.

## 1. "Busca directos de GTA 6"
`clip.py buscar` (opciones: `--cuantos 10`, `--idioma es`). Muestra la lista y pregunta cuál vigilar.

## 2. "Vigila este directo: ENLACE" — el ciclo en vivo

### 2.1 Encender el vigía
`clip.py vigilar ENLACE` (acepta varios enlaces). Enciende un proceso **en segundo plano** que sigue funcionando
aunque se cierre la terminal: graba el directo en trozos de 5 min, escucha la voz, mide los gritos y lee el chat.
Si el directo todavía no empezó, espera hasta 8 h; si se cae, reconecta; 20 min sin señal = directo terminado.

Di: "Listo, estoy grabando el directo de FULANO. Cada 30 minutos leo lo que pasó y separo los clips. Puedes dejar
el ordenador encendido; los clips van apareciendo para que los apruebes."

### 2.2 El ciclo (repite hasta que termine el directo)
1. Ejecuta `clip.py esperar` (tarda hasta 9 min; ejecútalo otra vez mientras diga "AÚN NO HAY BLOQUE NUEVO").
   No comentes cada espera: avisa solo cuando pase algo.
2. Cuando diga **BLOQUE LISTO PARA LEER**, lee el `bloque_NN.txt` indicado y escribe el `momentos/bloque_NN.json`
   (reglas abajo). Escribe el archivo **siempre**, aunque esté vacío (`[]`).
3. Ejecuta `clip.py cortar`. Monta los clips y muestra la cola de pendientes.
4. Muestra a la persona los clips nuevos: número, título, nota, por qué y la ruta del archivo. Pregunta cuáles
   aprobar. **No detengas el ciclo esperando respuesta**: vuelve al paso 1. Cuando la persona responda, ejecuta
   `clip.py aprobar 3 5` / `clip.py rechazar 4` y sigue.
5. Si `esperar` dice **FALTA CORTAR**, ejecuta `clip.py cortar`. Si dice **NINGÚN DIRECTO VIGILADO**, el directo
   terminó y todo fue analizado: haz el resumen final (cuántos clips, cuántos aprobados, dónde están).

Si la persona quiere parar: `clip.py detener` (o `clip.py detener NOMBRE`). `clip.py estado` lo muestra todo en
cualquier momento.

### 2.3 Cómo elegir los momentos (esta es tu parte)

Cada línea del bloque es `[hh:mm:ss] frase`, en **tiempo de grabación**. Las marcas ayudan (en inglés salen como
`LOUD` y `LAUGH/HYPE`; en portugués, `ALTO` y `RISADA/HYPE`):
- `[ALTO +12dB]` — el streamer habló mucho más alto de lo normal (grito, ataque de rabia, susto).
- `[CHAT 3.1x]` — el chat fue 3 veces más rápido de lo normal ahí: algo pasó.
- `[RISA/HYPE]` — en el pico, la mayoría del chat era JAJAJA, KEKW, CLIP, ????.
- Al final del bloque, **PICOS DEL CHAT** muestra lo que la gente escribió en cada pico. Úsalo para entender la
  reacción (a veces el momento es visual y el streamer ni habla: si el chat explotó con "CLIP"/"JAJAJA", mira la
  frase de alrededor).

Una marca sola no es un momento. Confírmalo con lo que se dice.

**Lo que vale un clip** (lo que la gente comparte):
- primera reacción a algo del juego (ver el mapa, un personaje, un gráfico, una escena por primera vez)
- descubrimiento absurdo o detalle que nadie había visto
- ataque de rabia, grito, susto
- fallo gracioso, bug, muerte ridícula
- opinión fuerte o polémica ("esto está peor que el GTA 5")
- historia o chiste que se cierra solo

**Sé estricto. Descarta:**
- lo que necesita contexto previo para entenderse
- lo que empieza con relleno ("eh…", "entonces…", "o sea", "volviendo…", "uh, so yeah", "é…", "tipo assim")
- lectura de donaciones, publicidad, charla sobre el propio directo, pausas, pantallas de carga
- frases cortadas o que la transcripción no deja entender

**Nota de 0 a 100.** 90+ = cualquiera deja de hacer scroll. 70–89 = bueno. Por debajo de 60, ni lo escribas.
Solo los momentos con nota 70+ se convierten en clip (máximo 3 por bloque). Normalmente un bloque de 30 min tiene
de 0 a 4 buenos: no inventes para rellenar.

**Duración:** de 20 a 60 segundos. Empieza 1–2 s antes de la frase o el grito que engancha (nunca en mitad de una
palabra) y termina justo después de la reacción/conclusión.

Formato de `momentos/bloque_NN.json`:

```json
[
  {
    "inicio": "01:12:03",
    "fim": "01:12:41",
    "nota": 88,
    "tipo": "primera reacción",
    "titulo": "NO SE CREYÓ EL TAMAÑO DEL MAPA",
    "porque": "grita al ver el mapa entero; el chat explotó (4x, 80% hype); se cierra solo",
    "post": "El tamaño del mapa de GTA 6 lo dejó sin palabras 😳 #gta6 #gtavi #gta #clips #streamer"
  }
]
```

(Las claves `inicio`, `fim`, `nota`, `tipo`, `titulo`, `porque`, `post` se escriben exactamente así.)

- `titulo`: el gancho escrito en el vídeo. Corto (hasta ~45 letras), MAYÚSCULAS, **en el idioma del directo**,
  sin spoiler del final. Usa el nombre/apodo del streamer cuando ayude ("IBAI NO SE LO CREYÓ…").
- `post`: texto del post en el idioma del directo, 1–2 frases + 4 a 6 hashtags (siempre `#gta6`).

## Dónde está cada cosa
- `CARPETA/cortes/pendientes/` — clips esperando aprobación (`007_canal.mp4` + `.txt` con el texto y el crédito)
- `CARPETA/cortes/aprobados/NOMBRE-DEL-DIRECTO/` — aprobados (nunca se borran solos)
- `CARPETA/lives/NOMBRE-DEL-DIRECTO/` — grabación en trozos, escucha, chat, bloques y momentos

## Espacio en disco
La limpieza corre cada minuto: borra la grabación ya leída y cortada (guarda 1 h de margen); si el uso pasa del 85%
de los GB reservados, borra antes; si pasa del 95%, borra incluso grabación todavía no leída y avisa en `estado`
(señal de que la IA va atrasada o de que se reservó poco espacio). Rechazar un clip lo borra al momento.
Los aprobados se quedan: recuerda a la persona que saque de la carpeta los que ya publicó.

## Problemas comunes
- `vigilar` o `esperar` dicen **EL VIGÍA SE CAYÓ** → muestra el motivo a la persona en una frase. Si el enlace
  está mal o el directo no existe, pide otro enlace; si no, ejecuta `clip.py actualizar` y `clip.py vigilar ENLACE`
  otra vez (sigue donde quedó).
- `estado` muestra **ERROR: restricción de edad / solo para miembros** → es un bloqueo del sitio, no del clipper.
  Dilo con esas palabras y ofrece otro directo.
- **(sin chat)** en el estado → la plataforma bloqueó la lectura del chat. El clipper sigue con voz y volumen; los
  clips siguen saliendo.
- Error de descarga/grabación → `clip.py actualizar` y `clip.py vigilar ENLACE` otra vez (sigue donde quedó).
- Elegiste un momento malo → `clip.py rechazar N`.
- Ajustes: `clip.py configurar --bloque-min 20` (analiza cada 20 min), `--nota-minima 80`, `--max-por-bloque 5`,
  `--calidad 1080p60,best`, `--idioma-directo es`, `--lengua en`.

## Respeto a los streamers
Corta solo a streamers que permiten clips. El `.txt` de cada clip trae el crédito con el enlace del directo:
mantenlo en la publicación.
