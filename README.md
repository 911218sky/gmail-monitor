# Gmail 庫存監控

每 5 分鐘監控 https://gmailbuy.com/ 的庫存變化，有更新時透過 Telegram 通知。

## 快速開始

### 1. 取得 Telegram Bot Token

1. 在 Telegram 搜尋 `@BotFather`
2. 發送 `/newbot` 並按指示創建 Bot
3. 複製取得的 Token（格式：`123456:ABC-DEF...`）

### 2. 配置 Bot Token

```bash
cp .env.example .env
# 編輯 .env 填入你的 Bot Token
```

### 3. 啟動監控

```bash
docker compose up -d
docker compose logs -f  # 查看日誌
```

### 4. 訂閱通知

在 Telegram 搜尋你的 Bot，發送：
```
/subscribe
```

✅ 訂閱後才會收到庫存變化通知！

## 停止監控

```bash
docker compose down
```

## 更新到最新版本

```bash
docker compose pull
docker compose up -d
```

## 解除安裝

```bash
# 停止並刪除容器
docker compose down

# 刪除 Docker 映像
docker rmi ghcr.io/911218sky/gmail-monitor:latest

# 刪除數據（包含所有訂閱者、庫存記錄等）
docker volume rm gmail-monitor_monitor-data

# 刪除專案目錄
cd ..
rm -rf gmail-monitor
```

## Telegram 指令

### 普通用戶指令

- `/start` - 查看指令列表
- `/subscribe` - 訂閱庫存變化通知 ⭐
- `/unsubscribe` - 取消訂閱
- `/check` - 立即檢查庫存
- `/report` - 查看完整庫存報告

### 管理員指令 🔐

首先使用 `/admin <密碼>` 登入成為管理員，然後可使用：

- `/status` - 查看系統狀態（訂閱人數、檢查間隔等）
- `/interval <分鐘>` - 調整檢查間隔（例如：`/interval 10`）
- `/broadcast <訊息>` - 廣播訊息給所有訂閱者

**設定管理員密碼：** 在 `.env` 文件中設定 `ADMIN_PASSWORD`

## 查看歷史庫存

```bash
cat stock_data.json
```