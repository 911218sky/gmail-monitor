#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 載入 .env
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()

from monitor import fetch_stock, send_telegram

async def test():
    print("🧪 測試 1: 抓取庫存資料...")
    stocks = await fetch_stock()
    print(f"✅ 成功抓取 {len(stocks)} 個商品")
    for name, count in list(stocks.items())[:3]:
        print(f"   {name}: {count}")
    
    print("\n🧪 測試 2: 發送 Telegram 訊息...")
    await send_telegram(f"✅ 監控系統測試成功！\n\n目前共監控 {len(stocks)} 個商品")
    print("✅ 訊息已發送，請檢查 Telegram")

if __name__ == "__main__":
    asyncio.run(test())
