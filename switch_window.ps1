#requires -Version 2

function Show-Process($Process, [Switch]$Maximize)
{
	
  $sig = '
    [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern int SetForegroundWindow(IntPtr hwnd);
	[DllImport("user32.dll")] public static extern int MoveWindow(IntPtr hwnd, int x, int y, int width, int height, bool repaint);
  '
  
  if ($Maximize) { $Mode = 3 } else { $Mode = 4 }
  $type = Add-Type -MemberDefinition $sig -Name WindowAPI -PassThru
  $hwnd = $process.MainWindowHandle
  $null = $type::ShowWindowAsync($hwnd, $Mode)
  $null = $type::SetForegroundWindow($hwnd)  
  $null = $type::MoveWindow($hwnd, 800, 300, 275, 420, $true)
  
}

$param1=$args[0]
Show-Process -Process (Get-Process -Id $param1)#-Maximize
write-host `n"[PS] Window activated for PID:" $param1