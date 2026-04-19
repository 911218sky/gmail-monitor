"""整合測試 - 測試模組間互動"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from storage import add_subscriber, save_stock, save_config, set_user_preference
from handlers import cmd_subscribe, cmd_check, cmd_report
from monitor_logic import monitor


@pytest.mark.integration
@pytest.mark.asyncio
class TestSubscriptionFlow:
    """測試訂閱流程"""
    
    async def test_subscribe_and_receive_notification(self, mock_env, mock_telegram_update, mock_telegram_context, sample_stock_data):
        """測試訂閱後接收通知"""
        # 1. 用戶訂閱
        await cmd_subscribe(mock_telegram_update, mock_telegram_context)
        
        # 2. 儲存初始庫存
        save_stock(sample_stock_data)
        
        # 3. 庫存變化
        changed_stock = sample_stock_data.copy()
        changed_stock["【web gmail】企业Edu谷歌账号(短效号.可用1-2天)"] = 500
        
        # 4. 監控應該發送通知
        with patch("monitor_logic.fetch_stock", new_callable=AsyncMock) as mock_fetch, \
             patch("monitor_logic.Bot") as mock_bot_class, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            
            mock_bot = MagicMock()
            mock_bot.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            mock_fetch.side_effect = [changed_stock, Exception("Stop")]
            mock_sleep.side_effect = Exception("Stop")
            
            try:
                await monitor()
            except Exception:
                pass
            
            # 應該發送通知給訂閱者
            assert mock_bot.send_message.called
    
    async def test_preference_filtering(self, mock_env, mock_telegram_update, mock_telegram_context, sample_stock_data):
        """測試偏好過濾"""
        # 1. 訂閱並設定只接收補貨通知
        await cmd_subscribe(mock_telegram_update, mock_telegram_context)
        set_user_preference(mock_telegram_update.effective_chat.id, "increase")
        
        # 2. 儲存初始庫存
        save_stock(sample_stock_data)
        
        # 3. 庫存減少
        changed_stock = sample_stock_data.copy()
        changed_stock["【web gmail】企业Edu谷歌账号(短效号.可用1-2天)"] = 0  # 減少
        
        # 4. 不應該收到通知（因為是減少）
        with patch("monitor_logic.fetch_stock", new_callable=AsyncMock) as mock_fetch, \
             patch("monitor_logic.Bot") as mock_bot_class, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            
            mock_bot = MagicMock()
            mock_bot.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            mock_fetch.side_effect = [changed_stock, Exception("Stop")]
            mock_sleep.side_effect = Exception("Stop")
            
            try:
                await monitor()
            except Exception:
                pass
            
            # 不應該發送通知（用戶只要補貨通知）
            assert not mock_bot.send_message.called


@pytest.mark.integration
@pytest.mark.asyncio
class TestCommandIntegration:
    """測試指令整合"""
    
    async def test_check_command_with_real_data(self, mock_env, mock_telegram_update, mock_telegram_context, sample_stock_data):
        """測試檢查指令與實際資料"""
        # 儲存初始庫存
        save_stock(sample_stock_data)
        
        # 模擬庫存變化
        changed_stock = sample_stock_data.copy()
        changed_stock["【web gmail】企业Edu谷歌账号(短效号.可用1-2天)"] = 500
        
        with patch("handlers.fetch_stock", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = changed_stock
            
            await cmd_check(mock_telegram_update, mock_telegram_context)
            
            # 應該顯示變化
            assert mock_telegram_update.message.reply_text.call_count >= 2
            calls = [call[0][0] for call in mock_telegram_update.message.reply_text.call_args_list]
            message = " ".join(calls)
            assert "📈" in message or "變化" in message
    
    async def test_report_command_formatting(self, mock_env, mock_telegram_update, mock_telegram_context, sample_stock_data):
        """測試報告指令格式化"""
        with patch("handlers.fetch_stock", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_stock_data
            
            await cmd_report(mock_telegram_update, mock_telegram_context)
            
            # 檢查報告格式
            assert mock_telegram_update.message.reply_text.call_count >= 2
            calls = [call[0][0] for call in mock_telegram_update.message.reply_text.call_args_list]
            report = " ".join(calls)
            
            # 應該包含商品名稱（修正後不會被截斷）
            assert "web gmail" in report or "企业Edu" in report


@pytest.mark.integration
@pytest.mark.asyncio
class TestEndToEnd:
    """端到端測試"""
    
    async def test_full_monitoring_cycle(self, mock_env, sample_stock_data):
        """測試完整監控週期"""
        # 1. 配置系統
        save_config({"interval": 1, "threshold": 50})
        
        # 2. 添加訂閱者
        add_subscriber(12345)
        add_subscriber(67890)
        set_user_preference(12345, "all")
        set_user_preference(67890, "increase")
        
        # 3. 初始庫存
        save_stock(sample_stock_data)
        
        # 4. 模擬多次庫存變化
        stocks = [
            {**sample_stock_data, "【web gmail】企业Edu谷歌账号(短效号.可用1-2天)": 200},  # 增加 100
            {**sample_stock_data, "【web gmail】企业Edu谷歌账号(短效号.可用1-2天)": 50},   # 減少 150
        ]
        
        with patch("monitor_logic.fetch_stock", new_callable=AsyncMock) as mock_fetch, \
             patch("monitor_logic.Bot") as mock_bot_class, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            
            mock_bot = MagicMock()
            mock_bot.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            # 兩次變化後停止
            mock_fetch.side_effect = stocks + [Exception("Stop")]
            mock_sleep.side_effect = [None, None, Exception("Stop")]
            
            try:
                await monitor()
            except Exception:
                pass
            
            # 應該發送兩次通知
            # 第一次：兩個用戶都收到（補貨）
            # 第二次：只有 12345 收到（減少，67890 只要補貨）
            assert mock_bot.send_message.call_count == 3  # 2 + 1
    
    async def test_error_recovery(self, mock_env, sample_stock_data):
        """測試錯誤恢復"""
        add_subscriber(12345)
        save_stock(sample_stock_data)
        
        with patch("monitor_logic.fetch_stock", new_callable=AsyncMock) as mock_fetch, \
             patch("monitor_logic.Bot") as mock_bot_class, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            
            mock_bot = MagicMock()
            mock_bot.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            # 第一次錯誤，第二次成功，第三次停止
            changed_stock = {**sample_stock_data, "【web gmail】企业Edu谷歌账号(短效号.可用1-2天)": 500}
            mock_fetch.side_effect = [
                Exception("Network error"),
                changed_stock,
                Exception("Stop")
            ]
            mock_sleep.side_effect = [None, None, Exception("Stop")]
            
            try:
                await monitor()
            except Exception:
                pass
            
            # 應該從錯誤中恢復並繼續監控
            assert mock_fetch.call_count == 3
            # 第二次成功後應該發送通知
            assert mock_bot.send_message.called
    
    async def test_concurrent_users(self, mock_env, sample_stock_data):
        """測試多用戶並發"""
        # 添加多個訂閱者
        for i in range(10):
            add_subscriber(10000 + i)
            set_user_preference(10000 + i, ["all", "increase", "decrease"][i % 3])
        
        save_stock(sample_stock_data)
        changed_stock = {**sample_stock_data, "【web gmail】企业Edu谷歌账号(短效号.可用1-2天)": 500}
        
        with patch("monitor_logic.fetch_stock", new_callable=AsyncMock) as mock_fetch, \
             patch("monitor_logic.Bot") as mock_bot_class, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            
            mock_bot = MagicMock()
            mock_bot.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            mock_fetch.side_effect = [changed_stock, Exception("Stop")]
            mock_sleep.side_effect = Exception("Stop")
            
            try:
                await monitor()
            except Exception:
                pass
            
            # 應該發送給符合偏好的用戶
            # all: 4 個, increase: 3 個 (補貨通知)
            assert mock_bot.send_message.call_count == 7
