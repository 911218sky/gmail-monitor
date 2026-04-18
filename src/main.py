import asyncio
from telegram import Bot, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN, URL
from storage import load_config, load_subscribers
from handlers import (
    cmd_start, cmd_help, cmd_subscribe, cmd_unsubscribe,
    cmd_admin, cmd_interval, cmd_status, cmd_broadcast,
    cmd_check, cmd_report, cmd_website
)
from callbacks import button_callback
from monitor_logic import monitor


async def run_bot():
    """運行 Telegram Bot"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # 註冊指令處理器
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("interval", cmd_interval))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("website", cmd_website))
    
    # 註冊按鈕回調處理器
    app.add_handler(CallbackQueryHandler(button_callback))
    
    await app.initialize()
    await app.start()
    
    # 設定一般用戶的 Bot 指令選單
    commands = [
        BotCommand("start", "開始使用"),
        BotCommand("subscribe", "訂閱庫存通知"),
        BotCommand("unsubscribe", "取消訂閱"),
        BotCommand("check", "立即檢查庫存"),
        BotCommand("report", "查看完整報告"),
        BotCommand("website", "前往官網"),
        BotCommand("help", "顯示幫助訊息"),
        BotCommand("admin", "管理員登入"),
    ]
    await app.bot.set_my_commands(commands)
    
    # 為已存在的管理員設定專屬指令選單
    from telegram import BotCommandScopeChat
    from storage import load_admins
    admins = load_admins()
    admin_commands = [
        BotCommand("start", "開始使用"),
        BotCommand("subscribe", "訂閱庫存通知"),
        BotCommand("unsubscribe", "取消訂閱"),
        BotCommand("check", "立即檢查庫存"),
        BotCommand("report", "查看完整報告"),
        BotCommand("website", "前往官網"),
        BotCommand("status", "系統狀態"),
        BotCommand("interval", "調整檢查間隔"),
        BotCommand("broadcast", "廣播訊息"),
        BotCommand("help", "顯示幫助訊息"),
    ]
    for admin_id in admins:
        try:
            await app.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception as e:
            print(f"[設定管理員指令失敗 {admin_id}] {e}")
    
    await app.updater.start_polling()
    
    # 發送啟動通知
    config = load_config()
    subscribers = load_subscribers()
    if subscribers:
        bot = Bot(token=BOT_TOKEN)
        welcome_msg = (
            f"🤖 *監控系統已啟動*\n\n"
            f"⏱ 檢查間隔: *{config['interval']}* 分鐘\n"
            f"🌐 監控網址: {URL}\n\n"
            f"有庫存變化時會自動通知你！"
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
