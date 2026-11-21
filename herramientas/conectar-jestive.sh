#!/usr/bin/env bash
# Conecta (o reconecta) el estudio Jestive en Claude Code con las credenciales ACTUALES (Linux / Chromebook).
# Las pide al modelo "jestive-credenciales" por la URL fija; así no hace falta que nadie te mande el enlace nuevo.
#
# Uso:  bash herramientas/conectar-jestive.sh        (con --silencioso no imprime nada si todo sale bien)
# La primera vez te pide tu clave de acceso (la que te dio Juan) y la guarda en ~/.cocotero, fuera del repo.
set -euo pipefail
API='https://r3w75ds.abc-tunnel.us/v1/chat/completions'
DIR="$HOME/.cocotero"; ARCHIVO="$DIR/clave-acceso.txt"
SIL=0; [ "${1:-}" = "--silencioso" ] && SIL=1
mkdir -p "$DIR"; chmod 700 "$DIR"
if [ ! -s "$ARCHIVO" ]; then
  read -r -s -p 'Pega tu clave de acceso (empieza por sk-): ' C; echo
  [[ "$C" =~ ^sk-[A-Za-z0-9_-]+$ ]] || { echo 'Esa clave no tiene el formato esperado.' >&2; exit 1; }
  printf '%s' "$C" > "$ARCHIVO"; chmod 600 "$ARCHIVO"
fi
CLAVE="$(tr -d '[:space:]' < "$ARCHIVO")"
CUERPO='{"model":"jestive-credenciales","messages":[{"role":"user","content":"credenciales"}]}'

CRED=''
for i in $(seq 1 12); do   # el enlace fijo a veces falla unos segundos: reintenta
  COD=$(curl -sS -o /tmp/.jestive-cred.json -w '%{http_code}' --max-time 30 "$API" \
        -H "Authorization: Bearer $CLAVE" -H 'Content-Type: application/json' -d "$CUERPO" || echo 000)
  if [ "$COD" = 401 ] || [ "$COD" = 403 ]; then
    rm -f /tmp/.jestive-cred.json; echo "La clave de acceso no sirve: pídele a Juan una nueva y borra $ARCHIVO" >&2; exit 1
  fi
  if [ "$COD" = 200 ]; then
    # raw_decode: a veces la respuesta trae texto extra después del JSON
    CRED=$(python3 -c 'import json; t=open("/tmp/.jestive-cred.json").read().strip(); print(json.JSONDecoder().raw_decode(t)[0]["choices"][0]["message"]["content"])' 2>/dev/null || true)
    [ -n "$CRED" ] && break
  fi
  [ $SIL = 1 ] || echo "Intento $i sin respuesta, reintento en 10 s..."; sleep 10
done
rm -f /tmp/.jestive-cred.json
[ -n "$CRED" ] || { echo 'No se pudieron obtener las credenciales. Prueba en unos minutos o avisa a Juan.' >&2; exit 1; }

# Escribe el servidor en ~/.claude.json (alcance de usuario) directamente: `claude mcp add` tarda minutos en equipos chicos.
# Hazlo con Claude Code cerrado (el lanzador lo corre antes de abrirlo).
printf '%s' "$CRED" | python3 -c '
import json, os, sys
c = json.JSONDecoder().raw_decode(sys.stdin.read().strip())[0]
p = os.path.expanduser("~/.claude.json")
d = json.load(open(p)) if os.path.exists(p) else {}
d.setdefault("mcpServers", {})["jestive"] = {"type": "http", "url": c["mcp_url"],
    "headers": {"Authorization": "Bearer " + c["api_key"]}}
tmp = p + ".tmp"
json.dump(d, open(tmp, "w"), indent=2)
os.chmod(tmp, 0o600); os.replace(tmp, p)
'
[ $SIL = 1 ] || echo 'Jestive conectado. Reinicia la conversación de Claude Code para usarlo.'
