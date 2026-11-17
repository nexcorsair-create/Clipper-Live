**Español** | [English](GUIDE.en.md) | [Português](GUIA.pt.md)

# Clipper Live — Guía paso a paso

Esta guía explica, sin tecnicismos, cómo instalar Clipper Live y usarlo para sacar clips de directos mientras
ocurren. No hace falta saber programar: tú hablas con Claude y él se encarga del resto.

---

## 1. Qué hace Clipper Live

Clipper Live mira un directo de Twitch, Kick o YouTube **mientras está en vivo** y, cada 30 minutos, te entrega
los mejores momentos ya cortados en vídeo vertical, listos para TikTok, Reels o Shorts.

Cada clip trae:

- la **cámara del streamer arriba** y el **juego abajo** (formato 1080×1920)
- un **título gancho** escrito en el vídeo
- **subtítulos palabra por palabra**
- un archivo `.txt` con el **texto del post**, los **hashtags** y el **crédito** del directo

Tú solo **apruebas** o **rechazas** cada clip. Lo aprobado se guarda; lo rechazado se borra.

### Cómo decide qué es un buen momento

1. **Graba** el directo en trozos de 5 minutos.
2. **Escucha** todo lo que dice el streamer y lo convierte en texto, en tu propio ordenador.
3. **Mide los gritos**: marca cuándo el streamer habló mucho más alto de lo normal.
4. **Lee el chat**: marca cuándo la gente empezó a escribir mucho más rápido (o a mandar "JAJAJA", "CLIP"…).
5. Cada 30 minutos, **Claude lee todo eso**, pone una nota de 0 a 100 a cada momento y elige los mejores.
6. El sistema **monta los clips** y los pone en la cola para que los apruebes.

---

## 2. Lo que necesitas

| Necesitas | Detalle |
|---|---|
| Ordenador | Windows, Mac o Linux. Con 16 GB de RAM va cómodo; con tarjeta NVIDIA, mejor. |
| Claude Code | La app de Claude (https://claude.com/download), pestaña **Code**. Plan Pro o superior. |
| Espacio en disco | Unos **3 GB** para el programa + el espacio que reserves para grabaciones (recomendado **50 GB**). |
| Internet | Estable. El sistema graba el directo mientras tú lo ves. |
| Python | 3.10 o más nuevo. En Windows el instalador lo pone solo. En Mac, la guía te dice qué hacer. |

> **¿Y gratis?** También funciona con Ollama (IA local, sin pagar), pero las elecciones de momentos salen peores
> y necesitas un ordenador potente (16 GB de RAM o más).

---

## 3. Instalación (una sola vez)

### Paso 1 — Abre Claude Code

Abre la app de Claude, entra en la pestaña **Code** y elige una carpeta cualquiera para trabajar (por ejemplo,
una carpeta nueva llamada `clips`).

### Paso 2 — Pide la instalación

Escribe en el chat:

> instala el clipper live: https://github.com/nexcorsair-create/Clipper-Live

Claude ejecutará el instalador. Tarda entre 5 y 15 minutos la primera vez, porque descarga:

- **Streamlink** (graba el directo)
- **yt-dlp** (descarga vídeos y el chat de YouTube)
- **ffmpeg** (monta los vídeos)
- **Whisper** (convierte la voz en texto)
- el detector de caras (encuentra la cámara del streamer)

Al final verás **TODO INSTALADO**.

> **Si falta Python:** en Windows el instalador lo instala solo y te pide cerrar y abrir la app de Claude; luego
> vuelve a pedir la instalación. En Mac se abre la web de Python: pulsa **Download Python**, instálalo y vuelve a
> pedir la instalación.

> **Instalación manual** (si prefieres no pedírselo a Claude), en PowerShell de Windows:
> `irm https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.ps1 | iex`
> En Mac/Linux, en la Terminal:
> `curl -fsSL https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.sh | bash`

### Paso 3 — Elige la carpeta y el espacio

Claude te hará dos preguntas:

1. **¿En qué carpeta guardo las grabaciones y los clips?**
   Lo normal es `C:\Users\TU-USUARIO\clipper-live` (Windows) o `~/clipper-live` (Mac). Si tienes un disco externo
   con espacio, mejor todavía.
2. **¿Cuántos GB puedo usar?**
   Cada hora de directo en 720p ocupa unos 2 GB mientras no se analiza. La limpieza borra sola lo que ya se
   convirtió en clip. **Recomendado: 50 GB** (mínimo 15).

Listo: ya puedes vigilar directos.

### Paso 4 — Permisos (importante)

La primera vez que Claude ejecute el programa, la app te preguntará si le das permiso. Elige **"permitir siempre"**
para `clip.py`. Así Claude puede trabajar solo durante horas sin pedirte confirmación a cada rato.

---

## 4. Vigilar un directo

### Paso 1 — Pasa el enlace

Escribe en Claude:

> vigila este directo: https://www.twitch.tv/NOMBRE-DEL-CANAL

Sirven enlaces de **Twitch** (`twitch.tv/canal`), **Kick** (`kick.com/canal`) y **YouTube** (el enlace del directo o
`youtube.com/@canal/live`).

¿No sabes a quién vigilar? Pide:

> busca los directos de GTA 6 más grandes ahora

Claude te muestra una lista con cuántas personas están viendo cada uno, y eliges.

### Paso 2 — Deja el ordenador encendido

A partir de aquí todo es automático:

- Si el directo **todavía no empezó**, el sistema espera (hasta 8 horas).
- Si el directo **se cae**, reconecta solo.
- Si pasan **20 minutos sin señal**, considera que el directo terminó.
- El grabador sigue funcionando aunque cierres la ventana de la terminal.

**No apagues el ordenador ni lo dejes en suspensión** mientras vigila.

### Paso 3 — Recibe y aprueba los clips

Cada 30 minutos de directo, Claude te muestra los clips nuevos, por ejemplo:

```
#3  nota 88  [01:12:03–01:12:41]  NO SE CREYÓ EL TAMAÑO DEL MAPA
     grita al ver el mapa entero; el chat explotó; se cierra solo
     C:\Users\...\clipper-live\cortes\pendientes\003_canal.mp4
```

Abre el vídeo, míralo y responde:

> aprueba el 3 y el 5

> rechaza el 4

- **Aprobado** → se mueve a `cortes/aprobados/`.
- **Rechazado** → se borra en el momento.
- Si no respondes, el clip se queda esperando en `cortes/pendientes/` y Claude sigue trabajando.

### Paso 4 — Publica

En la carpeta `cortes/aprobados/NOMBRE-DEL-DIRECTO/` cada clip tiene su `.mp4` y su `.txt`. Copia el texto del
`.txt` como descripción del post: ya trae los hashtags y el crédito al streamer.

### Paso 5 — Termina

Cuando el directo acaba, Claude te hace un resumen (cuántos clips salieron, cuántos aprobaste y dónde están).
Si quieres parar antes:

> deja de vigilar

---

## 5. Frases útiles

| Quieres… | Escribe |
|---|---|
| Ver cómo va todo | "¿cómo va el directo?" |
| Ver los clips que faltan por aprobar | "¿qué clips hay pendientes?" |
| Vigilar varios directos a la vez | "vigila estos directos: ENLACE1 ENLACE2" |
| Análisis más frecuente | "analiza cada 20 minutos" |
| Ser más exigente | "solo clips con nota 80 o más" |
| Más clips por bloque | "hasta 5 clips por bloque" |
| Mejor calidad de vídeo | "graba en 1080p" (ocupa más espacio) |
| Cambiar el idioma | "cambia el idioma a inglés" / "…a portugués" |
| Forzar la actualización | "actualiza el clipper" |
| Cortar un vídeo que ya terminó | "corta este vídeo: ENLACE" |

---

## 6. Dónde está cada cosa

```
clipper-live/                       ← la carpeta que elegiste
├── cortes/
│   ├── pendientes/                 ← clips esperando tu aprobación
│   └── aprobados/
│       └── canal-2026-11-19/       ← clips aprobados de cada directo (.mp4 + .txt)
└── lives/
    └── canal-2026-11-19/           ← grabación, texto, chat y bloques (se limpia sola)
```

El programa en sí se instala en `~/.clipper-live` (no hace falta tocarlo).

---

## 7. Espacio en disco y limpieza

Clipper Live respeta los GB que reservaste:

- La grabación que **ya se analizó y cortó** se borra una hora después.
- Si el uso pasa del **85%** de lo reservado, borra antes.
- Si pasa del **95%**, borra incluso grabación todavía no analizada y te avisa (señal de que hay que reservar más
  espacio).
- Los clips **rechazados** se borran al momento.
- Los clips **aprobados nunca se borran solos**: cuando ya los hayas publicado, sácalos de la carpeta.

---

## 8. Actualizaciones

No tienes que hacer nada. Cada vez que empiezas a vigilar un directo, si pasaron más de 12 horas desde la última
vez, el sistema actualiza Streamlink, yt-dlp, Whisper y ffmpeg. Después **prueba que todo funciona**; si una
versión nueva rompió algo, vuelve sola a la anterior.

Nunca actualiza mientras hay un directo grabándose.

Para actualizar Clipper Live en sí (cuando salga una versión nueva en GitHub), pide:

> actualiza la skill del clipper live

---

## 9. Problemas frecuentes

| Ves… | Qué significa | Qué hacer |
|---|---|---|
| "restricción de edad" o "solo para miembros" | El sitio pide iniciar sesión para ver ese directo. | Elige otro directo. |
| "(sin chat)" en el estado | La plataforma bloqueó la lectura del chat. | Nada: los clips siguen saliendo con la voz y el volumen. |
| "EL VIGÍA SE CAYÓ" | Algo falló al empezar (enlace incorrecto, sitio caído…). | Revisa el enlace. Si está bien, pide "actualiza el clipper" y vuelve a vigilar. |
| "ESPACIO: borré grabación aún no analizada" | Reservaste poco espacio o Claude va atrasado. | Reserva más GB: "usa 80 GB". |
| El directo está en vivo pero no graba | Puede ser un cambio en la plataforma. | Pide "actualiza el clipper" y vuelve a vigilar. |
| Un clip salió mal | La IA eligió un mal momento. | "rechaza el N". |

---

## 10. Límites (lo que no hace)

- No graba directos **solo para miembros** o con **restricción de edad**.
- Decide por la **voz, el volumen y el chat**; no "ve" la imagen. Un momento solo visual entra si el chat explota.
- El clip sale **entre 30 y 40 minutos** después del momento (es el ciclo de análisis).
- **No publica** en redes: tú publicas los aprobados.

---

## 11. Respeta a los streamers

Corta solo a streamers que permiten clips (muchos tienen canal oficial de clips o lo autorizan). Mantén siempre
el crédito que viene en el `.txt` de cada clip.
