"""Monta un video vertical 1080x1920 (30 fps) de Cocotero desde un montaje.json.

Uso:  python herramientas/montar.py proyectos/<producto>/montaje-<etapa>.json
Necesita ffmpeg en el PATH. Las rutas del JSON son relativas a la carpeta del kit.

JSON (ver plantillas/montaje.json):
  salida            ruta del MP4 final
  clips             [{archivo, desde, hasta}]  se recortan, se llenan a 9:16 y se pegan en orden
  voz               MP3/WAV de la voz en off (opcional)
  musica            música de fondo (opcional), volumen_musica (0.12 por defecto)
  textos            [{texto, desde, hasta}]  rótulos sobre el video (tiempos del video, sin contar el cierre)
  cierre            {logo, texto, llamado, duracion}  tarjeta final crema con el logo (opcional)
"""
import json, shutil, subprocess, sys, tempfile, textwrap
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
CREMA, VERDE = "0xF6F1E4", "0x2F5D3A"
FUENTES = [Path("C:/Windows/Fonts/arialbd.ttf"), Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
           Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]


def ruta(p):
    p = Path(p)
    return p if p.is_absolute() else KIT / p


def duracion(archivo):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(archivo)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def main():
    if not shutil.which("ffmpeg"):
        sys.exit("Falta ffmpeg. En Windows: winget install Gyan.FFmpeg (y abre una terminal nueva).")
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    salida = ruta(cfg["salida"]); salida.parent.mkdir(parents=True, exist_ok=True)
    fuente = next((f for f in FUENTES if f.exists()), None)
    tmp = Path(tempfile.mkdtemp(prefix="montar-"))
    try:
        if fuente: shutil.copy(fuente, tmp / "f.ttf")
        entradas, filtros, partes, total = [], [], [], 0.0
        for i, c in enumerate(cfg["clips"]):
            a = ruta(c["archivo"])
            if not a.exists(): sys.exit(f"No existe el clip: {a}")
            desde = float(c.get("desde", 0)); hasta = float(c.get("hasta", duracion(a)))
            entradas += ["-i", str(a)]
            filtros.append(f"[{i}:v]trim={desde}:{hasta},setpts=PTS-STARTPTS,scale={W}:{H}:force_original_aspect_ratio=increase,"
                           f"crop={W}:{H},fps={FPS},setsar=1,format=yuv420p[v{i}]")
            partes.append(f"[v{i}]"); total += hasta - desde
        filtros.append(f"{''.join(partes)}concat=n={len(partes)}:v=1:a=0[base]")
        # rótulos
        fnt = "fontfile=f.ttf:" if fuente else ""
        ultimo = "base"
        for k, t in enumerate(cfg.get("textos", [])):
            for j, linea in enumerate(textwrap.wrap(t["texto"], 20)):   # cada línea centrada por separado
                (tmp / f"t{k}_{j}.txt").write_text(linea, encoding="utf-8")
                filtros.append(f"[{ultimo}]drawtext={fnt}textfile=t{k}_{j}.txt:fontsize=68:fontcolor=white:borderw=7:bordercolor=black@0.85:"
                               f"x=(w-text_w)/2:y=h*0.66+{j * 86}:enable='between(t,{t['desde']},{t['hasta']})'[r{k}_{j}]")
                ultimo = f"r{k}_{j}"
        video_final = ultimo
        # cierre
        ci = cfg.get("cierre")
        n = len(cfg["clips"])
        if ci:
            d = float(ci.get("duracion", 1.8))
            filtros.append(f"color=c={CREMA}:s={W}x{H}:r={FPS}:d={d},format=yuv420p[fondo]")
            logo = ruta(ci["logo"]) if ci.get("logo") else None
            cierre = "fondo"
            if logo and logo.exists():
                entradas += ["-loop", "1", "-t", str(d), "-i", str(logo)]
                filtros.append(f"[{n}:v]scale=620:-1,format=rgba[logo]")
                filtros.append("[fondo][logo]overlay=(W-w)/2:(H-h)/2-160[cl]"); cierre = "cl"; n += 1
            for k, (campo, y, tam) in enumerate((("texto", "h*0.66", 64), ("llamado", "h*0.74", 52))):
                if ci.get(campo):
                    (tmp / f"c{k}.txt").write_text(ci[campo], encoding="utf-8")
                    filtros.append(f"[{cierre}]drawtext={fnt}textfile=c{k}.txt:fontsize={tam}:fontcolor={VERDE}:x=(w-text_w)/2:y={y}[cc{k}]")
                    cierre = f"cc{k}"
            filtros.append(f"[{video_final}][{cierre}]concat=n=2:v=1:a=0[vout]"); total += d
        else:
            filtros.append(f"[{video_final}]null[vout]")
        # audio
        mezcla = []
        if cfg.get("voz"):
            entradas += ["-i", str(ruta(cfg["voz"]))]
            filtros.append(f"[{n}:a]aresample=48000,apad[voz]"); mezcla.append("[voz]"); n += 1
        if cfg.get("musica"):
            entradas += ["-stream_loop", "-1", "-i", str(ruta(cfg["musica"]))]
            filtros.append(f"[{n}:a]aresample=48000,volume={cfg.get('volumen_musica', 0.12)},afade=t=out:st={max(0, total - 1)}:d=1[mus]")
            mezcla.append("[mus]"); n += 1
        if not mezcla:
            entradas += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]; mezcla.append(f"[{n}:a]")
        filtros.append(f"{''.join(mezcla)}amix=inputs={len(mezcla)}:normalize=0,atrim=0:{total},alimiter=limit=0.95[aout]")
        cmd = ["ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex", ";".join(filtros), "-map", "[vout]", "-map", "[aout]",
               "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(salida.resolve())]
        subprocess.run(cmd, cwd=tmp, check=True)
        print(f"Listo: {salida} ({total:.1f} s)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
