# Levanta Pulso en esta PC: Ollama (Windows) + VM "ubuntu" (Pulso y VPN) y comprueba la URL pública.
# Uso: doble clic en levantar_pulso.bat (o: powershell -ExecutionPolicy Bypass -File levantar_pulso.ps1)
# No necesita contraseñas. Solo pide permiso de administrador (UAC) si hay bases de datos que detener.
param([switch]$SinPausa)  # -SinPausa: no espera Enter (pruebas automáticas)

$ErrorActionPreference = 'Stop'
$VBox      = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
$VM        = 'ubuntu'
$VboxFile  = 'D:\VirtualBox VMs\ubuntu\ubuntu.vbox'
$OllamaDir = Join-Path $env:LOCALAPPDATA 'Programs\Ollama'
$Url       = 'https://mentalhealth-app.duckdns.org'
$BasesDatos = 'mysql', 'MySQL80', 'postgresql-x64-13', 'postgresql-x64-17'
$RamNecesariaMB = 3500   # VM (1.5 GB) + modelo granite4.2:3b (unos 2 GB)

function Paso($n, $texto) { Write-Host "`n[$n/7] $texto" -ForegroundColor Cyan }
function Ok($texto)    { Write-Host "  OK  $texto" -ForegroundColor Green }
function Aviso($texto) { Write-Host "  !!  $texto" -ForegroundColor Yellow }
function Pausa($texto) { if (-not $SinPausa) { Read-Host $texto | Out-Null } }
function Falla($texto) { Write-Host "  XX  $texto" -ForegroundColor Red; Pausa "`nPresiona Enter para cerrar"; exit 1 }
function Responde($uri, $seg = 5) { try { Invoke-RestMethod -Uri $uri -TimeoutSec $seg } catch { $null } }
function RamDisponibleMB { [int](Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory).AvailableMBytes }
function EstadoVM {
    $info = & $VBox showvminfo $VM --machinereadable 2>$null
    ($info | Select-String '^VMState="(.+)"').Matches.Groups[1].Value
}

Write-Host '=== Levantar Pulso ===' -ForegroundColor White

Paso 1 'Disco de la VM'
if (-not (Test-Path $VboxFile)) { Falla "No encuentro $VboxFile. Conecta el disco de la VM y revisa que aparezca como D:." }
Ok 'Disco conectado'

Paso 2 'Liberar memoria (bases de datos)'
$activas = Get-Service -Name $BasesDatos -ErrorAction SilentlyContinue | Where-Object Status -eq 'Running'
if ($activas) {
    $nombres = ($activas.Name | ForEach-Object { "'$_'" }) -join ','
    Aviso "Deteniendo $($activas.Name -join ', ') (Windows pedirá permiso)"
    try {
        Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList '-NoProfile', '-Command', "Stop-Service -Name $nombres -Force"
        Ok 'Bases de datos detenidas (vuelven a arrancar solas al reiniciar Windows)'
    } catch { Aviso 'No se dio permiso; sigo, pero puede faltar memoria' }
} else { Ok 'No hay bases de datos encendidas' }

Paso 3 'Memoria disponible'
$vmYaCorre = (EstadoVM) -eq 'running'
$necesaria = if ($vmYaCorre) { 2000 } else { $RamNecesariaMB }
while ((RamDisponibleMB) -lt $necesaria) {
    Aviso "Hay $(RamDisponibleMB) MB disponibles y se necesitan unos $necesaria MB. Lo que más ocupa:"
    Get-Process | Group-Object ProcessName |
        ForEach-Object { [pscustomobject]@{ Programa = $_.Name; MB = [int](($_.Group | Measure-Object WorkingSet64 -Sum).Sum / 1MB) } } |
        Where-Object { $_.Programa -notin 'Memory Compression', 'System', 'svchost', 'MsMpEng', 'explorer', 'powershell', 'dwm' } |
        Sort-Object MB -Descending | Select-Object -First 6 | Format-Table -AutoSize | Out-Host
    if ($SinPausa) { Aviso 'Sigo sin la memoria recomendada; la VM o la IA pueden trabarse'; break }
    $r = Read-Host '  Cierra programas (navegadores, Spotify, etc.) y presiona Enter para volver a medir, o escribe S para seguir así'
    if ($r -match '^[sS]') { break }
}
if ((RamDisponibleMB) -ge $necesaria) { Ok "$(RamDisponibleMB) MB disponibles" }

Paso 4 'Ollama (IA) en Windows'
# Contexto de 2048 tokens: las explicaciones usan menos de 1500 y el modelo ocupa menos RAM.
[Environment]::SetEnvironmentVariable('OLLAMA_CONTEXT_LENGTH', '2048', 'User')
$env:OLLAMA_CONTEXT_LENGTH = '2048'
if (-not (Responde 'http://127.0.0.1:11434/api/version')) {
    Start-Process (Join-Path $OllamaDir 'ollama app.exe')
    for ($i = 0; $i -lt 10 -and -not (Responde 'http://127.0.0.1:11434/api/version'); $i++) { Start-Sleep 2 }
    if (-not (Responde 'http://127.0.0.1:11434/api/version')) {
        # A veces la app de bandeja abre pero no arranca su servidor: se arranca directo (escucha solo en 127.0.0.1).
        Aviso 'La app de Ollama no levantó su servidor; lo arranco directo'
        Start-Process (Join-Path $OllamaDir 'ollama.exe') -ArgumentList 'serve' -WindowStyle Hidden
        for ($i = 0; $i -lt 20 -and -not (Responde 'http://127.0.0.1:11434/api/version'); $i++) { Start-Sleep 2 }
    }
}
$ver = Responde 'http://127.0.0.1:11434/api/version'
if (-not $ver) { Falla 'Ollama no responde en 127.0.0.1:11434' }
Ok "Ollama $($ver.version) responde (solo en esta PC)"

Paso 5 'Máquina virtual (Pulso + VPN)'
$estado = EstadoVM
if (-not $estado) {
    Aviso 'La VM no está registrada en VirtualBox; la registro desde D:'
    & $VBox registervm $VboxFile | Out-Null
    $estado = EstadoVM
}
if ($estado -eq 'running') { Ok 'La VM ya estaba encendida' }
else {
    if ($estado -eq 'saved') { Aviso 'La VM estaba en estado guardado; se descarta para arrancar limpia'; & $VBox discardstate $VM | Out-Null }
    & $VBox startvm $VM --type headless | Out-Null
    Ok 'VM encendida (sin ventana)'
}

Paso 6 'Esperando a que Pulso responda en Internet (hasta 4 minutos)'
$listo = $false
for ($i = 0; $i -lt 48; $i++) {
    $s = Responde "$Url/api/salud/ollama" 10
    if ($s -and $s.ok) { $listo = $true; break }
    Write-Host '.' -NoNewline; Start-Sleep 5
}
Write-Host ''
if (-not $listo) { Falla "La URL no responde. Abre VirtualBox, mira la VM 'ubuntu' y vuelve a correr este script." }
Ok "$Url responde y la app ve a Ollama ($($s.modelo))"

Paso 7 'Prueba final: una explicación real con IA (carga el modelo; tarda 1 a 2 minutos)'
if (-not $vmYaCorre) {
    # Cargar el modelo justo cuando la VM acaba de arrancar la llegó a colgar: se espera a que se estabilice.
    Write-Host '  Dejando que la VM se estabilice 60 s' -NoNewline
    for ($i = 0; $i -lt 12; $i++) { Write-Host '.' -NoNewline; Start-Sleep 5 }
    Write-Host ''
}
try {
    $cuerpo = '{"vacante_id":"V04","perfil":{"A1":67,"A2":100,"A3":67,"A7":33}}'
    $t = Get-Date
    $r = Invoke-RestMethod -Uri "$Url/api/explicar" -Method Post -Body $cuerpo -ContentType 'application/json' -TimeoutSec 200
    $seg = [int]((Get-Date) - $t).TotalSeconds
    if ($r.fuente -eq 'ia') { Ok "La IA respondió en $seg s usando $($r.herramientas -join ', ')" }
    else { Aviso "Respondió la explicación automática (plantilla) en $seg s; vuelve a probar «¿Por qué?» en la página" }
} catch { Aviso "La prueba de la IA falló: $($_.Exception.Message). La página sigue funcionando con la explicación automática." }

Write-Host "`n=== Listo. Abre $Url ===" -ForegroundColor Green
Pausa 'Presiona Enter para cerrar'
