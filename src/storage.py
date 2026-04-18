import json
from config import (
    DATA_FILE, CONFIG_FILE, SUBSCRIBERS_FILE, ADMINS_FILE, DEFAULT_INTERVAL, DEFAULT_THRESHOLD
)

PREFERENCES_FILE = CONFIG_FILE.parent / "preferences.json"


def load_previous_stock():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {}


def save_stock(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load_config():
    if CONFIG_FILE.exists():
        config = json.loads(CONFIG_FILE.read_text())
        # 確保有 threshold 欄位
        if "threshold" not in config:
            config["threshold"] = DEFAULT_THRESHOLD
        return config
    return {"interval": DEFAULT_INTERVAL, "threshold": DEFAULT_THRESHOLD}


def save_config(config):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def load_subscribers():
    if SUBSCRIBERS_FILE.exists():
        return set(json.loads(SUBSCRIBERS_FILE.read_text()))
    return set()


def save_subscribers(subscribers):
    SUBSCRIBERS_FILE.write_text(json.dumps(list(subscribers), indent=2))


def add_subscriber(chat_id):
    subs = load_subscribers()
    subs.add(chat_id)
    save_subscribers(subs)


def remove_subscriber(chat_id):
    subs = load_subscribers()
    subs.discard(chat_id)
    save_subscribers(subs)


def load_admins():
    if ADMINS_FILE.exists():
        return set(json.loads(ADMINS_FILE.read_text()))
    return set()


def save_admins(admins):
    ADMINS_FILE.write_text(json.dumps(list(admins), indent=2))


def is_admin(chat_id):
    return chat_id in load_admins()



def load_preferences():
    """載入用戶通知偏好 {chat_id: 'all'|'increase'|'decrease'}"""
    if PREFERENCES_FILE.exists():
        return json.loads(PREFERENCES_FILE.read_text())
    return {}


def save_preferences(prefs):
    """儲存用戶通知偏好"""
    PREFERENCES_FILE.write_text(json.dumps(prefs, indent=2))


def get_user_preference(chat_id):
    """取得用戶通知偏好，預設為 'all'"""
    prefs = load_preferences()
    return prefs.get(str(chat_id), "all")


def set_user_preference(chat_id, preference):
    """設定用戶通知偏好"""
    prefs = load_preferences()
    prefs[str(chat_id)] = preference
    save_preferences(prefs)
