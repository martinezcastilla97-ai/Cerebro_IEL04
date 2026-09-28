<#
.SYNOPSIS
    Crea una copia limpia de esta plantilla de cerebro docente.

.DESCRIPTION
    Copia toda la plantilla (incluida la carpeta oculta .obsidian) a una carpeta nueva,
    sin lo que es propio de una instancia en uso (memory_store, __pycache__, .git), y deja
    el wiki/log.md de la copia vacio (solo la cabecera y el formato de entradas).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File config\nuevo-cerebro.ps1 -Destino "C:\Ruta\Programa_X" -Nombre "Programa X"

.NOTES
    Este archivo es ASCII a proposito: Windows PowerShell 5.1 lee los .ps1 sin BOM como ANSI.
#>
param(
    [Parameter(Mandatory = $true)][string]$Destino,
    [string]$Nombre
)

$ErrorActionPreference = "Stop"
$origen = Split-Path -Parent $PSScriptRoot      # la carpeta que contiene config/

if (Test-Path -LiteralPath $Destino) {
    throw "El destino ya existe: $Destino. Elige una carpeta nueva."
}

# /E incluye subcarpetas vacias y ocultas; robocopy devuelve 0-7 si todo fue bien.
& robocopy $origen $Destino /E /XD memory_store __pycache__ .git /XF *.pyc /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy fallo (codigo $LASTEXITCODE)" }

$utf8 = New-Object System.Text.UTF8Encoding($false)

# Log vacio: solo la cabecera y el formato de entradas (todo lo anterior a la primera entrada).
$rutaLog = Join-Path $Destino "wiki\log.md"
if (Test-Path -LiteralPath $rutaLog) {
    $log = Get-Content -LiteralPath $rutaLog -Raw -Encoding UTF8
    # Solo cuenta como entrada un encabezado con fecha real: la cabecera trae un ejemplo "## [YYYY-MM-DD]".
    $entrada = [regex]::Match($log, '(?m)^## \[\d{4}-\d{2}-\d{2}\]')
    if ($entrada.Success) { $log = $log.Substring(0, $entrada.Index).TrimEnd() + "`n" }
    [System.IO.File]::WriteAllText($rutaLog, $log, $utf8)
}

# Sin archivos recientes de Obsidian: son de quien uso la plantilla, no de la copia.
$rutaEspacio = Join-Path $Destino ".obsidian\workspace.json"
if (Test-Path -LiteralPath $rutaEspacio) {
    $espacio = Get-Content -LiteralPath $rutaEspacio -Raw -Encoding UTF8
    $espacio = [regex]::Replace($espacio, '"lastOpenFiles":\s*\[[^\]]*\]', '"lastOpenFiles": []')
    [System.IO.File]::WriteAllText($rutaEspacio, $espacio, $utf8)
}

# Titulo del README con el nombre de la copia.
if ($Nombre) {
    $rutaReadme = Join-Path $Destino "README.md"
    $readme = Get-Content -LiteralPath $rutaReadme -Raw -Encoding UTF8
    $guion = [string][char]0x2014
    $readme = $readme -replace "^# Cerebro Docente", ("# Cerebro Docente " + $guion + " " + $Nombre)
    [System.IO.File]::WriteAllText($rutaReadme, $readme, $utf8)
}

Write-Output "Copia creada en: $Destino"
Write-Output "Siguientes pasos:"
Write-Output "  1. Abrir la carpeta como vault en Obsidian e instalar el plugin Dataview."
Write-Output "  2. pip install -r requirements.txt   y configurar el proveedor de IA (README, 'Configurar el modelo de IA')."
Write-Output "  3. Si trabajas con un asistente de IA, abrirlo en esa carpeta: sus reglas estan en CLAUDE.md (AGENTS.md y GEMINI.md apuntan a el)."
Write-Output "  4. Colocar los documentos en raw/ y seguir el flujo de trabajo del README."
