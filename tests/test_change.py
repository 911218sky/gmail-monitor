#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()

from monitor import send_telegram

async def test_change_format():
    changes = [
        "📈 `3245→3300` (+55) │ 優質2fa滿3個月個人Gmail",
        "📉 ` 429→ 400` (-29) │ 優質滿年個人Gmail帳號",
        "📈 ` 106→ 150` (+44) │ 優質全新註冊Gmail帳號",
        "📉 `  85→  60` (-25) │ Google商店帳號英國區",
        "🆕 ` 500` │ 新商品測試"
    ]
    
    msg = f"🔔 *庫存變化* `{datetime.now().strftime('%H:%M:%S')}`\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "\n".join(changes)
    msg += f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📊 共 *{len(changes)}* 項變化"
    
    print(msg)
    print("\n發送到 Telegram...")
    await send_telegram(msg)
    print("✅ 已發送！請檢查 Telegram")

if __name__ == "__main__":
    asyncio.run(test_change_format())
