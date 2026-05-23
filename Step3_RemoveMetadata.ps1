# Step3_RemoveMetadata.ps1
$demoDir = "C:\MetadataDemo"
$exiftool = "$demoDir\exiftool.exe"
$original = "$demoDir\original_photo.jpg"
$stripped = "$demoDir\stripped_photo.jpg"

Copy-Item $original $stripped -Force

if (Test-Path $exiftool) {
    # Xóa tất cả metadata
    & $exiftool -overwrite_original -all= $stripped
    Write-Host "Đã xóa toàn bộ metadata của stripped_photo.jpg" -ForegroundColor Red
} else {
    Write-Host "exiftool không tìm thấy. Hãy chắc chắn exiftool.exe ở cùng thư mục." -ForegroundColor Yellow
}