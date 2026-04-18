#!/usr/bin/env python3
import asyncio
import json
import os
import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()

from monitor import fetch_stock, send_telegram

async def test_notification():
    print("🧪 模擬庫存變化通知...")
    
    # 模擬變化
    changes = [
        "📈 【優質】2fa滿3個月個人Gmail帳號\n   3248 → 3300 (+52)",
        "📉 【優質】滿年個人Gmail帳號\n   429 → 400 (-29)",
        "🆕 【新商品】測試商品\n   庫存: 100"
    ]
    
    from datetime import datetime
    msg = f"🔔 庫存更新 ({datetime.now().strftime('%H:%M:%S')})\n\n" + "\n\n".join(changes)
    
    print(msg)
    print("\n發送到 Telegram...")
    await send_telegram(msg)
    print("✅ 完成！請檢查 Telegram")

if __name__ == "__main__":
    asyncio.run(test_notification())
