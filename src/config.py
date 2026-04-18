import os
from pathlib import Path

# 載入 .env
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()

# 網站配置
URL = "https://gmailbuy.com/"

# 文件路徑
DATA_FILE = Path("stock_data.json")
CONFIG_FILE = Path("config.json")
SUBSCRIBERS_FILE = Path("subscribers.json")
ADMINS_FILE = Path("admins.json")

# Telegram 配置
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# 預設檢查間隔（分鐘）
DEFAULT_INTERVAL = 5

# 預設變化閾值（只通知變化超過此數量的商品）
DEFAULT_THRESHOLD = 200
