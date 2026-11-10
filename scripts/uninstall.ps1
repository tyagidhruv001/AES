# Aether Uninstallation Script (Safe, Idempotent, Symmetric)
$ErrorActionPreference = "Continue"
$Base = Join-Path $env:USERPROFILE ".gemini\config"
Write-Host "Uninstalling Aether Engineering System from $Base..." -ForegroundColor Cyan

# 1. Remove canonical rule
$rule = Join-Path $Base "rules\aether-engineering.md"
if (Test-Path $rule) { Remove-Item $rule -Force; Write-Host "Removed Aether global rule" -ForegroundColor Green }

# 2. Remove managed subagents
$agents = @("principal-architect","project-planner","senior-developer","debugging-engineer","security-engineer","qa-engineer","independent-reviewer","performance-engineer","devops-engineer")
foreach ($a in $agents) {
  $p = Join-Path $Base ("agents\"+$a+".md")
  if (Test-Path $p) { Remove-Item $p -Force; Write-Host "Removed agent $a" -ForegroundColor Green }
}

# 3. Remove managed skills
$skills = @("project-intake","feature-development","code-review","security-audit","debugging","testing","architecture-review","ui-ux-review","research-first","agent-orchestration")
foreach ($s in $skills) {
  $p = Join-Path $Base ("skills\"+$s)
  if (Test-Path $p) { Remove-Item $p -Recurse -Force; Write-Host "Removed skill $s" -ForegroundColor Green }
}

# 4. Clean up Aether hooks from hooks.json safely without touching user hooks
$hooksPath = Join-Path $Base "hooks.json"
if (Test-Path $hooksPath) {
    try {
        $hooksJson = Get-Content $hooksPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($hooksJson.PSObject.Properties['aether-destructive-command-gate']) {
            $hooksJson.PSObject.Properties.Remove('aether-destructive-command-gate')
            $updatedJson = $hooksJson | ConvertTo-Json -Depth 10
            Set-Content -Path $hooksPath -Value $updatedJson -Encoding UTF8
            Write-Host "Removed Aether hook gate from hooks.json (unrelated hooks preserved)." -ForegroundColor Green
        }
    } catch {
        Write-Warning "Could not automatically parse hooks.json; please inspect manually to remove Aether hook reference: $_"
    }
}

Write-Host "`nAether-managed files and hooks removed successfully." -ForegroundColor Cyan
Write-Host "Backups and unrelated custom agents, skills, and rules remain untouched."
