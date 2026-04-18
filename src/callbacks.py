from telegram import Update
from telegram.ext import ContextTypes

from handlers import (
    cmd_start, cmd_help, cmd_subscribe, cmd_unsubscribe,
    cmd_check, cmd_report, cmd_status
)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理按鈕點擊"""
    query = update.callback_query
    await query.answer()
    
    # 將 callback_query 轉換為類似 message 的格式
    update.message = query.message
    
    data = query.data
    
    if data == "start":
        await cmd_start(update, context)
    elif data == "help":
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
