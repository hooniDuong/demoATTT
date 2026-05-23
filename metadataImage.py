import sys
import webbrowser
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def convert_dms_to_decimal(dms_tuple, ref):
    """Chuyển đổi tọa độ dạng (độ, phút, giây) dạng phân số sang độ thập phân."""
    degrees = dms_tuple[0][0] / dms_tuple[0][1]
    minutes = dms_tuple[1][0] / dms_tuple[1][1]
    seconds = dms_tuple[2][0] / dms_tuple[2][1]
    decimal = degrees + minutes / 60.0 + seconds / 3600.0
    if ref in ('S', 'W'):          # Nam hoặc Tây => giá trị âm
        decimal = -decimal
    return decimal

def extract_gps_coordinates(gps_dict):
    """Trích xuất tọa độ thập phân từ thông tin GPS (nếu có)."""
    lat = lon = None
    # Các tag số theo chuẩn EXIF: 1=LatitudeRef, 2=Latitude, 3=LongitudeRef, 4=Longitude
    lat_ref = gps_dict.get(1)
    lat_dms = gps_dict.get(2)
    lon_ref = gps_dict.get(3)
    lon_dms = gps_dict.get(4)
    if lat_dms and lat_ref and lon_dms and lon_ref:
        lat = convert_dms_to_decimal(lat_dms, lat_ref)
        lon = convert_dms_to_decimal(lon_dms, lon_ref)
    return lat, lon

def main():
    if len(sys.argv) != 2:
        print("Cách dùng: python script.py <đường_dẫn_ảnh>")
        sys.exit(1)

    image_path = sys.argv[1]

    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Không thể mở ảnh: {e}")
        sys.exit(1)

    exif = img._getexif()
    if not exif:
        print("Không tìm thấy metadata EXIF trong ảnh này.")
        return

    print("=== THÔNG TIN METADATA EXIF ===")
    gps_data = None

    for tag_id, value in exif.items():
        tag_name = TAGS.get(tag_id, tag_id)
        if tag_name == "GPSInfo":
            gps_data = value
            print(f"{tag_name}:")
            # In chi tiết từng trường GPS
            for gps_tag_id, gps_val in value.items():
                gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                print(f"    {gps_tag_name}: {gps_val}")
        else:
            print(f"{tag_name}: {value}")

    # Xử lý GPS và mở bản đồ
    if gps_data:
        lat, lon = extract_gps_coordinates(gps_data)
        if lat is not None and lon is not None:
            print(f"\nTọa độ GPS (thập phân): {lat:.6f}, {lon:.6f}")
            maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            print(f"Đang mở Google Maps tại: {maps_url}")
            webbrowser.open(maps_url)
        else:
            print("\nCó thông tin GPS nhưng không phân tích được tọa độ.")
    else:
        print("\nKhông tìm thấy thông tin GPS trong ảnh.")

if __name__ == "__main__":
    main()