from telegram import Update
from telegram.ext import ContextTypes

from handlers import (
    cmd_help, cmd_subscribe, cmd_unsubscribe,
    cmd_check, cmd_report, cmd_status, cmd_website
)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理文字訊息（按鈕點擊）- 映射到指令"""
    text = update.message.text
    
    # 映射中文按鈕到對應指令
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
        await cmd_website(update, context)
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
    
    # 這個函數現在不需要了，因為使用指令按鈕
    pass
