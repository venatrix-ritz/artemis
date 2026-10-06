#!/usr/bin/env python3
"""
Deploy Artemis to AYN Thor (Armada OS) and register it in Steam Game Mode with grid artwork.
Credits:
- Artemis / Moonlight Qt team
- Project Barry / lavachemist / Armada OS
- Apollo Project
"""
import os
import sys
import binascii
from pathlib import Path

try:
    import vdf
except ImportError:
    print("Error: 'vdf' package not found. Install with: pip install vdf")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: 'Pillow' package not found. Install with: pip install Pillow")
    sys.exit(1)

def deploy_steam_integration():
    home = Path(os.path.expanduser("~"))
    steam_userdata = home / ".local" / "share" / "Steam" / "userdata"
    
    if not steam_userdata.exists():
        print(f"Steam userdata directory not found at {steam_userdata}")
        sys.exit(1)

    user_dirs = [d for d in steam_userdata.iterdir() if d.is_dir() and d.name.isdigit() and d.name != "0"]
    if not user_dirs:
        print("No active Steam user profile found in userdata.")
        sys.exit(1)

    user_dir = user_dirs[0]
    config_dir = user_dir / "config"
    grid_dir = config_dir / "grid"
    grid_dir.mkdir(parents=True, exist_ok=True)

    exe_path = "\"/var/home/armada/.local/share/artemis/bin/artemis\""
    app_name = "Artemis"
    target = exe_path + app_name
    crc = binascii.crc32(target.encode("utf-8"))
    appid_unsigned = (crc | 0x80000000) & 0xFFFFFFFF
    appid_signed = appid_unsigned if appid_unsigned < 0x80000000 else appid_unsigned - 0x100000000
    shortcut_id = (appid_unsigned << 32) | 0x02000000

    print(f"Configuring Steam shortcut for {app_name}:")
    print(f"  Profile:          {user_dir.name}")
    print(f"  AppID (unsigned): {appid_unsigned}")
    print(f"  AppID (signed):   {appid_signed}")
    print(f"  Shortcut ID:      {shortcut_id}")

    # 1. Update / create shortcuts.vdf
    shortcuts_file = config_dir / "shortcuts.vdf"
    data = {"shortcuts": {}}
    if shortcuts_file.exists() and shortcuts_file.stat().st_size > 0:
        try:
            with open(shortcuts_file, "rb") as f:
                data = vdf.binary_load(f)
                if "shortcuts" not in data:
                    data["shortcuts"] = {}
        except Exception as e:
            print(f"Warning: Failed reading existing shortcuts.vdf: {e}. Reinitializing.")
            data = {"shortcuts": {}}

    shortcuts = data.get("shortcuts", {})
    artemis_idx = None
    for idx, entry in shortcuts.items():
        if entry.get("AppName") == app_name or entry.get("appid") in (appid_signed, appid_unsigned):
            artemis_idx = idx
            break

    if artemis_idx is None:
        artemis_idx = str(len(shortcuts))

    shortcuts[artemis_idx] = {
        "appid": appid_signed,
        "AppName": app_name,
        "Exe": exe_path,
        "StartDir": "\"/var/home/armada/.local/share/artemis/bin/\"",
        "icon": "/var/home/armada/.local/share/artemis/share/icons/artemis.png",
        "ShortcutPath": "",
        "LaunchOptions": "",
        "IsHidden": 0,
        "AllowDesktopConfig": 1,
        "AllowOverlay": 1,
        "OpenVR": 0,
        "Devkit": 0,
        "DevkitGameID": "",
        "DevkitOverrideAppId": 0,
        "LastPlayTime": 0,
        "FlatpakAppID": "",
        "tags": { "0": "Streaming", "1": "Apollo" }
    }
    data["shortcuts"] = shortcuts

    with open(shortcuts_file, "wb") as f:
        vdf.binary_dump(data, f)
    print(f"Saved shortcuts.vdf at entry index {artemis_idx}")

    # 2. Generate Grid Assets
    icon_src = "/var/home/armada/.local/share/artemis/share/icons/artemis.png"
    if not os.path.exists(icon_src):
        icon_src = str(Path(__file__).resolve().parent / "artemis-black-logo.png")

    logo_img = Image.open(icon_src).convert("RGBA")
    font_bold = "/usr/share/fonts/google-noto/NotoSans-Bold.ttf"
    font_reg = "/usr/share/fonts/google-noto/NotoSans-Regular.ttf"

    def make_gradient(width, height, color1, color2):
        base = Image.new("RGBA", (width, height), color1)
        top = Image.new("RGBA", (width, height), color2)
        mask = Image.new("L", (width, height))
        mask_data = []
        for y in range(height):
            ratio = int(255 * (y / height))
            mask_data.extend([ratio] * width)
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return base

    # Portrait Capsule: 600x900
    capsule = make_gradient(600, 900, (14, 20, 27, 255), (20, 36, 52, 255))
    logo_cap = logo_img.resize((320, 320), Image.Resampling.LANCZOS)
    capsule.paste(logo_cap, ((600 - 320) // 2, 260), logo_cap)
    draw_cap = ImageDraw.Draw(capsule)
    try:
        font_cap = ImageFont.truetype(font_bold, 48)
        font_sub = ImageFont.truetype(font_reg, 22)
        bbox = draw_cap.textbbox((0, 0), "ARTEMIS", font=font_cap)
        tw = bbox[2] - bbox[0]
        draw_cap.text(((600 - tw) // 2, 620), "ARTEMIS", font=font_cap, fill=(240, 246, 252, 255))
        bbox_sub = draw_cap.textbbox((0, 0), "APOLLO & SUNSHINE CLIENT", font=font_sub)
        tw_sub = bbox_sub[2] - bbox_sub[0]
        draw_cap.text(((600 - tw_sub) // 2, 680), "APOLLO & SUNSHINE CLIENT", font=font_sub, fill=(138, 163, 184, 255))
    except Exception:
        pass

    for name in [f"{appid_unsigned}p.png", f"{shortcut_id}p.png"]:
        capsule.save(grid_dir / name)

    # Banner Header: 920x430
    header = make_gradient(920, 430, (14, 20, 27, 255), (20, 36, 52, 255))
    logo_hdr = logo_img.resize((220, 220), Image.Resampling.LANCZOS)
    header.paste(logo_hdr, (100, (430 - 220) // 2), logo_hdr)
    draw_hdr = ImageDraw.Draw(header)
    try:
        font_hdr = ImageFont.truetype(font_bold, 54)
        draw_hdr.text((360, 160), "ARTEMIS", font=font_hdr, fill=(240, 246, 252, 255))
        draw_hdr.text((364, 230), "High-Performance Game Streaming", font=font_sub, fill=(138, 163, 184, 255))
    except Exception:
        pass

    for name in [f"{appid_unsigned}.png", f"{shortcut_id}.png"]:
        header.save(grid_dir / name)

    # Hero Banner: 1920x620
    hero = make_gradient(1920, 620, (10, 14, 20, 255), (18, 30, 46, 255))
    logo_hero = logo_img.resize((340, 340), Image.Resampling.LANCZOS)
    hero.paste(logo_hero, (1400, (620 - 340) // 2), logo_hero)
    for name in [f"{appid_unsigned}_hero.png", f"{shortcut_id}_hero.png"]:
        hero.save(grid_dir / name)

    # Logo Overlay: 800x300 transparent
    logo_overlay = Image.new("RGBA", (800, 300), (0, 0, 0, 0))
    logo_ov = logo_img.resize((180, 180), Image.Resampling.LANCZOS)
    logo_overlay.paste(logo_ov, (40, 60), logo_ov)
    draw_ov = ImageDraw.Draw(logo_overlay)
    try:
        font_ov = ImageFont.truetype(font_bold, 60)
        draw_ov.text((250, 105), "ARTEMIS", font=font_ov, fill=(255, 255, 255, 255))
    except Exception:
        pass

    for name in [f"{appid_unsigned}_logo.png", f"{shortcut_id}_logo.png"]:
        logo_overlay.save(grid_dir / name)

    print("Steam integration and custom grid assets installed successfully.")

if __name__ == "__main__":
    deploy_steam_integration()
