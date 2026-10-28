# Export every slide of a PPTX to PNG and a PDF copy with Microsoft PowerPoint.
# Usage: powershell -File render_pptx.ps1 <deck.pptx> <out_dir>
param([string]$Pptx, [string]$OutDir)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$app = New-Object -ComObject PowerPoint.Application
try {
  $p = (Resolve-Path $Pptx).Path
  $pres = $app.Presentations.Open($p, $true, $false, $false)
  $pres.Export((Resolve-Path $OutDir).Path, "PNG", 1600, 900)
  $pres.SaveAs([System.IO.Path]::ChangeExtension($p, ".pdf"), 32)
  $pres.Close()
} finally { $app.Quit() }
