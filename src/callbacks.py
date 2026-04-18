from telegram import Update
from telegram.ext import ContextTypes


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 inline 按鈕點擊（保留以防萬一）"""
    query = update.callback_query
    await query.answer()
    
    # 這個函數現在不需要了，因為使用指令按鈕
    pass
