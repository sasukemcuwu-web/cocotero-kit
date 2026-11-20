# Cocotero Kit

Kit para trabajar el contenido de **Cocotero** con Claude Code (VS Code): videos cortos verticales, marketing y plantillas.

## Qué trae
- `CLAUDE.md`: reglas de la marca y cómo trabajar (Claude lo lee solo).
- `.claude/skills/video-cocotero`: video de punta a punta (guion → tomas → voz → montaje).
- `.claude/skills/marketing-cocotero`: copys, ideas, calendario, fichas de producto.
- `plantillas/`: guion, prompt de toma e imagen, copy, calendario semanal, ficha de producto, `montaje.json`.
- `marca/`: logo, productos, tono y embudo TOFU/MOFU/BOFU.
- `herramientas/montar.py`: arma el MP4 final 1080x1920 con rótulos, voz, música y cierre con logo.

## Instalar (una vez)
1. Clonar: `git clone https://github.com/sasukemcuwu-web/cocotero-kit.git` y abrir la carpeta en VS Code.
2. Python 3.10+ y ffmpeg: `winget install Python.Python.3.12` y `winget install Gyan.FFmpeg` (abrir una terminal nueva después).
3. Conectar el estudio (Jestive) en Claude Code, con el conector que te pasa Juan:
   `claude mcp add --transport http jestive <URL>/mcp --header "Authorization: Bearer <TU_CLAVE>"`
   (si la URL cambia, Juan te pasa la nueva: `claude mcp remove jestive` y se vuelve a agregar).
4. Probar: pedirle a Claude "mira mi cupo del estudio" y "haz los 3 videos del producto 3".

## Probar el montaje sin generar nada
`python herramientas/montar.py plantillas/montaje.json` (necesita clips en `proyectos/ejemplo/tomas/`).

Los proyectos (`proyectos/`) y los videos no se suben a git.
