# Export a DOCX to PDF with Microsoft Word: updates the table of contents and all fields first,
# so the PDF carries the real page numbers.  Usage: powershell -File export_pdf.ps1 <in.docx> <out.pdf>
param([string]$Docx, [string]$Pdf)
$ErrorActionPreference = "Stop"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
  $doc = $word.Documents.Open((Resolve-Path $Docx).Path, $false, $false)
  $doc.Fields.Update() | Out-Null
  foreach ($t in $doc.TablesOfContents) { $t.Update() }
  $doc.Repaginate()
  foreach ($t in $doc.TablesOfContents) { $t.Update() }
  $doc.Save()
  $doc.ExportAsFixedFormat((Join-Path (Resolve-Path (Split-Path $Pdf)).Path (Split-Path $Pdf -Leaf)), 17, $false, 0, 0, 1, 1, 0, $true)
  $doc.Close($false)
} finally { $word.Quit() }
