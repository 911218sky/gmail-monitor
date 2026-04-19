import asyncio
from datetime import datetime
from telegram import Bot

from config import BOT_TOKEN, URL
from storage import load_config, load_subscribers, load_previous_stock, save_stock
from scraper import fetch_stock


async def send_telegram(message, change_type="all"):
    """發送 Telegram 訊息給所有訂閱者
    
    Args:
        message: 訊息內容
        change_type: 變化類型 ('increase', 'decrease', 'all')
    """
    if not BOT_TOKEN:
        print(f"[未配置 TG] {message}")
        return
    
    bot = Bot(token=BOT_TOKEN)
    subscribers = load_subscribers()
    
    if not subscribers:
        print(f"[無訂閱者] {message}")
        return
    
    from storage import get_user_preference
    
    for chat_id in subscribers:
        try:
            # 檢查用戶偏好
            user_pref = get_user_preference(chat_id)
            if user_pref == "all" or user_pref == change_type:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"[發送失敗 {chat_id}] {e}")


async def monitor():
    """主監控循環"""
    config = load_config()
    interval = config["interval"] * 60
    print(f"[啟動] 監控 {URL}，每 {config['interval']} 分鐘檢查一次")
    
    while True:
        try:
            # 重新載入配置（支援動態更新）
            config = load_config()
            new_interval = config["interval"] * 60
            if new_interval != interval:
                interval = new_interval
                print(f"[更新] 檢查間隔改為 {config['interval']} 分鐘")
            
            current = await fetch_stock()
            previous = load_previous_stock()
            threshold = config.get("threshold", 200)
            
            changes = []
            for name, stock in current.items():
                old = previous.get(name)
                if old is None:
                    short_name = name.replace("【", "").replace("】", "")[:30]
                    changes.append(f"🆕 `{stock:>4}` │ {short_name}")
                elif old != stock:
                    diff = stock - old
                    # 只通知變化超過閾值的商品
                    if abs(diff) >= threshold:
                        emoji = "📈" if diff > 0 else "📉"
                        short_name = name.replace("【", "").replace("】", "")[:30]
                        changes.append(f"{emoji} `{old:>4}→{stock:<4}` ({diff:+d}) │ {short_name}")
            
            if changes:
                # 檢查是否有補貨（庫存增加）
                has_restock = any("📈" in change for change in changes)
                has_decrease = any("📉" in change for change in changes)
                
                # 判斷變化類型
                if has_restock and has_decrease:
                    change_type = "all"
                    title = "🔔 *庫存變化（有補貨）*"
                elif has_restock:
                    change_type = "increase"
                    title = "🔔 *庫存變化（有補貨）*"
                else:
                    change_type = "decrease"
                    title = "🔔 *庫存變化*"
                
                msg = f"{title} `{datetime.now().strftime('%H:%M:%S')}`\n"
                msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
                msg += "\n".join(changes)
                msg += f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
                msg += f"📊 共 *{len(changes)}* 項變化"
                await send_telegram(msg, change_type)
                print(msg)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 無變化")
            
            save_stock(current)
        except Exception as e:
            print(f"[錯誤] {e}")
        
        await asyncio.sleep(interval)
