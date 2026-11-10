$Base = Join-Path $env:USERPROFILE ".gemini\config"
$rule = Join-Path $Base "rules\aether-engineering.md"
if (Test-Path $rule) { Remove-Item $rule -Force; Write-Host "Removed Aether rule" }
$agents = @("principal-architect","project-planner","senior-developer","debugging-engineer","security-engineer","qa-engineer","independent-reviewer","performance-engineer","devops-engineer")
foreach ($a in $agents) {
  $p = Join-Path $Base ("agents\"+$a+".md")
  if (Test-Path $p) { Remove-Item $p -Force; Write-Host "Removed agent $a" }
}
$skills = @("project-intake","feature-development","code-review","security-audit","debugging","testing","architecture-review","ui-ux-review","research-first","agent-orchestration")
foreach ($s in $skills) {
  $p = Join-Path $Base ("skills\"+$s)
  if (Test-Path $p) { Remove-Item $p -Recurse -Force; Write-Host "Removed skill $s" }
}
Write-Host "Aether-managed files removed. Backups, hooks.json, and unrelated customizations are preserved."
