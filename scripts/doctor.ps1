$Base = Join-Path $env:USERPROFILE ".gemini\config"
Write-Host "Aether v1.0.0 diagnostic" -ForegroundColor Cyan
$rule = Join-Path $Base "rules\aether-engineering.md"
if (Test-Path $rule) { Write-Host "OK global rule" -ForegroundColor Green } else { Write-Host "MISSING global rule" -ForegroundColor Red }
$agents = @("principal-architect","project-planner","senior-developer","debugging-engineer","security-engineer","qa-engineer","independent-reviewer","performance-engineer","devops-engineer")
foreach ($a in $agents) {
  if (Test-Path (Join-Path $Base ("agents\"+$a+".md"))) { Write-Host "OK agent $a" -ForegroundColor Green } else { Write-Host "MISSING agent $a" -ForegroundColor Red }
}
$skills = @("project-intake","feature-development","code-review","security-audit","debugging","testing","architecture-review","ui-ux-review","research-first","agent-orchestration")
foreach ($s in $skills) {
  if (Test-Path (Join-Path $Base ("skills\"+$s+"\SKILL.md"))) { Write-Host "OK skill $s" -ForegroundColor Green } else { Write-Host "MISSING skill $s" -ForegroundColor Red }
}
Write-Host "`nFilesystem presence is not proof of runtime loading or delegation. Verify Customizations and /agents in Antigravity." -ForegroundColor Yellow
