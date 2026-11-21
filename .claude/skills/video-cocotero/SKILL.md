---
name: video-cocotero
description: Hace un video corto vertical (9:16) de un producto de Cocotero de punta a punta - guion por etapa del embudo, tomas y voz con Higgsfield, montaje con subtítulos y cierre con logo. Úsala cuando pidan un video, un reel, un TikTok o "los 3 videos" de un producto.
---

# Video de Cocotero

Lee antes: `CLAUDE.md`, `marca/embudo.md`, `marca/productos.md`, `marca/tono.md`.

## 1. Guion (plantillas/guion-video.md)
- Elige la etapa (TOFU, MOFU o BOFU) o haz las tres con las mismas 3 tomas.
- Copia la plantilla a `proyectos/<producto>/guion-<etapa>.md` y llénala: gancho de 0–2 s, tomas, voz (3–4 frases cortas),
  rótulos de 2–5 palabras y cierre. Nada inventado; lo no confirmado va como `[POR CONFIRMAR]`.

## 2. Tomas (plantillas/prompt-toma.md)
- Antes de generar, mira el saldo de créditos de Higgsfield y estima el costo de las tomas (`estimate_video_cost`). Dile al
  usuario cuánto va a gastar en una línea y sigue; si la tanda gasta más de la mitad del saldo, pregunta primero.
- `generate_video` en vertical 9:16, 4 a 6 s por toma. Escribe el prompt en inglés con la plantilla: una acción, un plano,
  sin texto, sin cortes, el producto descrito como es en la foto real. Si tienes la foto del producto, súbela como referencia.
- Lanza las tomas y, mientras se generan, haz la voz. Espera los trabajos y descarga cada toma a
  `proyectos/<producto>/tomas/` (por ejemplo con `curl -L -o toma-a.mp4 "<url>"`).
- Si una toma sale con texto, cortes raros o un producto distinto, avisa y propón un prompt corregido (un reintento).

## 3. Voz
- `generate_audio` (voz hablada) **una vez por frase** (una por toma) más la frase de cierre, en español con acento
  colombiano suave, siempre la misma voz (la que elija el equipo). Descarga a `proyectos/<producto>/voz/f1.mp3`, `f2.mp3`, `f3.mp3`, `cierre.mp3`.
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
Python 3.10 o más, ffmpeg en el PATH y faster-whisper (subtítulos palabra por palabra). En la Chromebook ya está todo
en `.venv` y el lanzador lo activa; en equipos chicos usa el modelo `base` y renderiza en 1080x1920, un render a la vez.
