import json
from config import (
    DATA_FILE, CONFIG_FILE, SUBSCRIBERS_FILE, ADMINS_FILE, DEFAULT_INTERVAL
)


def load_previous_stock():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {}


def save_stock(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"interval": DEFAULT_INTERVAL}


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
