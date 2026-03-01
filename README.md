# Rokoko Vision Automation

Script tự động hóa quá trình upload 1 local video lên Rokoko Vision, download kết quả FBX, và convert sang CSV.

```
Video → Rokoko Vision → FBX → Blender CLI → CSV
```

1. Đăng nhập Rokoko Vision bằng email/password
2. Upload video và chờ Rokoko xử lý motion capture
3. Download file FBX kết quả
4. Dùng Blender CLI convert FBX → CSV


## Yêu cầu

- Python 3.8+
- [Blender](https://www.blender.org/download/) đã cài trên máy
- Tài khoản Rokoko Vision


## Cài đặt

```bash
pip install playwright
playwright install chromium
```


## Cấu hình

### 1. Credentials

Set environment variable trước khi chạy:

```bash
# macOS/Linux
export ROKOKO_EMAIL=your@email.com
export ROKOKO_PASSWORD=yourpassword

# Windows
set ROKOKO_EMAIL=your@email.com
set ROKOKO_PASSWORD=yourpassword
```

### 2. Đường dẫn Blender

Mở file `rokoko_automation.py` và sửa biến `BLENDER_PATH` cho đúng với máy:

```python
# Windows
BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 4.x\blender.exe"

# macOS
BLENDER_PATH = "/Applications/Blender.app/Contents/MacOS/Blender"

# Linux
BLENDER_PATH = "blender"
```


## Sử dụng

```bash
python rokoko_automation.py --video path/to/video.mp4 --output path/to/output.csv
```

### Ví dụ

```bash
python rokoko_automation.py --video recordings/jump.mp4 --output results/jump.csv
```

Khi chạy, script sẽ không mở trình duyệt Chrome (có giao diện) để thực hiện đăng nhập và upload. Sau khi Rokoko xử lý xong, file CSV sẽ được lưu tự động. Để xem quá trình thực hiện, hãy sửa `headless=True` thành `headless=False` trong file `rokoko_automation.py`.


## Định dạng CSV đầu ra

Mỗi hàng tương ứng với 1 frame. Mỗi bone có 10 cột:

| Cột | Ý nghĩa |
|-----|---------|
| `{bone}_loc_x/y/z` | Vị trí (translation) |
| `{bone}_rot_x/y/z/w` | Góc xoay dạng quaternion |
| `{bone}_scale_x/y/z` | Tỉ lệ (scale) |

Ví dụ:

```
frame, Hips_loc_x, Hips_loc_y, Hips_loc_z, Hips_rot_x, ...
1, 0.012, 0.981, -0.003, 0.001, ...
2, 0.013, 0.980, -0.003, 0.001, ...
```


## Lưu ý

- File FBX trung gian (`*_output.fbx`) được lưu cùng thư mục chạy script, có thể xóa sau khi có CSV.
- Thời gian xử lý của Rokoko tùy thuộc vào độ dài video, thường từ 1–15 phút.