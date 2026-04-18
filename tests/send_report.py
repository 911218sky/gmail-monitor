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

from monitor import fetch_stock, send_telegram

async def send_table_report():
    print("📊 正在抓取當前庫存...")
    stocks = await fetch_stock()
    
    # 使用 Telegram Markdown 表格格式
    msg = f"📊 *庫存報告* `{datetime.now().strftime('%H:%M:%S')}`\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for name, stock in stocks.items():
        # 狀態圖示
        if stock == 0:
            status = "🔴"
        elif stock < 100:
            status = "🟡"
        elif stock < 500:
            status = "🟢"
        else:
            status = "🔵"
        
        # 簡化商品名稱（取關鍵字）
        short_name = name.replace("【", "").replace("】", "").split("(")[0][:25]
        
        msg += f"{status} `{stock:>4}` │ {short_name}\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📦 總計: *{len(stocks)}* 個商品"
    
    print(msg)
    print("\n發送到 Telegram...")
    await send_telegram(msg)
    print("✅ 已發送！")

if __name__ == "__main__":
    asyncio.run(send_table_report())
