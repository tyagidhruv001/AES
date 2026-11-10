param([switch]$EnableHooks)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Config = Join-Path $env:USERPROFILE ".gemini\config"
$Backup = Join-Path $env:USERPROFILE (".gemini\aether-backups\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
$Manifest = Join-Path $Root "scripts\managed-files.json"
New-Item -ItemType Directory -Force -Path (Join-Path $Config "rules"),(Join-Path $Config "agents"),(Join-Path $Config "skills") | Out-Null

function Install-Managed($Source,$Destination) {
    $parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    if (Test-Path $Destination) {
        $relative = $Destination.Substring($env:USERPROFILE.Length).TrimStart('\')
        $backupPath = Join-Path $Backup $relative
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backupPath) | Out-Null
        Copy-Item $Destination $backupPath -Recurse -Force
        Write-Host "Backed up $Destination"
    }
    Copy-Item $Source $Destination -Recurse -Force
    Write-Host "Installed $Destination"
}
Install-Managed (Join-Path $Root "adapters\antigravity\rules\aether-engineering.md") (Join-Path $Config "rules\aether-engineering.md")
Get-ChildItem (Join-Path $Root "agents") -Filter "*.md" | ForEach-Object {
    Install-Managed $_.FullName (Join-Path $Config ("agents\" + $_.Name))
}
Get-ChildItem (Join-Path $Root "skills") -Directory | ForEach-Object {
    Install-Managed $_.FullName (Join-Path $Config ("skills\" + $_.Name))
}
if ($EnableHooks) {
    Write-Warning "Hooks execute local commands. Inspect adapters\antigravity\hooks before enabling."
    $template = Get-Content (Join-Path $Root "adapters\antigravity\hooks\hooks.template.json") -Raw
    $hookCommand = 'python "' + (Join-Path $Root "adapters\antigravity\hooks\safety_gate.py") + '"'
    $template = $template.Replace('python "<AETHER_INSTALL_DIR>/adapters/antigravity/hooks/safety_gate.py"', $hookCommand.Replace('\','\\'))
    $hooksPath = Join-Path $Config "hooks.json"
    if (Test-Path $hooksPath) {
        Copy-Item $hooksPath (Join-Path $Backup "hooks.json") -Force
        Write-Warning "Existing hooks.json backed up. Aether will not merge automatically; review and merge manually."
    } else {
        $template = $template.Replace('"enabled": false','"enabled": true')
        Set-Content -Path $hooksPath -Value $template -Encoding UTF8
        Write-Host "Installed opt-in Aether hook at $hooksPath"
    }
}
Write-Host "`nAether v1.0.0 installed. Restart Antigravity and run scripts\doctor.ps1."
if (Test-Path $Backup) { Write-Host "Backups: $Backup" }
