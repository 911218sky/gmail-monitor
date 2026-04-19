"""測試 storage.py 模組"""
import json
import pytest
from pathlib import Path

from storage import (
    load_previous_stock, save_stock,
    load_config, save_config,
    load_subscribers, save_subscribers, add_subscriber, remove_subscriber,
    load_admins, save_admins, is_admin,
    load_preferences, save_preferences, get_user_preference, set_user_preference
)


@pytest.mark.unit
class TestStockStorage:
    """測試庫存儲存功能"""
    
    def test_load_previous_stock_empty(self, mock_env):
        """測試載入空的庫存資料"""
        stock = load_previous_stock()
        assert stock == {}
    
    def test_save_and_load_stock(self, mock_env, sample_stock_data):
        """測試儲存和載入庫存資料"""
        save_stock(sample_stock_data)
        loaded = load_previous_stock()
        assert loaded == sample_stock_data
    
    def test_save_stock_overwrites(self, mock_env, sample_stock_data):
        """測試儲存會覆蓋舊資料"""
        save_stock({"test": 100})
        save_stock(sample_stock_data)
        loaded = load_previous_stock()
        assert loaded == sample_stock_data
        assert "test" not in loaded


@pytest.mark.unit
class TestConfigStorage:
    """測試配置儲存功能"""
    
    def test_load_config_default(self, mock_env):
        """測試載入預設配置"""
        config = load_config()
        assert config["interval"] == 5
        assert "threshold" in config
    
    def test_save_and_load_config(self, mock_env):
        """測試儲存和載入配置"""
        new_config = {"interval": 10, "threshold": 300}
        save_config(new_config)
        loaded = load_config()
        assert loaded["interval"] == 10
        assert loaded["threshold"] == 300
    
    def test_config_persistence(self, mock_env):
        """測試配置持久化"""
        save_config({"interval": 15})
        config1 = load_config()
        config2 = load_config()
        assert config1 == config2


@pytest.mark.unit
class TestSubscriberStorage:
    """測試訂閱者儲存功能"""
    
    def test_load_subscribers_empty(self, mock_env):
        """測試載入空的訂閱者列表"""
        subscribers = load_subscribers()
        assert subscribers == set()
    
    def test_add_subscriber(self, mock_env):
        """測試添加訂閱者"""
        add_subscriber(12345)
        subscribers = load_subscribers()
        assert 12345 in subscribers
    
    def test_add_duplicate_subscriber(self, mock_env):
        """測試添加重複訂閱者"""
        add_subscriber(12345)
        add_subscriber(12345)
        subscribers = load_subscribers()
        assert len(subscribers) == 1
    
    def test_remove_subscriber(self, mock_env):
        """測試移除訂閱者"""
        add_subscriber(12345)
        add_subscriber(67890)
        remove_subscriber(12345)
        subscribers = load_subscribers()
        assert 12345 not in subscribers
        assert 67890 in subscribers
    
    def test_remove_nonexistent_subscriber(self, mock_env):
        """測試移除不存在的訂閱者"""
        remove_subscriber(99999)  # 不應該拋出錯誤
        subscribers = load_subscribers()
        assert 99999 not in subscribers


@pytest.mark.unit
class TestAdminStorage:
    """測試管理員儲存功能"""
    
    def test_load_admins_empty(self, mock_env):
        """測試載入空的管理員列表"""
        admins = load_admins()
        assert admins == set()
    
    def test_save_and_load_admins(self, mock_env):
        """測試儲存和載入管理員"""
        admin_set = {12345, 67890}
        save_admins(admin_set)
        loaded = load_admins()
        assert loaded == admin_set
    
    def test_is_admin(self, mock_env):
        """測試檢查管理員身份"""
        save_admins({12345})
        assert is_admin(12345) is True
        assert is_admin(67890) is False


@pytest.mark.unit
class TestPreferencesStorage:
    """測試偏好設定儲存功能"""
    
    def test_load_preferences_empty(self, mock_env):
        """測試載入空的偏好設定"""
        prefs = load_preferences()
        assert prefs == {}
    
    def test_get_user_preference_default(self, mock_env):
        """測試取得預設偏好"""
        pref = get_user_preference(12345)
        assert pref == "all"
    
    def test_set_and_get_user_preference(self, mock_env):
        """測試設定和取得用戶偏好"""
        set_user_preference(12345, "increase")
        pref = get_user_preference(12345)
        assert pref == "increase"
    
    def test_multiple_user_preferences(self, mock_env):
        """測試多個用戶的偏好設定"""
        set_user_preference(12345, "increase")
        set_user_preference(67890, "decrease")
        set_user_preference(11111, "all")
        
        assert get_user_preference(12345) == "increase"
        assert get_user_preference(67890) == "decrease"
        assert get_user_preference(11111) == "all"
    
    def test_update_user_preference(self, mock_env):
        """測試更新用戶偏好"""
        set_user_preference(12345, "increase")
        set_user_preference(12345, "decrease")
        pref = get_user_preference(12345)
        assert pref == "decrease"
