import sys
import subprocess
import webbrowser
import json
import re

def get_metadata_with_exiftool(image_path, exiftool_path="exiftool"):
    """Gọi exiftool, lấy metadata dạng JSON."""
    try:
        result = subprocess.run(
            [exiftool_path, "-j", image_path],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        if data:
            return data[0]
        else:
            return {}
    except Exception as e:
        print(f"Lỗi khi gọi ExifTool: {e}")
        return {}

def extract_gps_from_exiftool(metadata):
    """Trích xuất tọa độ thập phân từ metadata của ExifTool."""
    # ExifTool trả về GPS Latitude, GPS Longitude dạng "21 deg 1' 49.49\" N"
    lat_str = metadata.get("GPS Latitude")
    lon_str = metadata.get("GPS Longitude")
    if not lat_str or not lon_str:
        return None, None
    
    def dms_to_decimal(dms_str):
        # Ví dụ: "21 deg 1' 49.49\" N"
        parts = re.split(r"[°'\" ]+", dms_str.strip())
        # parts: ['21', 'deg', '1', '49.49', 'N']
        try:
            deg = float(parts[0])
            minutes = float(parts[2])
            seconds = float(parts[3])
            direction = parts[4]
        except:
            return None
        decimal = deg + minutes/60.0 + seconds/3600.0
        if direction in ('S', 'W'):
            decimal = -decimal
        return decimal
    
    lat = dms_to_decimal(lat_str)
    lon = dms_to_decimal(lon_str)
    return lat, lon

def main():
    if len(sys.argv) != 2:
        print("Cách dùng: python exif_viewer.py <đường_dẫn_ảnh>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Lấy metadata bằng ExifTool
    metadata = get_metadata_with_exiftool(image_path)
    if not metadata:
        print("Không thể đọc metadata từ ảnh. Hãy kiểm tra đường dẫn hoặc cài ExifTool.")
        return
    
    print("\n=== TOÀN BỘ METADATA (ExifTool) ===\n")
    for key, value in metadata.items():
        # Bỏ qua các trường binary dài
        if isinstance(value, str) and len(value) > 200 and "Binary data" not in key:
            value = value[:200] + "..."
        print(f"{key}: {value}")
    
    # Trích xuất GPS và mở map
    lat, lon = extract_gps_from_exiftool(metadata)
    if lat is not None and lon is not None:
        print(f"\n✅ Tọa độ GPS: {lat:.6f}, {lon:.6f}")
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        print(f"🗺️  Mở Google Maps...")
        webbrowser.open(maps_url)
    else:
        print("\n❌ Không tìm thấy GPS trong metadata.")

if __name__ == "__main__":
    main()