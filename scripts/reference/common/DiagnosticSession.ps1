# External process watcher only. No game scripts, hooks, injection or process control.
function Wait-FFRStudioGameSession {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$GamePath,
          [ValidateRange(0,86400)][int]$StartTimeoutSeconds=0,
          [ValidateRange(100,5000)][int]$PollMilliseconds=500,
          # Windows PowerShell can shorten long process names. Match the prefix,
          # then verify the full executable path before selecting a game.
          [scriptblock]$ProcessQuery={ Get-Process -Name 'FFRS*' -ErrorAction SilentlyContinue },
          [scriptblock]$Pause={ param($Milliseconds) Start-Sleep -Milliseconds $Milliseconds },
          [scriptblock]$UtcNow={ [DateTime]::UtcNow })
    $expected=[IO.Path]::GetFullPath([IO.Path]::Combine($GamePath,'FFRS/Binaries/Win64/FFRS-Win64-Shipping.exe'))
    $waitingSince=(& $UtcNow).ToUniversalTime()
    $message=''
    function Read-GameProcesses {
        foreach ($candidate in @(& $ProcessQuery)) {
            try {
                $path=[IO.Path]::GetFullPath([string]$candidate.Path)
                $start=$candidate.StartTime.ToUniversalTime()
                [pscustomobject]@{Id=[int]$candidate.Id;Executable=$path;Started=$start;Verified=$true}
            } catch {
                # A temporary path/start-time read failure does not prove exit.
                try { [pscustomobject]@{Id=[int]$candidate.Id;Executable=$null;Started=$null;Verified=$false} } catch {}
            }
        }
    }
    Write-Host 'Waiting for Resonance. Launch your selected game normally through Steam.' -ForegroundColor Cyan
    Write-Host 'Keep this window open; it will export after the game closes. Ctrl+C cancels.'
    $watched=$null
    while ($null -eq $watched) {
        $candidatesFound=@(Read-GameProcesses | Where-Object {
            $_.Verified -and $_.Executable.Equals($expected,[StringComparison]::OrdinalIgnoreCase)
        })
        if ($candidatesFound.Count -eq 1) { $watched=$candidatesFound[0]; break }
        if ($candidatesFound.Count -gt 1 -and $message -ne 'multiple') {
            Write-Host 'More than one copy of this game is running. Close the extra copy to select a session.' -ForegroundColor Yellow
            $message='multiple'
        }
        $now=(& $UtcNow).ToUniversalTime()
        if ($StartTimeoutSeconds -gt 0 -and ($now-$waitingSince).TotalSeconds -ge $StartTimeoutSeconds) {
            throw 'Timed out waiting for the selected full-game process. No game files were changed.'
        }
        & $Pause $PollMilliseconds | Out-Null
    }
    $attached=(& $UtcNow).ToUniversalTime()
    Write-Host ('Following Resonance process ' + $watched.Id + '. Close the game when finished.') -ForegroundColor Green
    while ($true) {
        & $Pause $PollMilliseconds | Out-Null
        $states=@(Read-GameProcesses | Where-Object { $_.Id -eq $watched.Id })
        $alive=$false
        foreach ($state in $states) {
            if (-not $state.Verified -or
                ($state.Executable.Equals($expected,[StringComparison]::OrdinalIgnoreCase) -and
                 $state.Started.Ticks -eq $watched.Started.Ticks)) { $alive=$true }
        }
        if (-not $alive) { break }
    }
    $ended=(& $UtcNow).ToUniversalTime()
    Write-Host 'Game closed. Exporting logs and crash reports...' -ForegroundColor Cyan
    [pscustomobject]@{schema=1;processId=$watched.Id;executable=$watched.Executable;
        processStartedUtc=$watched.Started.ToString('o');watcherStartedUtc=$waitingSince.ToString('o');
        attachedUtc=$attached.ToString('o');exitObservedUtc=$ended.ToString('o');
        attachedToExistingSession=($watched.Started -lt $waitingSince);
        pollMilliseconds=$PollMilliseconds;installedGameScripts=$false;processControlled=$false}
}
