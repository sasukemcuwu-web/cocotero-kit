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
- `generar_voz` con el texto completo de la voz en off (voz por defecto `lola`; si el equipo prefiere otra, úsala siempre).
- Descarga a `proyectos/<producto>/voz/`. Una voz por video; no partas frase por frase (ahorra cupo).

## 4. Montaje (herramientas/montar.py)
- Copia `plantillas/montaje.json` a `proyectos/<producto>/montaje-<etapa>.json` y ajusta: clips (con `desde`/`hasta`
  para recortar), voz, música opcional, rótulos con sus tiempos (que coincidan con lo que dice la voz) y el cierre.
- Corre: `python herramientas/montar.py proyectos/<producto>/montaje-<etapa>.json`
- Sale un MP4 1080x1920 a 30 fps en `proyectos/<producto>/renders/`.

## 5. Revisión antes de entregar
- Que abra, dure lo esperado y el producto se vea en el primer segundo.
- Que los rótulos no tapen la cara ni el producto y que no queden cortados.
- Que la voz no se corte al final y que el cierre tenga el logo y el llamado a la acción.
- Entrega: ruta del video, el copy sugerido para la publicación (habilidad marketing-cocotero) y qué quedó pendiente.

## Requisitos de la máquina
Python 3.10 o más y ffmpeg en el PATH (`winget install Gyan.FFmpeg` en Windows, con permiso del usuario).
