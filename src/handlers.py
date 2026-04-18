from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes

from config import BOT_TOKEN, ADMIN_PASSWORD, URL
from storage import (
    add_subscriber, remove_subscriber, is_admin, load_admins, save_admins,
    load_config, save_config, load_subscribers, load_previous_stock, save_stock
)
from scraper import fetch_stock


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """開始指令 - 帶按鈕"""
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    is_subscribed = chat_id in subscribers
    is_admin_user = is_admin(chat_id)
    
    if is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📊 查看報告", callback_data="report")],
            [InlineKeyboardButton("🔍 立即檢查", callback_data="check")],
            [InlineKeyboardButton("❌ 取消訂閱", callback_data="unsubscribe")],
        ]
        if is_admin_user:
            keyboard.append([InlineKeyboardButton("⚙️ 系統狀態", callback_data="status")])
        
        msg = "🤖 *Gmail 庫存監控 Bot*\n\n✅ 你已訂閱，會自動收到庫存變化通知"
    else:
        keyboard = [
            [InlineKeyboardButton("✅ 訂閱通知", callback_data="subscribe")],
            [InlineKeyboardButton("📊 查看報告", callback_data="report")],
            [InlineKeyboardButton("❓ 幫助", callback_data="help")],
        ]
        msg = "🤖 *Gmail 庫存監控 Bot*\n\n👋 歡迎使用！點擊下方按鈕開始"
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """幫助指令"""
    chat_id = update.effective_chat.id
    is_admin_user = is_admin(chat_id)
    
    keyboard = [[InlineKeyboardButton("🏠 返回主選單", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = (
        "🤖 *Gmail 庫存監控 Bot*\n\n"
        "📋 *可用指令：*\n\n"
        "👤 *一般用戶*\n"
        "/start - 開始使用\n"
        "/subscribe - 訂閱庫存通知\n"
        "/check - 立即檢查庫存\n"
        "/report - 查看完整報告\n"
        "/help - 顯示此幫助訊息\n"
    )
    
    if is_admin_user:
        msg += (
            "\n🔐 *管理員*\n"
            "/status - 查看系統狀態\n"
            "/interval <分鐘> - 調整檢查頻率\n"
            "/broadcast <訊息> - 廣播訊息\n"
        )
    else:
        msg += "\n🔐 /admin <密碼> - 管理員登入\n"
    
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """訂閱指令"""
    chat_id = update.effective_chat.id
    add_subscriber(chat_id)
    
    keyboard = [[InlineKeyboardButton("🏠 返回主選單", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ 訂閱成功！\n\n你將收到庫存變化通知\nChat ID: `{chat_id}`",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """取消訂閱指令"""
    chat_id = update.effective_chat.id
    remove_subscriber(chat_id)
    
    keyboard = [[InlineKeyboardButton("🏠 返回主選單", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("✅ 已取消訂閱", reply_markup=reply_markup)


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
    
    keyboard = [[InlineKeyboardButton("⚙️ 系統狀態", callback_data="status")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✅ *管理員登入成功！*\n\n使用 /status 查看系統狀態",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def cmd_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """調整檢查間隔（管理員）"""
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text("❌ 此指令僅限管理員使用")
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
    """查看系統狀態（管理員）"""
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text("❌ 此指令僅限管理員使用")
        return
    
    config = load_config()
    subscribers = load_subscribers()
    admins = load_admins()
    
    keyboard = [[InlineKeyboardButton("🏠 返回主選單", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📊 *系統狀態*\n\n"
        f"⏱ 檢查間隔: *{config['interval']}* 分鐘\n"
        f"👥 訂閱人數: *{len(subscribers)}*\n"
        f"🔐 管理員數: *{len(admins)}*\n"
        f"🌐 監控網址: {URL}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """廣播訊息（管理員）"""
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
    """立即檢查庫存"""
    keyboard = [[InlineKeyboardButton("🏠 返回主選單", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
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
            msg = "🔔 *發現變化*\n━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(changes)
            await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text("✅ 無變化", reply_markup=reply_markup)
        
        save_stock(current)
    except Exception as e:
        await update.message.reply_text(f"❌ 錯誤: {e}", reply_markup=reply_markup)


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看完整庫存報告"""
    keyboard = [[InlineKeyboardButton("🏠 返回主選單", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
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
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ 錯誤: {e}", reply_markup=reply_markup)
