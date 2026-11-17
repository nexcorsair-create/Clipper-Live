# Instala (o actualiza) Clipper Live en Windows.
# Uso:            irm https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.ps1 | iex
# In English:     $env:CLIPPER_LANG="en"; irm https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.ps1 | iex
# Em portugues:   $env:CLIPPER_LANG="pt"; irm https://raw.githubusercontent.com/nexcorsair-create/Clipper-Live/main/instalar.ps1 | iex
$ErrorActionPreference = "Stop"
$Repo = "nexcorsair-create/Clipper-Live"
$Ramo = "main"
$Skill = Join-Path $HOME ".claude\skills\clipper-live"

$L = "$env:CLIPPER_LANG".ToLower()
if ($L -notin @("es", "en", "pt")) { $L = "es" }
$env:CLIPPER_LANG = $L
$M = @{
    es = @{ titulo = "== Clipper Live: instalando =="; baja = "  ... descargando la skill de github.com/$Repo";
            ok = "  OK skill en $Skill"; py = "  ... no encontre Python 3.10+; instalando Python 3.12 con winget";
            reabre = "`nFALTA: Python ya esta instalado, pero esta terminal todavia no lo ve. Cierra y abre la terminal (o la app de Claude) y ejecuta el comando otra vez." }
    en = @{ titulo = "== Clipper Live: installing =="; baja = "  ... downloading the skill from github.com/$Repo";
            ok = "  OK skill in $Skill"; py = "  ... Python 3.10+ not found; installing Python 3.12 with winget";
            reabre = "`nMISSING: Python is installed, but this terminal can't see it yet. Close and reopen the terminal (or the Claude app) and run the command again." }
    pt = @{ titulo = "== Clipper Live: instalando =="; baja = "  ... baixando a skill de github.com/$Repo";
            ok = "  OK skill em $Skill"; py = "  ... nao achei Python 3.10+; instalando o Python 3.12 pelo winget";
            reabre = "`nFALTA: Python instalado, mas este terminal ainda nao enxerga. Feche e abra o terminal (ou o app do Claude) e rode o comando de novo." }
}[$L]

Write-Host $M.titulo

# 1. descarga la skill
$tmp = Join-Path $env:TEMP ("clipper-live-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force $tmp | Out-Null
$zip = Join-Path $tmp "skill.zip"
Write-Host $M.baja
Invoke-WebRequest -UseBasicParsing "https://github.com/$Repo/archive/refs/heads/$Ramo.zip" -OutFile $zip
Expand-Archive $zip -DestinationPath $tmp -Force
$origen = Get-ChildItem $tmp -Directory | Select-Object -First 1
if (Test-Path $Skill) { Remove-Item -Recurse -Force $Skill }
New-Item -ItemType Directory -Force (Split-Path $Skill) | Out-Null
Copy-Item -Recurse $origen.FullName $Skill
Remove-Item -Recurse -Force $tmp
Write-Host $M.ok

# 2. busca un Python 3.10 o mas nuevo
function Buscar-Python {
    foreach ($c in @(@("py", "-3"), @("python"), @("python3"))) {
        try {
            $exe = $c[0]; $args_ = @(); if ($c.Length -gt 1) { $args_ = $c[1..($c.Length - 1)] }
            $ok = & $exe @args_ -c "import sys; print(int(sys.version_info >= (3, 10)))" 2>$null
            if ($ok -eq "1") { return ,$c }
        } catch {}
    }
    return $null
}
$py = Buscar-Python
if (-not $py) {
    Write-Host $M.py
    winget install -e --id Python.Python.3.12 --scope user --silent
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
    $py = Buscar-Python
    if (-not $py) {
        Write-Host $M.reabre
        exit 1
    }
}

# 3. instala/actualiza Streamlink, yt-dlp, ffmpeg, Whisper y prueba todo
$exe = $py[0]; $args_ = @(); if ($py.Length -gt 1) { $args_ = $py[1..($py.Length - 1)] }
& $exe @args_ (Join-Path $Skill "scripts\clip.py") instalar
