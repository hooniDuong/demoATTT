import streamlit as st
import subprocess
import json
import os
import tempfile
import pandas as pd

def get_exif_data(file_path, exiftool_path="exiftool"):
    """
    Run exiftool to get metadata.
    Uses -c "%+.6f" to format GPS coordinates to standard decimal numbers for Google Maps.
    """
    try:
        # Xây dựng lệnh exiftool
        cmd = [exiftool_path, "-j", "-c", "%+.6f", file_path]
        
        # Bắt đầu tiến trình
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8' # Hỗ trợ tiếng Việt và các ký tự đặc biệt
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data and len(data) > 0:
                return data[0]
            return None
        else:
            st.error(f"Lỗi khi chạy exiftool: {result.stderr}")
            return None
    except FileNotFoundError:
        st.error(f"❌ Không tìm thấy công cụ '{exiftool_path}'.\n\nVui lòng kiểm tra xem Exiftool đã được cài đặt và thêm vào PATH chưa, hoặc trỏ đúng đường dẫn trong phần Cài đặt.")
        return None
    except Exception as e:
        st.error(f"Đã xảy ra lỗi: {e}")
        return None

# Cấu hình ý nghĩa của các metadata quan trọng
KEY_EXPLANATIONS = {
    "Make": ("Hãng máy ảnh", "Tên nhà sản xuất của thiết bị chụp ảnh."),
    "Model": ("Dòng thiết bị", "Tên cụ thể của dòng máy hoặc điện thoại được sử dụng để chụp."),
    "DateTimeOriginal": ("Ngày giờ chụp", "Thời điểm bức ảnh được chụp lần đầu."),
    "ImageSize": ("Độ phân giải", "Kích thước chiều ngang và dọc của ảnh (Pixels)."),
    "Megapixels": ("Độ phân giải (MP)", "Số triệu điểm ảnh, thể hiện độ sắc nét tổng thể của ảnh."),
    "FNumber": ("Khẩu độ (F-stop)", "Độ mở của ống kính. Chỉ số càng nhỏ, phông nền càng dễ xóa mờ và thu được nhiều ánh sáng hơn."),
    "ExposureTime": ("Tốc độ màn trập", "Thời gian cảm biến nhận ánh sáng. Tốc độ cao giúp bắt dính chuyển động, tốc độ thấp giúp chụp ban đêm sáng hơn."),
    "ISO": ("Độ nhạy sáng (ISO)", "Khả năng nhạy sáng của cảm biến. ISO cao giúp chụp trong tối tốt nhưng dễ bị nhiễu hạt (noise)."),
    "FocalLength": ("Tiêu cự", "Độ dài tiêu cự ống kính. Số nhỏ là góc rộng (chụp phong cảnh), số lớn là tele (chụp xa, chân dung)."),
    "LensModel": ("Ống kính", "Loại ống kính đã được sử dụng."),
    "Software": ("Phần mềm", "Phần mềm được sử dụng để tạo, xử lý hoặc chỉnh sửa ảnh.")
}

def main():
    st.set_page_config(page_title="Image Metadata Hub", page_icon="📸", layout="wide")
    
    # Tiêu đề ứng dụng
    st.title("📸 Image Metadata Hub")
    st.markdown("Trích xuất và giải thích các thông số quan trọng (Metadata/Exif) của bức ảnh.")
    
    # Sidebar: Cài đặt và Hướng dẫn
    with st.sidebar:
        st.header("⚙️ Cài đặt")
        exiftool_path = st.text_input(
            "Đường dẫn Exiftool", 
            value="exiftool",
            help="Nếu Exiftool đã nằm trong PATH, bạn chỉ cần để là 'exiftool'. Nếu chưa, hãy dán đường dẫn tuyệt đối đến file exiftool.exe (VD: C:\\Users\\Name\\Downloads\\exiftool(-k).exe)"
        )
        
        st.markdown("---")
        st.markdown(
            """
            **Hướng dẫn sử dụng:**
            1. Tại phần giao diện chính, bấm Browse files hoặc kéo thả ảnh vào khung.
            2. Hệ thống sẽ kết nối với Exiftool để trích xuất dữ liệu.
            3. Thông tin chi tiết, giải nghĩa và vị trí GPS sẽ hiện lên.
            """
        )

    # Main Area: Upload file
    uploaded_file = st.file_uploader("📂 Tải lên một bức ảnh...", type=["jpg", "jpeg", "png", "heic", "tiff", "webp"])
    
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.image(uploaded_file, caption="Ảnh đã chọn", use_container_width=True)
            
        with col2:
            st.subheader("📊 Kết quả Phân tích")
            
            with st.spinner("Đang xử lý dữ liệu với Exiftool..."):
                # Lưu file tạm để Exiftool có thể đọc từ disk
                ext = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Gọi Exiftool
                metadata = get_exif_data(tmp_file_path, exiftool_path)
                
                # Xóa file tạm
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
                
                if metadata:
                    # ----------------------------
                    # 1. Phân tích GPS
                    # ----------------------------
                    st.markdown("### 📍 Vị trí (GPS)")
                    gps_lat = metadata.get("GPSLatitude")
                    gps_lon = metadata.get("GPSLongitude")
                    
                    if gps_lat and gps_lon:
                        try:
                            # Parse chuỗi format (ví dụ: "+21.026481" -> 21.026481)
                            # Exiftool có thể trả về string có kèm chữ N, S, E, W tùy cấu hình, nhưng ta đã ép dùng -c "%+.6f"
                            # Trong trường hợp fallback (do Exiftool bản cũ không xử lý hoàn hảo -c), thay thế các ký tự phụ
                            lat_str = str(gps_lat).replace("+", "").replace(" N", "").replace(" S", "-").strip()
                            lon_str = str(gps_lon).replace("+", "").replace(" E", "").replace(" W", "-").strip()
                            
                            lat_val = float(lat_str)
                            lon_val = float(lon_str)
                            
                            # Hiển thị Link Google Maps
                            google_maps_url = f"https://www.google.com/maps/search/?api=1&query={lat_val},{lon_val}"
                            st.success(f"Phát hiện dữ liệu GPS: **{lat_val}, {lon_val}**")
                            st.markdown(f"[🌍 **Bấm vào đây để xem vị trí trên Google Maps**]({google_maps_url})")
                            
                            # Vẽ bản đồ nhỏ trên giao diện
                            st.map(pd.DataFrame({'lat': [lat_val], 'lon': [lon_val]}), zoom=12)
                            
                        except ValueError:
                            st.warning(f"Có thông tin GPS nhưng định dạng không được hỗ trợ để mở map: {gps_lat}, {gps_lon}")
                    else:
                        st.info("Không (Ảnh không chứa dữ liệu GPS)")
                        
                    st.markdown("---")
                    
                    # ----------------------------
                    # 2. Các thông số máy ảnh quan trọng
                    # ----------------------------
                    st.markdown("### 📷 Thông số quan trọng")
                    
                    found_important_keys = False
                    for key, (label, explanation) in KEY_EXPLANATIONS.items():
                        if key in metadata:
                            found_important_keys = True
                            value = metadata[key]
                            with st.expander(f"**{label}:** {value}"):
                                st.write(f"👉 *Ý nghĩa:* {explanation}")
                                
                    if not found_important_keys:
                        st.info("Không tìm thấy thông số máy ảnh cơ bản nào trong bức ảnh này.")

                    st.markdown("---")

                    # ----------------------------
                    # 3. Tất cả siêu dữ liệu thô
                    # ----------------------------
                    with st.expander("🔍 Xem toàn bộ dữ liệu Exif thô (Raw Data)"):
                        st.json(metadata)

if __name__ == "__main__":
    main()
