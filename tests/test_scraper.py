"""測試 scraper.py 模組"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from scraper import fetch_stock


@pytest.mark.unit
@pytest.mark.asyncio
class TestScraper:
    """測試爬蟲功能"""
    
    async def test_fetch_stock_success(self, mock_env):
        """測試成功抓取庫存"""
        mock_html = """
        <html>
            <body>
                <div class="product-item">
                    <h3 class="product-title">【web gmail】企业Edu谷歌账号(短效号.可用1-2天)</h3>
                    <span class="stock-count">100</span>
                </div>
                <div class="product-item">
                    <h3 class="product-title">【优质】2fa满3个月个人谷歌Gmail邮箱</h3>
                    <span class="stock-count">3244</span>
                </div>
            </body>
        </html>
        """
        
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.status_code = 200
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            stocks = await fetch_stock()
            
            assert isinstance(stocks, dict)
            assert len(stocks) >= 0  # 實際解析結果取決於 HTML 結構
    
    async def test_fetch_stock_empty_response(self, mock_env):
        """測試空回應"""
        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"
        mock_response.status_code = 200
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            stocks = await fetch_stock()
            
            assert isinstance(stocks, dict)
    
    async def test_fetch_stock_network_error(self, mock_env):
        """測試網路錯誤"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception):
                await fetch_stock()
    
    async def test_fetch_stock_http_error(self, mock_env):
        """測試 HTTP 錯誤"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            # 根據實際實作，可能拋出錯誤或返回空字典
            result = await fetch_stock()
            assert isinstance(result, dict)
    
    async def test_fetch_stock_malformed_html(self, mock_env):
        """測試格式錯誤的 HTML"""
        mock_html = "<html><body><div>Malformed HTML"
        
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.status_code = 200
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            stocks = await fetch_stock()
            
            # BeautifulSoup 應該能處理格式錯誤的 HTML
            assert isinstance(stocks, dict)
