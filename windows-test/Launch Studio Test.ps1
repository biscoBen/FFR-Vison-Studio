$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$updater = Join-Path $root 'Update Studio Test.ps1'
$statePath = Join-Path $root 'update-state.json'
if (Test-Path -LiteralPath $statePath) {
    try {
        $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        $candidate = [IO.Path]::GetFullPath((Join-Path $root $state.updater))
        $prefix = [IO.Path]::GetFullPath($root).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
        if ($candidate.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $candidate)) {
            $updater = $candidate
        }
    } catch {
        # Recover using the original bundled updater if the state file is damaged.
    }
}
& $updater -Root $root
