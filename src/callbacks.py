from telegram import Update
from telegram.ext import ContextTypes

from handlers import (
    cmd_help, cmd_subscribe, cmd_unsubscribe,
    cmd_check, cmd_report, cmd_status
)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理文字訊息（按鈕點擊）"""
    text = update.message.text
    
    if text == "✅ 訂閱通知":
        await cmd_subscribe(update, context)
    elif text == "❌ 取消訂閱":
        await cmd_unsubscribe(update, context)
    elif text == "📊 查看報告":
        await cmd_report(update, context)
    elif text == "🔍 立即檢查":
        await cmd_check(update, context)
    elif text == "❓ 幫助":
        await cmd_help(update, context)
    elif text == "⚙️ 系統狀態":
        await cmd_status(update, context)
    elif text == "🌐 前往官網":
        from config import URL
        await update.message.reply_text(
            f"🌐 *官方網站*\n\n{URL}\n\n點擊連結前往查看商品",
            parse_mode="Markdown"
        )
    elif text == "📢 廣播":
        await update.message.reply_text(
            "📢 *廣播訊息*\n\n"
            "使用指令: /broadcast <訊息內容>\n\n"
            "例如: /broadcast 系統將於今晚維護",
            parse_mode="Markdown"
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 inline 按鈕點擊（保留以防萬一）"""
    query = update.callback_query
    await query.answer()
    update.message = query.message
    
    data = query.data
    if data == "help":
        await cmd_help(update, context)
    elif data == "subscribe":
        await cmd_subscribe(update, context)
    elif data == "unsubscribe":
        await cmd_unsubscribe(update, context)
    elif data == "check":
        await cmd_check(update, context)
    elif data == "report":
        await cmd_report(update, context)
    elif data == "status":
        await cmd_status(update, context)
