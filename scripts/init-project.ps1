param([string]$ProjectPath = ".")
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path $ProjectPath).Path
$AetherRoot = Split-Path -Parent $PSScriptRoot
$AgentsDir = Join-Path $Root ".agents"
New-Item -ItemType Directory -Force -Path (Join-Path $AgentsDir "agents"),(Join-Path $AgentsDir "rules"),(Join-Path $AgentsDir "skills") | Out-Null
Copy-Item (Join-Path $AetherRoot "templates\workspace\AGENTS.md") (Join-Path $Root "AGENTS.md") -Force:$false
Copy-Item (Join-Path $AetherRoot "adapters\antigravity\rules\aether-engineering.md") (Join-Path $AgentsDir "rules\aether-engineering.md") -Force
Get-ChildItem (Join-Path $AetherRoot "agents") -Filter "*.md" | ForEach-Object { Copy-Item $_.FullName (Join-Path $AgentsDir ("agents\"+$_.Name)) -Force }
Get-ChildItem (Join-Path $AetherRoot "skills") -Directory | ForEach-Object { Copy-Item $_.FullName (Join-Path $AgentsDir ("skills\"+$_.Name)) -Recurse -Force }
$AetherLocal = Join-Path $Root ".aether"
New-Item -ItemType Directory -Force -Path (Join-Path $AetherLocal "memory\private"),(Join-Path $AetherLocal "reports"),(Join-Path $AetherLocal "cache") | Out-Null
$ignore = Join-Path $Root ".gitignore"
$ignoreLines = @(".aether/memory/private/", ".aether/reports/", ".aether/cache/")
if (Test-Path $ignore) {
  $existing = Get-Content $ignore
  foreach ($line in $ignoreLines) { $clean = $line.Trim(); if ($existing -notcontains $clean) { Add-Content $ignore $clean } }
} else {
  Set-Content $ignore ($ignoreLines | ForEach-Object { $_.Trim() })
}
Write-Host "Workspace Aether files initialized in $Root. Review before committing."
