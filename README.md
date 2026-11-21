# Cocotero Kit

Kit para trabajar el contenido de **Cocotero** con Claude Code (VS Code): videos cortos verticales, marketing y plantillas.

## Qué trae
- `CLAUDE.md`: reglas de la marca y cómo trabajar (Claude lo lee solo).
- `.claude/skills/video-cocotero`: video de punta a punta (guion → tomas → voz → montaje).
- `.claude/skills/marketing-cocotero`: copys, ideas, calendario, fichas de producto.
- `plantillas/`: guion, prompt de toma e imagen, copy, calendario semanal, ficha de producto, `montaje.json`.
- `marca/`: logo, productos, tono y embudo TOFU/MOFU/BOFU.
- `herramientas/montar.py`: edita el MP4 final 1080x1920 con el criterio de Cocotero (`marca/edicion.md`): voz limpia,
  subtítulos palabra por palabra, acercamiento, destellos, sonidos propios y cierre con logo.

## Instalar (una vez)
1. Clonar: `git clone https://github.com/sasukemcuwu-web/cocotero-kit.git` y abrir la carpeta en VS Code.
2. Python 3.10+, ffmpeg y los subtítulos: `winget install Python.Python.3.12`, `winget install Gyan.FFmpeg`
   (abrir una terminal nueva) y `pip install faster-whisper`. Todo el montaje corre en tu PC.
3. Conectar Higgsfield como conector en tu cuenta de Claude (claude.ai > Configuración > Conectores). Las tomas, la voz
   y las imágenes se generan ahí con tus créditos.
4. Probar: pedirle a Claude "mira mis créditos de Higgsfield" y "haz los 3 videos del producto 3".

## Probar el montaje sin generar nada
`python herramientas/montar.py plantillas/montaje.json` (necesita clips en `proyectos/ejemplo/tomas/`).

Los proyectos (`proyectos/`) y los videos no se suben a git.
