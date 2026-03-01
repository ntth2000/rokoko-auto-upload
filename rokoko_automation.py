"""
Rokoko Vision Automation Script
--------------------------------
1. Đăng nhập Rokoko Vision
2. Upload video
3. Chờ xử lý xong
4. Download file FBX
5. Dùng Blender CLI convert FBX → CSV

Requirements:
    pip install playwright
    playwright install chromium
    Blender đã cài sẵn trên máy

Usage:
    python rokoko_automation.py --video path/to/video.mp4 --output path/to/output.csv
"""

import asyncio
import argparse
import subprocess
import tempfile
import os
from pathlib import Path
from playwright.async_api import async_playwright, Download


ROKOKO_EMAIL    = os.environ.get("ROKOKO_EMAIL", "")
ROKOKO_PASSWORD = os.environ.get("ROKOKO_PASSWORD", "")
ROKOKO_URL      = "https://vision.rokoko.com"

# Đường dẫn đến Blender:
#   Windows : r"C:\Program Files\Blender Foundation\Blender 4.x\blender.exe"
#   macOS   : "/Applications/Blender.app/Contents/MacOS/Blender"
#   Linux   : "blender"
BLENDER_PATH    = "blender"


### Upload lên Rokoko và download fbx
async def upload_and_download_fbx(video_path: str, fbx_output_path: str):
    print("[Upload] Upload video lên Rokoko và download fbx")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print("[1/3] Đang đăng nhập...")
        await page.goto(ROKOKO_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        await page.get_by_role("button", name="Log in").wait_for()
        await page.get_by_role("button", name="Log in").click()
        await page.wait_for_load_state("networkidle")

        await page.fill('input[type="email"]', ROKOKO_EMAIL)
        await page.fill('input[type="password"]', ROKOKO_PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")
        print("    Đăng nhập thành công.")

        print("[2/3] Đang upload video...")
        await page.get_by_role("button", name="Create").click()
        await page.wait_for_timeout(5000)

        await page.get_by_role("button", name="Upload video").click()
        await page.wait_for_timeout(5000)

        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(video_path)
        print("    File đã chọn, đang upload...")

        await page.locator('[role="progressbar"][aria-valuenow="100"]').wait_for(timeout=600_000)
        print("    Upload xong.")

        await page.get_by_role("button", name="Go to preview").click()
        await page.wait_for_timeout(5000)

        await page.get_by_role("button", name="Turn into animation").click()
        print("[3/3] Đang chờ Rokoko xử lý...")

        download_btn = page.get_by_role("button", name="Download")
        await download_btn.wait_for(state="visible", timeout=900_000)
        print("    Xử lý hoàn tất.")

        async with page.expect_download() as download_info:
            await download_btn.click()

        download: Download = await download_info.value
        await download.save_as(fbx_output_path)
        print(f"    FBX đã lưu tại: {fbx_output_path}")

        await browser.close()


### Blender CLI: Convert FBX → CSV
BLENDER_SCRIPT = """\
import bpy, csv, sys

argv = sys.argv
args = argv[argv.index("--") + 1:]
fbx_path = args[0]
csv_path = args[1]

# Import FBX
bpy.ops.import_scene.fbx(filepath=fbx_path)

# Tìm armature (skeleton)
armature = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
if not armature:
    print("ERROR: Không tìm thấy armature trong file FBX.")
    sys.exit(1)

scene = bpy.context.scene

# Xác định frame range
if armature.animation_data and armature.animation_data.action:
    action = armature.animation_data.action
    start_frame = int(action.frame_range[0])
    end_frame   = int(action.frame_range[1])
else:
    start_frame = scene.frame_start
    end_frame   = scene.frame_end

print(f"Frames: {start_frame} -> {end_frame}")
print(f"Bones : {len(armature.pose.bones)}")

# Tạo header CSV
bone_names = [b.name for b in armature.pose.bones]
header = ["frame"]
for name in bone_names:
    for col in ["loc_x","loc_y","loc_z",
                "rot_x","rot_y","rot_z","rot_w",
                "scale_x","scale_y","scale_z"]:
        header.append(f"{name}_{col}")

# Ghi từng frame vào CSV
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)

    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        row = [frame]
        for bone in armature.pose.bones:
            loc, rot, scale = bone.matrix_basis.decompose()
            row.extend([
                loc.x,   loc.y,   loc.z,
                rot.x,   rot.y,   rot.z,   rot.w,
                scale.x, scale.y, scale.z,
            ])
        writer.writerow(row)

print(f"CSV saved: {csv_path}")
"""


def convert_fbx_to_csv(fbx_path: str, csv_path: str):
    """Gọi Blender ở chế độ headless để convert FBX → CSV."""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp.write(BLENDER_SCRIPT)
        tmp_path = tmp.name

    cmd = [
        BLENDER_PATH,
        "--background",
        "--factory-startup",
        "--python", tmp_path,
        "--",
        str(Path(fbx_path).resolve()),
        str(Path(csv_path).resolve()),
    ]

    print(f"\n[Convert] Chạy Blender CLI...")
    result = subprocess.run(cmd, text=True)

    Path(tmp_path).unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"Blender thoát với code {result.returncode}. "
            "Xem log phía trên để biết lỗi."
        )


# ── Main ──────────────────────────────────────────────────────────────────────

async def main(video_path: str, output_csv: str):
    fbx_path = str(Path(video_path).stem) + "_output.fbx"

    await upload_and_download_fbx(video_path, fbx_path)
    convert_fbx_to_csv(fbx_path, output_csv)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rokoko Vision → FBX → CSV")
    parser.add_argument("--video",  required=True, help="Đường dẫn video đầu vào")
    parser.add_argument("--output", required=True, help="Đường dẫn file CSV đầu ra")
    args = parser.parse_args()

    asyncio.run(main(args.video, args.output))