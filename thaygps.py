import piexif
try:
    from PIL import Image
except ImportError:
    raise ImportError("Pillow is required to run this script. Install it with: pip install Pillow")
import math

def to_deg(value, loc):
    """Chuyển đổi tọa độ thập phân sang định dạng độ/phút/giây của EXIF"""
    if value < 0:
        loc = loc  # giữ nguyên 'S' hoặc 'W'
        value = abs(value)
    else:
        loc = loc
    deg = int(value)
    min_float = (value - deg) * 60
    minutes = int(min_float)
    seconds = (min_float - minutes) * 60
    return ((deg, 1), (minutes, 1), (int(seconds * 100), 100)), loc

# === THAY ĐỔI TỌA ĐỘ CỦA BẠN VÀO ĐÂY ===
latitude = 21.028511   # ví dụ: vĩ độ Hà Nội (21°01'42.6"N)
longitude = 105.804817 # kinh độ Hà Nội (105°48'17.3"E)
# =====================================

# Chuyển đổi tọa độ
lat_deg, lat_ref = to_deg(latitude, "N" if latitude >= 0 else "S")
lon_deg, lon_ref = to_deg(longitude, "E" if longitude >= 0 else "W")

# Tạo dict GPS cho EXIF
gps_ifd = {
    piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
    piexif.GPSIFD.GPSLatitudeRef: lat_ref,
    piexif.GPSIFD.GPSLatitude: lat_deg,
    piexif.GPSIFD.GPSLongitudeRef: lon_ref,
    piexif.GPSIFD.GPSLongitude: lon_deg,
}

# Mở ảnh và gắn GPS
img_path = "Image.jpg"
try:
    # Đọc exif hiện tại (nếu có)
    exif_dict = piexif.load(img_path)
except:
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

# Ghi đè phần GPS
exif_dict["GPS"] = gps_ifd

# Chuyển đổi exif_dict thành bytes
exif_bytes = piexif.dump(exif_dict)

# Lưu ảnh với exif mới
img = Image.open(img_path)
img.save("Image_with_GPS.jpg", exif=exif_bytes)
print("Đã thêm GPS thành công! Ảnh mới: Image_with_GPS.jpg")