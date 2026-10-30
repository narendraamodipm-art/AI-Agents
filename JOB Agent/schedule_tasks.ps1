# Registers two Windows scheduled tasks for the GCC Job Agent (runs only while you're logged in):
#   9:00 every day          → agent.py run       (find + score + Telegram shortlist)
#   every 15 min, 7am–11pm  → agent.py replies   (act on APPLY / SKIP replies)
# Run:     powershell -ExecutionPolicy Bypass -File "JOB Agent\schedule_tasks.ps1"
# Remove:  Unregister-ScheduledTask -TaskName "GCC Job Agent*" -Confirm:$false

$bat = Join-Path $PSScriptRoot "run_agent.bat"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName "GCC Job Agent - daily run" -Force -Settings $settings `
    -Action (New-ScheduledTaskAction -Execute $bat -Argument "run") `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 9:00am) | Out-Null

$repeat = New-ScheduledTaskTrigger -Once -At 7:00am -RepetitionInterval (New-TimeSpan -Minutes 15) `
    -RepetitionDuration (New-TimeSpan -Hours 16)
$trigger = New-ScheduledTaskTrigger -Daily -At 7:00am
$trigger.Repetition = $repeat.Repetition
Register-ScheduledTask -TaskName "GCC Job Agent - Telegram replies" -Force -Settings $settings `
    -Action (New-ScheduledTaskAction -Execute $bat -Argument "replies") -Trigger $trigger | Out-Null

Get-ScheduledTask -TaskName "GCC Job Agent*" |
    Select-Object TaskName, State, @{n = "NextRun"; e = { (Get-ScheduledTaskInfo $_).NextRunTime } } |
    Format-Table -AutoSize
