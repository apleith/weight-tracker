# Creates Windows Task Scheduler tasks for the weight tracker.
# Run this script once as Administrator:
#   powershell -ExecutionPolicy Bypass -File setup-reminder-task.ps1

$pythonPath = "E:\Projects\apleith\weight-tracker\.venv\Scripts\python.exe"
$workingDir = "E:\Projects\apleith\weight-tracker"

# --- Task 1: Health Log Reminder (8pm daily) ---
$taskName = "HealthLogReminder"
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "run.py remind" `
    -WorkingDirectory $workingDir

$trigger = New-ScheduledTaskTrigger -Daily -At "8:00PM"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Check if health log has been filled today. If not, send ntfy push notification." `
    -RunLevel Limited

Write-Host "Task '$taskName' created. Runs daily at 8:00 PM."

# --- Task 2: Weight Tracker Dashboard on logon (windowless) ---
# Remove old wallpaper-only task if it exists
Unregister-ScheduledTask -TaskName "WeightTrackerWallpaper" -Confirm:$false -ErrorAction SilentlyContinue

$taskName = "WeightTrackerDashboard"
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$pythonwPath = "E:\Projects\apleith\weight-tracker\.venv\Scripts\pythonw.exe"

$action = New-ScheduledTaskAction `
    -Execute $pythonwPath `
    -Argument "run.py all" `
    -WorkingDirectory $workingDir

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Days 365)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Start weight tracker dashboard server, wallpaper generator, and file watcher on logon. Runs windowless via pythonw.exe." `
    -RunLevel Limited

Write-Host "Task '$taskName' created. Runs at every logon (windowless)."
Write-Host ""
Write-Host "Both tasks registered. Test with:"
Write-Host "  .venv\Scripts\python run.py remind"
Write-Host "  .venv\Scripts\pythonw run.py all"
