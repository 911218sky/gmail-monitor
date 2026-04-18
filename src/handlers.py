from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
from telegram.ext import ContextTypes

from config import BOT_TOKEN, ADMIN_PASSWORD, URL
from storage import (
    add_subscriber, remove_subscriber, is_admin, load_admins, save_admins,
    load_config, save_config, load_subscribers, load_previous_stock, save_stock,
    get_user_preference, set_user_preference
)
from scraper import fetch_stock


def get_user_keyboard(is_subscribed=False, is_admin_user=False):
    """取得用戶鍵盤"""
    if is_subscribed:
        keyboard = [
            ["📊 查看報告", "🔍 立即檢查"],
            ["🌐 前往官網", "❓ 幫助"],
            ["❌ 取消訂閱"],
        ]
        if is_admin_user:
            keyboard.insert(2, ["⚙️ 系統狀態", "📢 廣播"])
    else:
        keyboard = [
            ["✅ 訂閱通知"],
            ["📊 查看報告", "🌐 前往官網"],
            ["❓ 幫助"],
        ]
        if is_admin_user:
            keyboard.insert(2, ["⚙️ 系統狀態"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """開始指令"""
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    is_subscribed = chat_id in subscribers
    is_admin_user = is_admin(chat_id)
    
    keyboard = get_user_keyboard(is_subscribed, is_admin_user)
    
    if is_subscribed:
        msg = "🤖 *Gmail 庫存監控 Bot*\n\n✅ 你已訂閱，會自動收到庫存變化通知\n\n使用下方按鈕快速操作"
    else:
        msg = "🤖 *Gmail 庫存監控 Bot*\n\n👋 歡迎使用！點擊下方按鈕開始"
    
    await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """幫助指令"""
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    is_subscribed = chat_id in subscribers
    is_admin_user = is_admin(chat_id)
    
    keyboard = get_user_keyboard(is_subscribed, is_admin_user)
    
    msg = (
        "🤖 *Gmail 庫存監控 Bot*\n\n"
        "📋 *普通用戶指令：*\n\n"
        "/start - 開始使用\n"
        "/subscribe - 訂閱庫存通知\n"
        "/unsubscribe - 取消訂閱\n"
        "/notify - 設定通知偏好\n"
        "/check - 立即檢查庫存\n"
        "/report - 查看完整報告\n"
        "/website - 前往官網\n"
        "/help - 顯示此訊息\n"
    )
    
    if is_admin_user:
        msg += (
            "\n🔐 *管理員指令：*\n\n"
            "/status - 系統狀態\n"
            "/interval <分鐘> - 調整檢查間隔\n"
            "/threshold <數量> - 調整變化閾值\n"
            "/broadcast <訊息> - 廣播訊息\n"
        )
    else:
        msg += "\n🔐 /admin <密碼> - 管理員登入\n"
    
    await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """訂閱指令"""
    chat_id = update.effective_chat.id
    add_subscriber(chat_id)
    
    keyboard = get_user_keyboard(is_subscribed=True, is_admin_user=is_admin(chat_id))
    
    await update.message.reply_text(
        f"✅ 訂閱成功！\n\n你將收到庫存變化通知\nChat ID: `{chat_id}`",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """取消訂閱指令"""
    chat_id = update.effective_chat.id
    remove_subscriber(chat_id)
    
    keyboard = get_user_keyboard(is_subscribed=False, is_admin_user=is_admin(chat_id))
    
    await update.message.reply_text("✅ 已取消訂閱", reply_markup=keyboard)


async def cmd_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """設定通知偏好"""
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    
    if chat_id not in subscribers:
        await update.message.reply_text("❌ 請先訂閱才能設定通知偏好\n使用 /subscribe 訂閱")
        return
    
    if not context.args:
        current = get_user_preference(chat_id)
        pref_text = {"all": "全部通知", "increase": "只接收補貨", "decrease": "只接收減少"}
        await update.message.reply_text(
            f"📢 *當前通知偏好*: {pref_text.get(current, '全部通知')}\n\n"
            f"用法: /notify <類型>\n\n"
            f"可用類型：\n"
            f"• all - 全部通知（增加+減少）\n"
            f"• increase - 只接收補貨通知\n"
            f"• decrease - 只接收減少通知\n\n"
            f"例如: /notify increase",
            parse_mode="Markdown"
        )
        return
    
    preference = context.args[0].lower()
    if preference not in ["all", "increase", "decrease"]:
        await update.message.reply_text("❌ 無效的類型，請使用: all, increase, decrease")
        return
    
    set_user_preference(chat_id, preference)
    pref_text = {"all": "全部通知", "increase": "只接收補貨", "decrease": "只接收減少"}
    await update.message.reply_text(
        f"✅ 通知偏好已設為: *{pref_text[preference]}*",
        parse_mode="Markdown"
    )


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
    
    # 為管理員設定專屬指令選單
    from telegram import BotCommand, BotCommandScopeChat
    admin_commands = [
        BotCommand("start", "開始使用"),
        BotCommand("subscribe", "訂閱庫存通知"),
        BotCommand("unsubscribe", "取消訂閱"),
        BotCommand("notify", "設定通知偏好"),
        BotCommand("check", "立即檢查庫存"),
        BotCommand("report", "查看完整報告"),
        BotCommand("website", "前往官網"),
        BotCommand("status", "系統狀態"),
        BotCommand("interval", "調整檢查間隔"),
        BotCommand("threshold", "調整變化閾值"),
        BotCommand("broadcast", "廣播訊息"),
        BotCommand("help", "顯示幫助訊息"),
    ]
    bot = Bot(token=BOT_TOKEN)
    await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=chat_id))
    
    subscribers = load_subscribers()
    is_subscribed = chat_id in subscribers
    keyboard = get_user_keyboard(is_subscribed, is_admin_user=True)
    
    await update.message.reply_text(
        "✅ *管理員登入成功！*\n\n"
        "🔧 管理員功能已啟用\n"
        "📋 指令選單已更新（輸入 / 查看）\n"
        "⌨️ 鍵盤按鈕已更新\n\n"
        "可用管理功能：\n"
        "• /status - 系統狀態\n"
        "• /interval - 調整檢查間隔\n"
        "• /threshold - 調整變化閾值\n"
        "• /broadcast - 廣播訊息",
        reply_markup=keyboard,
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
    chat_id = update.effective_chat.id
    if not is_admin(chat_id):
        await update.message.reply_text("❌ 此指令僅限管理員使用")
        return
    
    config = load_config()
    subscribers = load_subscribers()
    admins = load_admins()
    
    is_subscribed = chat_id in subscribers
    keyboard = get_user_keyboard(is_subscribed, is_admin_user=True)
    
    await update.message.reply_text(
        f"📊 *系統狀態*\n\n"
        f"⏱ 檢查間隔: *{config['interval']}* 分鐘\n"
        f"📈 變化閾值: *{config.get('threshold', 200)}*\n"
        f"👥 訂閱人數: *{len(subscribers)}*\n"
        f"🔐 管理員數: *{len(admins)}*\n"
        f"🌐 監控網址: {URL}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def cmd_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """調整變化閾值（管理員）"""
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text("❌ 此指令僅限管理員使用")
        return
    
    if not context.args or not context.args[0].isdigit():
        config = load_config()
        await update.message.reply_text(
            f"📊 *當前變化閾值*: {config.get('threshold', 200)}\n\n"
            f"只通知變化超過此數量的商品\n\n"
            f"用法: /threshold <數量>\n例如: /threshold 100",
            parse_mode="Markdown"
        )
        return
    
    threshold = int(context.args[0])
    if threshold < 0:
        await update.message.reply_text("❌ 閾值不能為負數")
        return
    
    config = load_config()
    config["threshold"] = threshold
    save_config(config)
    await update.message.reply_text(
        f"✅ 變化閾值已設為 *{threshold}*\n\n"
        f"現在只會通知變化 ≥{threshold} 的商品",
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
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    is_subscribed = chat_id in subscribers
    is_admin_user = is_admin(chat_id)
    keyboard = get_user_keyboard(is_subscribed, is_admin_user)
    
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
            await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await update.message.reply_text("✅ 無變化", reply_markup=keyboard)
        
        save_stock(current)
    except Exception as e:
        await update.message.reply_text(f"❌ 錯誤: {e}", reply_markup=keyboard)


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看完整庫存報告"""
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    is_subscribed = chat_id in subscribers
    is_admin_user = is_admin(chat_id)
    keyboard = get_user_keyboard(is_subscribed, is_admin_user)
    
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
        await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ 錯誤: {e}", reply_markup=keyboard)


async def cmd_website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """前往官網"""
    await update.message.reply_text(
        f"🌐 *官方網站*\n\n{URL}\n\n點擊連結前往查看商品",
        parse_mode="Markdown"
    )
