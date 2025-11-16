# PowerShell pre-commit wrapper
Param([String[]]$Args)

# Determine CPU count on Windows
$jobs = $env:NUMBER_OF_PROCESSORS
if ([String]::IsNullOrEmpty($jobs)) { $jobs = 4 }

# Build args: run pre-commit for pre-commit stage with job count
$argList = @('--hook-stage', 'pre-commit', '-j', $jobs) + $Args

# Execute pre-commit and propagate exit code
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'pre-commit'
$psi.Arguments = ($argList -join ' ')
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false

$proc = [System.Diagnostics.Process]::Start($psi)
$proc.WaitForExit()
exit $proc.ExitCode
