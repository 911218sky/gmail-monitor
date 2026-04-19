"""pytest 配置和共用 fixtures"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_data_dir(tmp_path):
    """臨時資料目錄"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def mock_env(monkeypatch, temp_data_dir):
    """模擬環境變數"""
    monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    monkeypatch.setenv("ADMIN_PASSWORD", "test_admin_pass")
    monkeypatch.setenv("URL", "https://example.com")
    
    # 設定資料檔案路徑到臨時目錄
    from pathlib import Path
    monkeypatch.setattr("config.DATA_FILE", temp_data_dir / "stock_data.json")
    monkeypatch.setattr("config.SUBSCRIBERS_FILE", temp_data_dir / "subscribers.json")
    monkeypatch.setattr("config.ADMINS_FILE", temp_data_dir / "admins.json")
    monkeypatch.setattr("config.CONFIG_FILE", temp_data_dir / "config.json")
    
    # 重新載入 storage 模組以使用新路徑
    import importlib
    import storage
    importlib.reload(storage)
    
    return {
        "BOT_TOKEN": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "ADMIN_PASSWORD": "test_admin_pass",
        "URL": "https://example.com",
        "data_dir": temp_data_dir
    }


@pytest.fixture
def sample_stock_data():
    """範例庫存資料"""
    return {
        "【web gmail】企业Edu谷歌账号(短效号.可用1-2天)": 100,
        "【web gmail】企业Edu谷歌账号(混合域名)": 1348,
        "【优质】2fa满3个月个人谷歌Gmail邮箱(链接可用7天.有使用痕迹)": 3244,
        "【优质】满年个人谷歌Gmail邮箱(包谷歌云，适合做piexl成品，家庭组，有使用痕迹)": 428,
        "谷歌商店账号英国区": 85,
    }


@pytest.fixture
def sample_html():
    """範例 HTML 內容"""
    return """
    <html>
        <body>
            <div class="product">
                <h3>【web gmail】企业Edu谷歌账号(短效号.可用1-2天)</h3>
                <span class="stock">100</span>
            </div>
            <div class="product">
                <h3>【优质】2fa满3个月个人谷歌Gmail邮箱</h3>
                <span class="stock">3244</span>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mock_telegram_update():
    """模擬 Telegram Update 物件"""
    update = MagicMock()
    update.effective_chat.id = 12345
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_telegram_context():
    """模擬 Telegram Context 物件"""
    context = MagicMock()
    context.args = []
    return context


@pytest.fixture
def mock_telegram_bot():
    """模擬 Telegram Bot"""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    bot.set_my_commands = AsyncMock()
    return bot


@pytest.fixture
def mock_httpx_client(sample_html):
    """模擬 httpx 客戶端"""
    client = MagicMock()
    response = MagicMock()
    response.text = sample_html
    response.status_code = 200
    client.get = AsyncMock(return_value=response)
    return client


@pytest.fixture(autouse=True)
def reset_storage_files(mock_env):
    """每次測試後重置儲存檔案"""
    yield
    # 清理測試產生的檔案
    data_dir = mock_env["data_dir"]
    for file in data_dir.glob("*.json"):
        file.unlink(missing_ok=True)
