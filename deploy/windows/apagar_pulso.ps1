# Apaga Pulso en esta PC de forma ordenada: VM "ubuntu" (Pulso y VPN) y Ollama (Windows).
# Uso: doble clic en apagar_pulso.bat (o: powershell -ExecutionPolicy Bypass -File apagar_pulso.ps1)
# nodo0 (la nube) NO se apaga: mientras tanto la URL mostrará "502 Bad Gateway".

param([switch]$SinPausa)  # -SinPausa: no espera Enter al final (pruebas automáticas)
$ErrorActionPreference = 'Stop'
$VBox = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
$VM   = 'ubuntu'

function Paso($n, $texto) { Write-Host "`n[$n/2] $texto" -ForegroundColor Cyan }
function Ok($texto)    { Write-Host "  OK  $texto" -ForegroundColor Green }
function Aviso($texto) { Write-Host "  !!  $texto" -ForegroundColor Yellow }
function EstadoVM {
    $info = & $VBox showvminfo $VM --machinereadable 2>$null
    ($info | Select-String '^VMState="(.+)"').Matches.Groups[1].Value
}

Write-Host '=== Apagar Pulso ===' -ForegroundColor White

Paso 1 'Máquina virtual'
$estado = EstadoVM
if ($estado -ne 'running') { Ok "La VM ya estaba apagada ($estado)" }
else {
    # Apagado normal de Linux (como presionar el botón de encendido). No se usa "guardar estado":
    # al reanudarse después de días, la VM se colgó.
    & $VBox controlvm $VM acpipowerbutton | Out-Null
    Write-Host '  Apagando Linux (hasta 2 minutos)' -NoNewline
    for ($i = 0; $i -lt 24 -and (EstadoVM) -eq 'running'; $i++) { Write-Host '.' -NoNewline; Start-Sleep 5 }
    Write-Host ''
    if ((EstadoVM) -eq 'running') {
        Aviso 'Linux no terminó de apagarse; se fuerza el apagado'
        & $VBox controlvm $VM poweroff | Out-Null
    }
    Ok 'VM apagada'
}

Paso 2 'Ollama (IA)'
$procesos = Get-Process -Name 'ollama app', 'ollama' -ErrorAction SilentlyContinue
if ($procesos) { $procesos | Stop-Process -Force; Ok 'Ollama cerrado (vuelve a abrirse solo al iniciar sesión en Windows)' }
else { Ok 'Ollama ya estaba cerrado' }

Write-Host "`n=== Listo. Ya puedes apagar la PC o desconectar el disco D: ===" -ForegroundColor Green
Write-Host 'Para volver a encender todo: doble clic en levantar_pulso.bat'
if (-not $SinPausa) { Read-Host 'Presiona Enter para cerrar' }
