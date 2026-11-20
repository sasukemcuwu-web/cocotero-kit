# Conecta (o reconecta) el estudio Jestive en Claude Code con las credenciales ACTUALES.
# Las pide al modelo "jestive-credenciales" por la URL fija; así no hace falta que nadie te mande el enlace nuevo.
#
# Uso:  powershell -ExecutionPolicy Bypass -File herramientas\conectar-jestive.ps1
# La primera vez te pide tu clave de acceso (la que te dio Juan) y la guarda en tu usuario, fuera del repo.

$ErrorActionPreference = 'Stop'
$api = 'https://r3w75ds.abc-tunnel.us/v1/chat/completions'
$dir = Join-Path $env:USERPROFILE '.cocotero'
$archivo = Join-Path $dir 'clave-acceso.txt'
New-Item -ItemType Directory -Force $dir | Out-Null
if (-not (Test-Path $archivo)) {
  $c = Read-Host 'Pega tu clave de acceso (empieza por sk-)'
  if ($c -notmatch '^sk-[\w-]+$') { throw 'Esa clave no tiene el formato esperado.' }
  Set-Content -Path $archivo -Value $c.Trim() -Encoding ascii
}
$clave = (Get-Content $archivo -Raw).Trim()
$cuerpo = '{"model":"jestive-credenciales","messages":[{"role":"user","content":"credenciales"}]}'

$cred = $null
for ($i = 1; $i -le 12 -and -not $cred; $i++) {   # el enlace fijo a veces falla unos segundos: reintenta
  try {
    $r = Invoke-RestMethod $api -Method Post -Headers @{ Authorization = "Bearer $clave" } -ContentType 'application/json' -Body $cuerpo -TimeoutSec 30
    $cred = $r.choices[0].message.content | ConvertFrom-Json
  } catch {
    if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -in 401, 403) { throw 'La clave de acceso no sirve: pídele a Juan una nueva y borra ' + $archivo }
    Write-Host "Intento $i sin respuesta, reintento en 10 s..."; Start-Sleep 10
  }
}
if (-not $cred) { throw 'No se pudieron obtener las credenciales. Prueba en unos minutos o avisa a Juan.' }

claude mcp remove jestive 2>$null | Out-Null
claude mcp add --transport http jestive $cred.mcp_url --header "Authorization: Bearer $($cred.api_key)"
Write-Host "Jestive conectado (credenciales del $($cred.actualizado)). Reinicia la conversación de Claude Code para usarlo."
