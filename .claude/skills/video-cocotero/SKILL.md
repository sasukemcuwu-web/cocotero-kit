---
name: video-cocotero
description: Hace un video corto vertical (9:16) de un producto de Cocotero de punta a punta - guion por etapa del embudo, tomas con el estudio Jestive, voz, montaje con subtítulos y cierre con logo. Úsala cuando pidan un video, un reel, un TikTok o "los 3 videos" de un producto.
---

# Video de Cocotero

Lee antes: `CLAUDE.md`, `marca/embudo.md`, `marca/productos.md`, `marca/tono.md`.

## 1. Guion (plantillas/guion-video.md)
- Elige la etapa (TOFU, MOFU o BOFU) o haz las tres con las mismas 3 tomas.
- Copia la plantilla a `proyectos/<producto>/guion-<etapa>.md` y llénala: gancho de 0–2 s, tomas, voz (3–4 frases cortas),
  rótulos de 2–5 palabras y cierre. Nada inventado; lo no confirmado va como `[POR CONFIRMAR]`.

## 2. Tomas (plantillas/prompt-toma.md)
- Mira `mi_cupo`. Una toma corta de 4 o 6 s gasta "video corto" (5 al día); 8 o 10 s gasta "video largo" (3 al día).
- `generar_video` con `aspecto: "9:16"`. Escribe el prompt en inglés con la plantilla: una acción, un plano, sin texto,
  sin cortes, el producto descrito como es en la foto real.
- Lanza las tomas y, mientras se generan, haz la voz. Consulta con `estado_video`; al completarse descarga cada una con su
  `url_descarga` a `proyectos/<producto>/tomas/` (por ejemplo con `curl -L -o toma-a.mp4 "<url>"`).
- Si una toma sale con texto, cortes raros o un producto distinto, avisa y propón un prompt corregido (un reintento).

## 3. Voz
- `generar_voz` **una vez por frase** (una por toma) más la frase de cierre; voz por defecto `lola` (si el equipo elige
  otra, úsala siempre). Descarga a `proyectos/<producto>/voz/f1.mp3`, `f2.mp3`, `f3.mp3`, `cierre.mp3`.
- Las mismas frases sirven para TOFU/MOFU/BOFU del mismo producto: no las generes otra vez.

## 4. Edición (herramientas/montar.py, criterio en marca/edicion.md)
- Copia `plantillas/montaje.json` a `proyectos/<producto>/montaje-<etapa>.json`: tomas en orden (con `desde`/`hasta`
  si hay que recortar), una frase por toma con su texto exacto, el cierre y las palabras clave del producto.
- Corre: `python herramientas/montar.py proyectos/<producto>/montaje-<etapa>.json` (todo corre en este PC).
- El script hace todo el criterio: voz recortada y nivelada, subtítulos palabra por palabra, acercamiento, destellos,
  sonidos, cierre con logo y volumen final. Si avisa "Revisa estas palabras", compara con el guion y corrige.

## 5. Revisión antes de entregar
- Que abra, dure lo esperado y el producto se vea en el primer segundo.
- Que los rótulos no tapen la cara ni el producto y que no queden cortados.
- Que la voz no se corte al final y que el cierre tenga el logo y el llamado a la acción.
- Entrega: ruta del video, el copy sugerido para la publicación (habilidad marketing-cocotero) y qué quedó pendiente.

## Requisitos de la máquina
Python 3.10 o más, ffmpeg en el PATH (`winget install Gyan.FFmpeg`) y `pip install faster-whisper` (subtítulos
palabra por palabra; la primera vez baja un modelo de ~0,5 GB). Pide permiso antes de instalar.
