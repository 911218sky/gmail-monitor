import httpx
from bs4 import BeautifulSoup
from config import URL


async def fetch_stock():
    """抓取網站庫存資料"""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(URL)
        soup = BeautifulSoup(resp.text, "html.parser")
        stocks = {}
        rows = soup.select("tr")
        for row in rows:
            badge = row.select_one("span.layui-badge.layui-bg-cyan")
            if not badge:
                continue
            name_td = row.select_one("td")
            if name_td:
                name = name_td.get_text(strip=True)
                stock = int(badge.text.strip())
                stocks[name] = stock
        return stocks
