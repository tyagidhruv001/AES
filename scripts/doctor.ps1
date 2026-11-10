# Aether Diagnostic & Health Check Script
$ErrorActionPreference = "Continue"
$Base = Join-Path $env:USERPROFILE ".gemini\config"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Aether Engineering System (AES) — Diagnostic & Health Check" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# Stage 1: Dependencies Available
# ---------------------------------------------------------------------------
Write-Host "`n[1] Checking Runtime Dependencies:" -ForegroundColor Yellow
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
    $pyVer = python --version 2>&1
    Write-Host "  [OK] Python: $pyVer ($($py.Source))" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Python 3 is not found in PATH" -ForegroundColor Red
}

$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    $gitVer = git --version 2>&1
    Write-Host "  [OK] Git: $gitVer" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Git is not found in PATH" -ForegroundColor Yellow
}

Write-Host "  [OK] PowerShell: $($PSVersionTable.PSVersion)" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Stage 2: Files Installed in Global Configuration
# ---------------------------------------------------------------------------
Write-Host "`n[2] Checking Installed Files in $Base:" -ForegroundColor Yellow
$rule = Join-Path $Base "rules\aether-engineering.md"
if (Test-Path $rule) { Write-Host "  [OK] Global rule: aether-engineering.md" -ForegroundColor Green } else { Write-Host "  [MISSING] Global rule: aether-engineering.md" -ForegroundColor Red }

$agents = @("principal-architect","project-planner","senior-developer","debugging-engineer","security-engineer","qa-engineer","independent-reviewer","performance-engineer","devops-engineer")
$installedAgents = 0
foreach ($a in $agents) {
  $p = Join-Path $Base ("agents\"+$a+".md")
  if (Test-Path $p) { $installedAgents++ } else { Write-Host "  [MISSING] Agent: $a" -ForegroundColor Red }
}
Write-Host "  Installed Agents: $installedAgents / $($agents.Count)" -ForegroundColor $(if ($installedAgents -eq $agents.Count) { "Green" } else { "Yellow" })

$skills = @("project-intake","feature-development","code-review","security-audit","debugging","testing","architecture-review","ui-ux-review","research-first","agent-orchestration")
$installedSkills = 0
foreach ($s in $skills) {
  $p = Join-Path $Base ("skills\"+$s+"\SKILL.md")
  if (Test-Path $p) { $installedSkills++ } else { Write-Host "  [MISSING] Skill: $s" -ForegroundColor Red }
}
Write-Host "  Installed Skills: $installedSkills / $($skills.Count)" -ForegroundColor $(if ($installedSkills -eq $skills.Count) { "Green" } else { "Yellow" })

# ---------------------------------------------------------------------------
# Stage 3: Configuration & Hook Validity
# ---------------------------------------------------------------------------
Write-Host "`n[3] Checking Configuration & Hook Validity:" -ForegroundColor Yellow
$hooksPath = Join-Path $Base "hooks.json"
if (Test-Path $hooksPath) {
    try {
        $hooksJson = Get-Content $hooksPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($hooksJson.PSObject.Properties['aether-destructive-command-gate']) {
            $gate = $hooksJson.'aether-destructive-command-gate'
            $status = if ($gate.enabled) { "ENABLED" } else { "DISABLED" }
            Write-Host "  [OK] Aether Hook Gate configured in hooks.json (Status: $status)" -ForegroundColor Green
        } else {
            Write-Host "  [INFO] Aether Hook Gate not configured in hooks.json (Default safe posture)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  [ERROR] hooks.json is malformed JSON: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  [INFO] hooks.json not present in global config (Hooks disabled by default)" -ForegroundColor Gray
}

# ---------------------------------------------------------------------------
# Stage 4: Runtime Capability Verification
# ---------------------------------------------------------------------------
Write-Host "`n[4] Runtime Capability Status:" -ForegroundColor Yellow
$Root = Split-Path -Parent $PSScriptRoot
$selfTestScript = Join-Path $Root "scripts\self_test.py"
if (Test-Path $selfTestScript) {
    $testOut = python $selfTestScript 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Repository self-test suite: PASSED" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Repository self-test suite reported failures:`n$testOut" -ForegroundColor Red
    }
} else {
    Write-Host "  [INFO] Running outside of Aether source repository" -ForegroundColor Gray
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "NOTE: Filesystem presence does not guarantee Antigravity runtime loading." -ForegroundColor Yellow
Write-Host "Verify active extensions in Antigravity via Customizations menu and '/agents'." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
