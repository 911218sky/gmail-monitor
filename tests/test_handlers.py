"""測試 handlers.py 模組"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from handlers import (
    cmd_start, cmd_help, cmd_subscribe, cmd_unsubscribe,
    cmd_notify, cmd_admin, cmd_status, cmd_interval, cmd_threshold,
    cmd_check, cmd_report, cmd_website, cmd_broadcast
)
from storage import add_subscriber, save_admins, save_config


@pytest.mark.unit
@pytest.mark.asyncio
class TestBasicCommands:
    """測試基本指令"""
    
    async def test_cmd_start_new_user(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試新用戶啟動"""
        await cmd_start(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "歡迎" in call_args[0][0] or "Welcome" in call_args[0][0]
    
    async def test_cmd_start_subscribed_user(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試已訂閱用戶啟動"""
        add_subscriber(mock_telegram_update.effective_chat.id)
        await cmd_start(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "已訂閱" in call_args[0][0]
    
    async def test_cmd_help(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試幫助指令"""
        await cmd_help(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "/subscribe" in call_args[0][0]
    
    async def test_cmd_website(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試官網指令"""
        await cmd_website(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        # URL 來自 config.py，不是 mock_env
        assert "http" in call_args[0][0]


@pytest.mark.unit
@pytest.mark.asyncio
class TestSubscriptionCommands:
    """測試訂閱相關指令"""
    
    async def test_cmd_subscribe(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試訂閱指令"""
        await cmd_subscribe(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "訂閱成功" in call_args[0][0] or "成功" in call_args[0][0]
    
    async def test_cmd_unsubscribe(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試取消訂閱指令"""
        add_subscriber(mock_telegram_update.effective_chat.id)
        await cmd_unsubscribe(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "取消" in call_args[0][0]
    
    async def test_cmd_notify_without_subscription(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試未訂閱時設定通知偏好"""
        await cmd_notify(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "訂閱" in call_args[0][0]
    
    async def test_cmd_notify_set_preference(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試設定通知偏好"""
        add_subscriber(mock_telegram_update.effective_chat.id)
        mock_telegram_context.args = ["increase"]
        await cmd_notify(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "補貨" in call_args[0][0] or "increase" in call_args[0][0]
    
    async def test_cmd_notify_invalid_preference(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試無效的通知偏好"""
        add_subscriber(mock_telegram_update.effective_chat.id)
        mock_telegram_context.args = ["invalid"]
        await cmd_notify(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "無效" in call_args[0][0] or "invalid" in call_args[0][0].lower()


@pytest.mark.unit
@pytest.mark.asyncio
class TestAdminCommands:
    """測試管理員指令"""
    
    async def test_cmd_admin_success(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試管理員登入成功"""
        # 從 config 讀取實際密碼
        from config import ADMIN_PASSWORD
        mock_telegram_context.args = [ADMIN_PASSWORD]
        
        with patch("handlers.Bot") as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.set_my_commands = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            await cmd_admin(mock_telegram_update, mock_telegram_context)
            
            mock_telegram_update.message.reply_text.assert_called_once()
            call_args = mock_telegram_update.message.reply_text.call_args
            assert "成功" in call_args[0][0]
    
    async def test_cmd_admin_wrong_password(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試管理員登入失敗"""
        mock_telegram_context.args = ["wrong_password"]
        await cmd_admin(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "錯誤" in call_args[0][0]
    
    async def test_cmd_status_non_admin(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試非管理員查看狀態"""
        await cmd_status(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "管理員" in call_args[0][0]
    
    async def test_cmd_status_admin(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試管理員查看狀態"""
        save_admins({mock_telegram_update.effective_chat.id})
        await cmd_status(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "系統狀態" in call_args[0][0] or "狀態" in call_args[0][0]
    
    async def test_cmd_interval_non_admin(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試非管理員調整間隔"""
        mock_telegram_context.args = ["10"]
        await cmd_interval(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "管理員" in call_args[0][0]
    
    async def test_cmd_interval_admin(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試管理員調整間隔"""
        save_admins({mock_telegram_update.effective_chat.id})
        mock_telegram_context.args = ["10"]
        await cmd_interval(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "10" in call_args[0][0]
    
    async def test_cmd_threshold_admin(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試管理員調整閾值"""
        save_admins({mock_telegram_update.effective_chat.id})
        mock_telegram_context.args = ["100"]
        await cmd_threshold(mock_telegram_update, mock_telegram_context)
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "100" in call_args[0][0]
    
    async def test_cmd_broadcast_admin(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試管理員廣播"""
        save_admins({mock_telegram_update.effective_chat.id})
        add_subscriber(67890)
        mock_telegram_context.args = ["測試", "訊息"]
        
        with patch("handlers.Bot") as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            await cmd_broadcast(mock_telegram_update, mock_telegram_context)
            
            assert mock_telegram_update.message.reply_text.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
class TestStockCommands:
    """測試庫存相關指令"""
    
    async def test_cmd_check(self, mock_env, mock_telegram_update, mock_telegram_context, sample_stock_data):
        """測試檢查庫存"""
        with patch("handlers.fetch_stock", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_stock_data
            
            await cmd_check(mock_telegram_update, mock_telegram_context)
            
            assert mock_telegram_update.message.reply_text.call_count >= 2
    
    async def test_cmd_report(self, mock_env, mock_telegram_update, mock_telegram_context, sample_stock_data):
        """測試查看報告"""
        with patch("handlers.fetch_stock", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_stock_data
            
            await cmd_report(mock_telegram_update, mock_telegram_context)
            
            assert mock_telegram_update.message.reply_text.call_count >= 2
    
    async def test_cmd_check_error(self, mock_env, mock_telegram_update, mock_telegram_context):
        """測試檢查庫存錯誤"""
        with patch("handlers.fetch_stock", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")
            
            await cmd_check(mock_telegram_update, mock_telegram_context)
            
            assert mock_telegram_update.message.reply_text.call_count >= 2
            call_args = mock_telegram_update.message.reply_text.call_args
            assert "錯誤" in call_args[0][0] or "error" in call_args[0][0].lower()
