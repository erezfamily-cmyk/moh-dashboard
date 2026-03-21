# הגדרת משימה חוזרת ב-Task Scheduler
# הרץ פעם אחת כמנהל: powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1

$taskName   = "MOH-Dashboard-Refresh"
$scriptPath = "C:\Users\erezf\moh-project\run_scraper.bat"
$logDir     = "C:\Users\erezf\moh-project\logs"

# --- הגדרה: כל כמה דקות לרוץ ---
$intervalMinutes = 30

# Create logs directory
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

# Remove existing task if exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Trigger: התחל עכשיו, חזור כל X דקות, ללא הפסקה
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval  (New-TimeSpan -Minutes $intervalMinutes) `
    -RepetitionDuration  ([TimeSpan]::MaxValue)

# Action
$action = New-ScheduledTaskAction -Execute $scriptPath

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit    (New-TimeSpan -Minutes 8) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances     IgnoreNew

# Register
Register-ScheduledTask `
    -TaskName   $taskName `
    -Trigger    $trigger `
    -Action     $action `
    -Settings   $settings `
    -Description "סריקת דשבורד משרד הבריאות כל $intervalMinutes דקות" `
    -RunLevel   Highest

Write-Host "משימה נוצרה: $taskName" -ForegroundColor Green
Write-Host "תדירות: כל $intervalMinutes דקות" -ForegroundColor Cyan
Write-Host "לבדיקה: Get-ScheduledTask -TaskName '$taskName'"
Write-Host "להרצה מיידית: Start-ScheduledTask -TaskName '$taskName'"
