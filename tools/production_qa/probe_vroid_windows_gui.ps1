# Windows GUI readiness probe for VRoid Studio. No installer is downloaded or executed.
$ErrorActionPreference = 'Stop'
$report = [ordered]@{
  target = 'VRoid Studio 2.16.0 GUI readiness'
  runnerOS = [System.Environment]::OSVersion.VersionString
  sessionName = $env:SESSIONNAME
  userInteractive = [Environment]::UserInteractive
  currentProcessSessionId = (Get-Process -Id $PID).SessionId
  desktopName = $null
  displayDevices = @()
  rdpServices = @()
  install = 'NOT_RUN'
  launch = 'NOT_RUN'
  editing = 'NOT_RUN'
  vrmExport = 'NOT_RUN'
  status = 'BLOCKED'
  notes = @()
}
try {
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class TWODesktopProbe {
  [DllImport("user32.dll", SetLastError=true)]
  public static extern IntPtr GetThreadDesktop(uint dwThreadId);
  [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern bool GetUserObjectInformation(IntPtr hObj, int nIndex, System.Text.StringBuilder pvInfo, uint nLength, out uint lpnLengthNeeded);
}
'@
  $h = [TWODesktopProbe]::GetThreadDesktop([TWODesktopProbe]::GetCurrentThreadId())
  $buffer = New-Object System.Text.StringBuilder 256
  [uint32]$needed = 0
  if ([TWODesktopProbe]::GetUserObjectInformation($h, 2, $buffer, 512, [ref]$needed)) { $report.desktopName = $buffer.ToString() }
} catch { $report.notes += "Desktop inspection unavailable: $($_.Exception.GetType().Name)" }
try {
  $report.displayDevices = @(Get-CimInstance Win32_VideoController | ForEach-Object {
    [ordered]@{name=$_.Name; videoMode=$_.VideoModeDescription; driverVersion=$_.DriverVersion}
  })
} catch { $report.notes += "Video device inspection unavailable: $($_.Exception.GetType().Name)" }
try {
  $report.rdpServices = @(Get-Service TermService -ErrorAction Stop | ForEach-Object { [ordered]@{name=$_.Name;status=[string]$_.Status} })
} catch { $report.notes += 'Remote desktop service state unavailable' }
# A service session or virtual display does not prove a usable interactive 3D GUI.
$report.notes += 'No claim of GUI functionality can be made without observed application launch and editor interaction.'
$report.notes += 'Do not install or execute the user-supplied binary until its distribution origin has been independently verified.'
if (-not [Environment]::UserInteractive -or $report.currentProcessSessionId -eq 0) {
  $report.status = 'BLOCKED_NONINTERACTIVE_SESSION'
} else {
  $report.status = 'GUI_SESSION_CANDIDATE_UNVERIFIED'
}
New-Item -ItemType Directory -Force -Path evidence | Out-Null
$report | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 evidence/vroid_windows_gui_readiness.json
Get-Content evidence/vroid_windows_gui_readiness.json
