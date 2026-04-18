import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 載入 .env
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()

URL = "https://gmailbuy.com/"
DATA_FILE = Path("stock_data.json")
CONFIG_FILE = Path("config.json")
SUBSCRIBERS_FILE = Path("subscribers.json")
ADMINS_FILE = Path("admins.json")
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# 預設檢查間隔（分鐘）
DEFAULT_INTERVAL = 5


def load_previous_stock():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {}


def save_stock(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"interval": DEFAULT_INTERVAL}


def save_config(config):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def load_subscribers():
    if SUBSCRIBERS_FILE.exists():
        return set(json.loads(SUBSCRIBERS_FILE.read_text()))
    return set()


def save_subscribers(subscribers):
    SUBSCRIBERS_FILE.write_text(json.dumps(list(subscribers), indent=2))


def add_subscriber(chat_id):
    subs = load_subscribers()
    subs.add(chat_id)
    save_subscribers(subs)


def remove_subscriber(chat_id):
    subs = load_subscribers()
    subs.discard(chat_id)
    save_subscribers(subs)


def load_admins():
    if ADMINS_FILE.exists():
        return set(json.loads(ADMINS_FILE.read_text()))
    return set()


def save_admins(admins):
    ADMINS_FILE.write_text(json.dumps(list(admins), indent=2))


def is_admin(chat_id):
    return chat_id in load_admins()


async def fetch_stock():
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(URL)
        soup = BeautifulSoup(resp.text, "html.parser")
        stocks = {}
        rows = soup.select("tr")
        for row in rows:
            badge = row.select_one("span.layui-badge.layui-bg-cyan")
            if not badge:
                continue
            name_td = row.select_one("td")
            if name_td:
                name = name_td.get_text(strip=True)
                stock = int(badge.text.strip())
                stocks[name] = stock
        return stocks


async def send_telegram(message):
    if not BOT_TOKEN:
        print(f"[未配置 TG] {message}")
        return
    
    bot = Bot(token=BOT_TOKEN)
    subscribers = load_subscribers()
    
    if not subscribers:
        print(f"[無訂閱者] {message}")
        return
    
    for chat_id in subscribers:
        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"[發送失敗 {chat_id}] {e}")


# Telegram 指令處理
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    is_subscribed = chat_id in subscribers
    is_admin_user = is_admin(chat_id)
    
    if is_subscribed:
        msg = (
            "🤖 *Gmail 庫存監控 Bot*\n\n"
            "✅ 你已訂閱，會自動收到庫存變化通知\n\n"
            "📋 *可用指令：*\n"
            "/check - 立即檢查庫存\n"
            "/report - 完整庫存報告\n"
            "/unsubscribe - 取消訂閱\n"
        )
        if is_admin_user:
            msg += (
                "\n🔐 *管理員指令：*\n"
                "/status - 查看系統狀態\n"
                "/interval <分鐘> - 調整檢查頻率\n"
                "/broadcast <訊息> - 廣播訊息"
            )
    else:
        msg = (
            "🤖 *Gmail 庫存監控 Bot*\n\n"
            "👋 歡迎使用！這個 Bot 會監控 gmailbuy.com 的庫存變化\n\n"
            "📌 *開始使用：*\n"
            "1️⃣ 發送 /subscribe 訂閱通知\n"
            "2️⃣ 有庫存變化時會自動通知你\n\n"
            "📋 *其他指令：*\n"
            "/check - 立即檢查\n"
            "/report - 完整報告\n"
        )
        if not is_admin_user:
            msg += "\n🔐 管理員請使用 /admin <密碼> 登入"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_subscriber(chat_id)
    await update.message.reply_text(
        f"✅ 訂閱成功！\n\n"
        f"你將收到庫存變化通知\n"
        f"Chat ID: `{chat_id}`",
        parse_mode="Markdown"
    )


async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remove_subscriber(chat_id)
    await update.message.reply_text("✅ 已取消訂閱")


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員登入"""
    chat_id = update.effective_chat.id
    
    if not context.args:
        await update.message.reply_text("❌ 用法: /admin <密碼>")
        return
    
    password = context.args[0]
    if password != ADMIN_PASSWORD:
        await update.message.reply_text("❌ 密碼錯誤")
        return
    
    admins = load_admins()
    admins.add(chat_id)
    save_admins(admins)
    
    await update.message.reply_text(
        "✅ *管理員登入成功！*\n\n"
        "🔐 *管理員指令：*\n"
        "/status - 查看系統狀態\n"
        "/interval <分鐘> - 調整檢查頻率\n"
        "/broadcast <訊息> - 廣播給所有訂閱者",
        parse_mode="Markdown"
    )


async def cmd_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員專屬：調整檢查間隔"""
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text("❌ 此指令僅限管理員使用\n使用 /admin <密碼> 登入")
        return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ 用法: /interval <分鐘>\n例如: /interval 10")
        return
    
    minutes = int(context.args[0])
    if minutes < 1:
        await update.message.reply_text("❌ 間隔必須至少 1 分鐘")
        return
    
    config = load_config()
    config["interval"] = minutes
    save_config(config)
    await update.message.reply_text(f"✅ 檢查間隔已設為 *{minutes}* 分鐘", parse_mode="Markdown")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員專屬：查看系統狀態"""
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text("❌ 此指令僅限管理員使用\n使用 /admin <密碼> 登入")
        return
    
    config = load_config()
    subscribers = load_subscribers()
    admins = load_admins()
    
    await update.message.reply_text(
        f"📊 *系統狀態*\n\n"
        f"⏱ 檢查間隔: *{config['interval']}* 分鐘\n"
        f"👥 訂閱人數: *{len(subscribers)}*\n"
        f"🔐 管理員數: *{len(admins)}*\n"
        f"🌐 監控網址: {URL}",
        parse_mode="Markdown"
    )


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員專屬：廣播訊息"""
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text("❌ 此指令僅限管理員使用")
        return
    
    if not context.args:
        await update.message.reply_text("❌ 用法: /broadcast <訊息>")
        return
    
    message = " ".join(context.args)
    subscribers = load_subscribers()
    
    await update.message.reply_text(f"📢 正在發送給 {len(subscribers)} 位訂閱者...")
    
    success = 0
    for chat_id in subscribers:
        try:
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(chat_id=chat_id, text=f"📢 *管理員訊息*\n\n{message}", parse_mode="Markdown")
            success += 1
        except Exception as e:
            print(f"[廣播失敗 {chat_id}] {e}")
    
    await update.message.reply_text(f"✅ 已發送給 {success}/{len(subscribers)} 位訂閱者")


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 正在檢查...")
    try:
        current = await fetch_stock()
        previous = load_previous_stock()
        
        changes = []
        for name, stock in current.items():
            old = previous.get(name)
            if old is not None and old != stock:
                diff = stock - old
                emoji = "📈" if diff > 0 else "📉"
                short_name = name.replace("【", "").replace("】", "").split("(")[0][:25]
                changes.append(f"{emoji} `{old:>4}→{stock:<4}` ({diff:+d}) │ {short_name}")
        
        if changes:
            msg = "🔔 *發現變化*\n━━━━━━━━━━━━━━━━━━━━\n\n"
            msg += "\n".join(changes)
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("✅ 無變化")
        
        save_stock(current)
    except Exception as e:
        await update.message.reply_text(f"❌ 錯誤: {e}")


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 正在生成報告...")
    try:
        stocks = await fetch_stock()
        msg = f"📊 *庫存報告* `{datetime.now().strftime('%H:%M:%S')}`\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for name, stock in stocks.items():
            if stock == 0:
                status = "🔴"
            elif stock < 100:
                status = "🟡"
            elif stock < 500:
                status = "🟢"
            else:
                status = "🔵"
            short_name = name.replace("【", "").replace("】", "").split("(")[0][:25]
            msg += f"{status} `{stock:>4}` │ {short_name}\n"
        
        msg += f"\n━━━━━━━━━━━━━━━━━━━━\n📦 總計: *{len(stocks)}* 個商品"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ 錯誤: {e}")


async def monitor():
    config = load_config()
    interval = config["interval"] * 60  # 轉換為秒
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
            
            changes = []
            for name, stock in current.items():
                old = previous.get(name)
                if old is None:
                    short_name = name.replace("【", "").replace("】", "").split("(")[0][:25]
                    changes.append(f"🆕 `{stock:>4}` │ {short_name}")
                elif old != stock:
                    diff = stock - old
                    emoji = "📈" if diff > 0 else "📉"
                    short_name = name.replace("【", "").replace("】", "").split("(")[0][:25]
                    changes.append(f"{emoji} `{old:>4}→{stock:<4}` ({diff:+d}) │ {short_name}")
            
            if changes:
                msg = f"🔔 *庫存變化* `{datetime.now().strftime('%H:%M:%S')}`\n"
                msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
                msg += "\n".join(changes)
                msg += f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
                msg += f"📊 共 *{len(changes)}* 項變化"
                await send_telegram(msg)
                print(msg)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 無變化")
            
            save_stock(current)
        except Exception as e:
            print(f"[錯誤] {e}")
        
        await asyncio.sleep(interval)


async def run_bot():
    """運行 Telegram Bot 接收指令"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("interval", cmd_interval))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("report", cmd_report))
    
    await app.initialize()
    await app.start()
    
    # 設定 Bot 指令選單
    from telegram import BotCommand
    commands = [
        BotCommand("start", "查看指令列表"),
        BotCommand("subscribe", "訂閱庫存通知"),
        BotCommand("unsubscribe", "取消訂閱"),
        BotCommand("check", "立即檢查庫存"),
        BotCommand("report", "查看完整報告"),
        BotCommand("admin", "管理員登入"),
    ]
    await app.bot.set_my_commands(commands)
    
    await app.updater.start_polling()
    
    # 發送啟動通知給所有訂閱者
    config = load_config()
    subscribers = load_subscribers()
    if subscribers:
        bot = Bot(token=BOT_TOKEN)
        welcome_msg = (
            f"🤖 *監控系統已啟動*\n\n"
            f"⏱ 檢查間隔: *{config['interval']}* 分鐘\n"
            f"🌐 監控網址: {URL}\n\n"
            f"有庫存變化時會自動通知你！\n\n"
            f"指令: /status /check /report /interval"
        )
        for chat_id in subscribers:
            try:
                await bot.send_message(chat_id=chat_id, text=welcome_msg, parse_mode="Markdown")
            except Exception as e:
                print(f"[啟動通知失敗 {chat_id}] {e}")
    
    print(f"[Bot 已啟動] 訂閱者: {len(subscribers)}")
    
    # 同時運行監控
    await monitor()


if __name__ == "__main__":
    asyncio.run(run_bot())