"""測試 monitor_logic.py 模組"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from monitor_logic import send_telegram, monitor
from storage import add_subscriber, save_stock, set_user_preference


@pytest.mark.unit
@pytest.mark.asyncio
class TestSendTelegram:
    """測試 Telegram 訊息發送"""
    
    async def test_send_telegram_no_subscribers(self, mock_env):
        """測試無訂閱者時發送訊息"""
        with patch("monitor_logic.Bot") as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            await send_telegram("測試訊息")
            
            # 無訂閱者，不應該發送訊息
            mock_bot.send_message.assert_not_called()
    
    async def test_send_telegram_with_subscribers(self, mock_env):
        """測試有訂閱者時發送訊息"""
        add_subscriber(12345)
        add_subscriber(67890)
        
        with patch("monitor_logic.Bot") as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            await send_telegram("測試訊息", "all")
            
            # 應該發送給所有訂閱者
            assert mock_bot.send_message.call_count == 2
    
    async def test_send_telegram_preference_filter(self, mock_env):
        """測試根據偏好過濾訊息"""
        add_subscriber(12345)
        add_subscriber(67890)
        set_user_preference(12345, "increase")
        set_user_preference(67890, "decrease")
        
        with patch("monitor_logic.Bot") as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            # 只發送補貨通知
            await send_telegram("測試訊息", "increase")
            
            # 只有偏好 increase 的用戶應該收到
            assert mock_bot.send_message.call_count == 1
    
    async def test_send_telegram_error_handling(self, mock_env):
        """測試發送錯誤處理"""
        add_subscriber(12345)
        add_subscriber(67890)
        
        with patch("monitor_logic.Bot") as mock_bot_class:
            mock_bot = MagicMock()
            # 第一個用戶發送失敗，第二個成功
            mock_bot.send_message = AsyncMock(side_effect=[Exception("Send failed"), None])
            mock_bot_class.return_value = mock_bot
            
            # 不應該拋出錯誤
            await send_telegram("測試訊息", "all")
            
            assert mock_bot.send_message.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
class TestMonitor:
    """測試監控邏輯"""
    
    async def test_monitor_detects_new_items(self, mock_env, sample_stock_data):
        """測試偵測新商品"""
        add_subscriber(12345)
        
        with patch("monitor_logic.fetch_stock", new_callable=AsyncMock) as mock_fetch, \
             patch("monitor_logic.send_telegram", new_callable=AsyncMock) as mock_send, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            
            # 第一次返回資料，第二次拋出錯誤以結束循環
            mock_fetch.side_effect = [sample_stock_data, Exception("Stop")]
            mock_sleep.side_effect = Exception("Stop")
            
            try:
                await monitor()
            except Exception:
                pass
            
            # 應該發送新商品通知
            assert mock_send.called
    
    async def test_monitor_detects_changes(self, mock_env, sample_stock_data):
        """測試偵測庫存變化"""
        add_subscriber(12345)
        
        # 儲存初始庫存
        save_stock(sample_stock_data)
        
        # 修改庫存
        changed_stock = sample_stock_data.copy()
        changed_stock["【web gmail】企业Edu谷歌账号(短效号.可用1-2天)"] = 500  # 增加 400
        
        with patch("monitor_logic.fetch_stock", new_callable=AsyncMock) as mock_fetch, \
             patch("monitor_logic.send_telegram", new_callable=AsyncMock) as mock_send, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            
            mock_fetch.side_effect = [changed_stock, Exception("Stop")]
            mock_sleep.side_effect = Exception("Stop")
            
            try:
                await monitor()
            except Exception:
                pass
            
            # 應該發送變化通知
            assert mock_send.called
            call_args = mock_send.call_args[0][0]
            assert "📈" in call_args or "補貨" in call_args
    
    async def test_monitor_threshold_filter(self, mock_env, sample_stock_data):
        """測試閾值過濾"""
        add_subscriber(12345)
        save_stock(sample_stock_data)
        
        # 小幅變化（低於閾值）
        changed_stock = sample_stock_data.copy()
        changed_stock["【web gmail】企业Edu谷歌账号(短效号.可用1-2天)"] = 110  # 只增加 10
        
        with patch("monitor_logic.fetch_stock", new_callable=AsyncMock) as mock_fetch, \
             patch("monitor_logic.send_telegram", new_callable=AsyncMock) as mock_send, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            
            mock_fetch.side_effect = [changed_stock, Exception("Stop")]
            mock_sleep.side_effect = Exception("Stop")
            
            try:
                await monitor()
            except Exception:
                pass
            
            # 變化小於閾值，不應該發送通知
            assert not mock_send.called
    
    async def test_monitor_no_changes(self, mock_env, sample_stock_data):
        """測試無變化時不發送通知"""
        add_subscriber(12345)
        save_stock(sample_stock_data)
        
        with patch("monitor_logic.fetch_stock", new_callable=AsyncMock) as mock_fetch, \
             patch("monitor_logic.send_telegram", new_callable=AsyncMock) as mock_send, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            
            mock_fetch.side_effect = [sample_stock_data, Exception("Stop")]
            mock_sleep.side_effect = Exception("Stop")
            
            try:
                await monitor()
            except Exception:
                pass
            
            # 無變化，不應該發送通知
            assert not mock_send.called
    
    async def test_monitor_error_handling(self, mock_env):
        """測試錯誤處理"""
        with patch("monitor_logic.fetch_stock", new_callable=AsyncMock) as mock_fetch, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            
            # 第一次拋出錯誤，第二次正常結束
            mock_fetch.side_effect = [Exception("Network error"), Exception("Stop")]
            mock_sleep.side_effect = [None, Exception("Stop")]
            
            try:
                await monitor()
            except Exception:
                pass
            
            # 應該繼續運行，不會因錯誤而停止
            assert mock_fetch.call_count == 2
    
    async def test_monitor_config_update(self, mock_env, sample_stock_data):
        """測試動態更新配置"""
        from storage import save_config
        
        save_config({"interval": 5, "threshold": 200})
        
        with patch("monitor_logic.fetch_stock", new_callable=AsyncMock) as mock_fetch, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            
            # 在第二次檢查前更新配置
            def update_config_on_second_call(*args):
                if mock_fetch.call_count == 1:
                    save_config({"interval": 10, "threshold": 200})
                if mock_fetch.call_count >= 2:
                    raise Exception("Stop")
                return sample_stock_data
            
            mock_fetch.side_effect = update_config_on_second_call
            mock_sleep.side_effect = [None, Exception("Stop")]
            
            try:
                await monitor()
            except Exception:
                pass
            
            # 應該讀取新配置
            assert mock_fetch.call_count >= 2
