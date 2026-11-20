"""Edición de un video de Cocotero (9:16, 1080x1920, 30 fps) con el criterio de la marca. Corre todo en tu PC.

Uso:   python herramientas/montar.py proyectos/<producto>/montaje-<etapa>.json
Necesita: ffmpeg (con libass; el de `winget install Gyan.FFmpeg` sirve) y, para subtítulos palabra por palabra,
`pip install faster-whisper` (sin él, cada frase sale entera como subtítulo).

Criterio (marca/edicion.md):
  - Una frase de voz por toma; entra 0,25 s después del inicio de la toma. Silencios de los bordes recortados,
    voz nivelada; si la frase no cabe en su toma se acelera hasta x1,2.
  - Subtítulos palabra por palabra (grupos cortos) con los tiempos reales de la voz: crema con borde verde profundo,
    palabras clave más grandes y en verde menta. Tercio inferior, sin tapar cara ni producto.
  - Acercamiento suave (4 %) dentro de cada toma; entre tomas, destello blanco corto (sin transiciones raras).
  - Cierre mínimo: fondo blanco, logo, "Respira. Suelta." en verde y la frase de cierre en voz.
  - Sonido: woosh en cada corte, woosh + ding al entrar el cierre, música baja que se agacha bajo la voz.
    Volumen final -15 LUFS.

JSON (ver plantillas/montaje.json):
  salida, tomas [{archivo, desde, hasta}], frases [{audio, texto}] (una por toma, en orden),
  cierre {texto, audio (frase de cierre en voz, opcional), logo, segundos_min}, musica (opcional),
  palabras_clave [..], modelo_whisper ("small" por defecto)
"""
import json, shutil, subprocess, sys, tempfile, unicodedata
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
CREMA, VERDE, MENTA, VERDE_CIERRE = "F4E8CC", "0D4A30", "BFE6C4", "146B47"
LEAD, FLASH = 0.25, 0.14
FUENTE = "Arial"


def ruta(p):
    p = Path(p)
    return p if p.is_absolute() else KIT / p


def ff(*a, cwd=None):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *map(str, a)], check=True, cwd=cwd)


def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True, check=True).stdout)


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def sfx(tmp):
    """Efectos propios (sin licencias de terceros): woosh suave, woosh limpio y ding."""
    w1, w2, d = tmp / "woosh-suave.wav", tmp / "woosh-limpio.wav", tmp / "ding.wav"
    ff("-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:a=0.6", "-af",
       "highpass=f=300,lowpass=f=3500,afade=t=in:d=0.25,afade=t=out:st=0.25:d=0.2,volume=0.9", w1)
    ff("-f", "lavfi", "-i", "anoisesrc=d=0.35:c=white:a=0.5", "-af",
       "highpass=f=900,lowpass=f=7000,afade=t=in:d=0.12,afade=t=out:st=0.12:d=0.23,volume=0.7", w2)
    ff("-f", "lavfi", "-i", "sine=f=1318:d=1.2", "-f", "lavfi", "-i", "sine=f=2636:d=1.2", "-filter_complex",
       "[0][1]amix=inputs=2:weights=1 0.35,afade=t=out:st=0.02:d=1.15:curve=exp,volume=0.6", d)
    return w1, w2, d


def preparar_voz(src, dst, maximo):
    base = ("silenceremove=start_periods=1:start_threshold=-48dB:start_silence=0.02,areverse,"
            "silenceremove=start_periods=1:start_threshold=-48dB:start_silence=0.02,areverse,highpass=f=70,"
            "loudnorm=I=-16:TP=-1.5:LRA=7,aformat=sample_rates=48000:channel_layouts=mono")
    ff("-i", src, "-af", base, "-c:a", "pcm_s16le", dst)
    d = dur(dst)
    if maximo and d > maximo:
        tmp2 = dst.with_name(dst.stem + "b.wav")
        ff("-i", dst, "-af", f"atempo={min(1.2, d / maximo):.3f}", "-c:a", "pcm_s16le", tmp2)
        return tmp2
    return dst


def palabras(voces, frases, modelo, claves):
    """Tiempos reales por palabra con faster-whisper, frase por frase (cada una en su sitio del video).
    Si faster-whisper no está instalado, cada frase sale entera mientras suena."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return [{"w": f["texto"], "t0": t, "t1": t + f["dur"], "key": False} for f, (_, t) in zip(frases, voces)]
    import numpy as np   # se pasa el audio ya decodificado (evita problemas de versión con PyAV)
    m = WhisperModel(modelo, device="cpu", compute_type="int8")
    guion = sin_tildes(" ".join(f["texto"] for f in frases))
    out = []
    for f, (wav, inicio) in zip(frases, voces):
        crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                               capture_output=True, check=True).stdout
        segs, _ = m.transcribe(np.frombuffer(crudo, np.int16).astype(np.float32) / 32768.0, language="es",
                               word_timestamps=True, condition_on_previous_text=False)   # sin initial_prompt: con la misma frase, Whisper se la salta
        for s in segs:
            for w in s.words or []:
                t = w.word.strip()
                if t.strip(".,;:¿?¡!"):
                    out.append({"w": t, "t0": inicio + float(w.start), "t1": inicio + float(w.end),
                                "key": sin_tildes(t.strip(".,;:¿?¡!")) in claves})
    raros = [x["w"] for x in out if sin_tildes(x["w"].strip(".,;:¿?¡!")) not in guion]
    if raros: print("Revisa estas palabras (no están en el guion):", raros)
    # grupos cortos: conectores (de, la, tu...) se pegan a la palabra siguiente
    grupos, i = [], 0
    while i < len(out):
        g = [out[i]]
        while len(g[-1]["w"]) <= 3 and i + 1 < len(out) and out[i + 1]["t0"] - g[-1]["t1"] < 0.25:
            i += 1; g.append(out[i])
        grupos.append({"w": " ".join(x["w"] for x in g), "t0": g[0]["t0"], "t1": g[-1]["t1"], "key": any(x["key"] for x in g)})
        i += 1
    return grupos


def ass(grupos, fin, archivo):
    t = lambda s: f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"
    bgr = lambda h: h[4:6] + h[2:4] + h[0:2]
    cab = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV\n"
           f"Style: S,{FUENTE},96,&H00{bgr(CREMA)},&H00{bgr(VERDE)},&H64000000,-1,0,1,9,3,2,60,60,700\n\n[Events]\n"
           "Format: Layer, Start, End, Style, Text\n")
    filas = []
    for k, g in enumerate(grupos):
        fin_g = min(grupos[k + 1]["t0"], fin) if k + 1 < len(grupos) else min(g["t1"] + 0.4, fin)
        txt = g["w"].lower().strip(".,;:")
        if g["key"]: txt = f"{{\\c&H{bgr(MENTA)}&\\fscx115\\fscy115}}{txt}"
        filas.append(f"Dialogue: 0,{t(g['t0'])},{t(max(fin_g, g['t0'] + 0.15))},S,{{\\fad(40,0)}}{txt}")
    Path(archivo).write_text(cab + "\n".join(filas) + "\n", encoding="utf-8")


def main():
    if not shutil.which("ffmpeg"): sys.exit("Falta ffmpeg: winget install Gyan.FFmpeg (y abre una terminal nueva).")
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    salida = ruta(cfg["salida"]); salida.parent.mkdir(parents=True, exist_ok=True)
    tomas, frases = cfg["tomas"], cfg.get("frases", [])
    tmp = Path(tempfile.mkdtemp(prefix="cocotero-"))
    try:
        # 1) tomas: llenar 9:16, acercamiento suave
        largos, piezas = [], []
        for i, c in enumerate(tomas):
            a = ruta(c["archivo"]); real = dur(a) - 0.03
            d0 = float(c.get("desde", 0)); d1 = min(float(c.get("hasta", real)), real)   # nunca más de lo que dura la toma
            d = d1 - d0; n = int(d * FPS)
            o = tmp / f"t{i}.mp4"
            ff("-ss", d0, "-t", d, "-i", a, "-vf",
               f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
               f"zoompan=z='1+0.04*on/{max(1, n)}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps={FPS},format=yuv420p",
               "-an", "-c:v", "libx264", "-crf", "16", "-preset", "fast", o)
            piezas.append(o); largos.append(dur(o))
        principal = sum(largos) - FLASH * (len(piezas) - 1)
        cortes = [sum(largos[:k]) - FLASH * k for k in range(1, len(piezas))]
        # 2) voz: una frase por toma
        inicios = [0.0] + cortes
        voces = []
        for k, f in enumerate(frases[: len(piezas)]):
            ventana = (inicios[k + 1] if k + 1 < len(inicios) else principal) - inicios[k] - LEAD - 0.35
            v = preparar_voz(ruta(f["audio"]), tmp / f"v{k}.wav", ventana)
            voces.append((v, inicios[k] + LEAD)); f["dur"] = dur(v)
        ci = cfg.get("cierre", {})
        voz_cierre = preparar_voz(ruta(ci["audio"]), tmp / "vc.wav", None) if ci.get("audio") else None
        cola = max(float(ci.get("segundos_min", 3.8)), (dur(voz_cierre) + 1.6) if voz_cierre else 0)
        total = principal + cola
        # 3) cierre mínimo
        logo = ruta(ci.get("logo", "marca/logo-cocotero.png"))
        (tmp / "c.txt").write_text(ci.get("texto", "Respira. Suelta."), encoding="utf-8")
        negrita = next((f for f in (Path("C:/Windows/Fonts/arialbd.ttf"), Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
                                    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")) if f.exists()), None)
        if negrita: shutil.copy(negrita, tmp / "f.ttf")
        letra = "fontfile=f.ttf" if negrita else f"font={FUENTE}"
        ff("-f", "lavfi", "-i", f"color=c=white:s={W}x{H}:r={FPS}:d={cola}", "-loop", "1", "-t", cola, "-i", logo, "-filter_complex",
           f"[1]scale=560:-1[l];[0][l]overlay=(W-w)/2:(H-h)/2-180,drawtext={letra}:textfile=c.txt:fontsize=62:"
           f"fontcolor=0x{VERDE_CIERRE}:x=(w-text_w)/2:y=h*0.62,fade=t=in:d=0.25,format=yuv420p",
           "-c:v", "libx264", "-crf", "16", "-preset", "fast", "cierre.mp4", cwd=tmp)
        # 4) unir: destello blanco entre tomas y fundido al cierre
        cadena, ent, off = "[0:v]", [], 0.0
        for p in piezas + [tmp / "cierre.mp4"]: ent += ["-i", p]
        fc = []
        for k in range(1, len(piezas) + 1):
            off = (cortes[k - 1] if k < len(piezas) else principal) - (FLASH if k < len(piezas) else 0.2)
            trans = "fadewhite" if k < len(piezas) else "fade"
            dd = FLASH if k < len(piezas) else 0.2
            fc.append(f"{cadena}[{k}:v]xfade=transition={trans}:duration={dd}:offset={off:.3f}[x{k}]"); cadena = f"[x{k}]"
        # 5) audio: voz + cierre + sfx + música
        w1, w2, ding = sfx(tmp)
        partes = [(v, t) for v, t in voces]
        if voz_cierre: partes.append((voz_cierre, principal + 0.6))
        partes += [(w1 if k == 0 else w2, max(0, c - 0.2)) for k, c in enumerate(cortes)] + [(w2, principal), (ding, principal + 0.9)]
        base_a = len(piezas) + 1
        for f, t in partes: ent += ["-i", f]
        mix = []
        for k, (f, t) in enumerate(partes):
            ms = int(t * 1000)
            fc.append(f"[{base_a + k}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms}[p{k}]"); mix.append(f"[p{k}]")
        fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=longest,apad=whole_dur={total:.3f}[voz]")
        voz_lbl = "[voz]"
        if cfg.get("musica"):
            ent += ["-stream_loop", "-1", "-i", ruta(cfg["musica"])]
            fc.append(f"[{base_a + len(partes)}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.25,atrim=0:{total:.3f},"
                      f"afade=t=out:st={total - 1.2:.3f}:d=1.2[mu]")
            fc.append("[voz]asplit=2[v1][v2];[mu][v2]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[muc];"
                      "[v1][muc]amix=inputs=2:normalize=0[voz2]"); voz_lbl = "[voz2]"
        fc.append(f"{voz_lbl}atrim=0:{total:.3f},loudnorm=I=-15:TP=-1.5:LRA=9[aout]")
        crudo = tmp / "crudo.mp4"
        ff(*ent, "-filter_complex", ";".join(fc), "-map", cadena, "-map", "[aout]", "-t", f"{total:.3f}", "-c:v", "libx264",
           "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", crudo)
        # 6) subtítulos palabra por palabra sobre la parte principal
        claves = {sin_tildes(x) for x in cfg.get("palabras_clave", [])}
        grupos = palabras(voces, frases[: len(voces)], cfg.get("modelo_whisper", "small"), claves) if voces else []
        print("Subtítulos:", " | ".join(f"{g['t0']:.1f} {g['w']}" for g in grupos))
        ass(grupos, principal, tmp / "subs.ass")
        ff("-i", crudo, "-vf", "subtitles=subs.ass", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
           "-c:a", "copy", "-movflags", "+faststart", salida.resolve(), cwd=tmp)
        print(f"Listo: {salida}  ({total:.1f} s: {principal:.1f} s de tomas + {cola:.1f} s de cierre)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
