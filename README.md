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
# 停止容器
docker compose down

# 拉取最新映像
docker compose pull

# 重新啟動
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
- `/notify` - 設定通知偏好（全部/只補貨/只減少）
- `/check` - 立即檢查庫存
- `/report` - 查看完整庫存報告
- `/website` - 前往官網
- `/help` - 顯示幫助訊息
- `/admin <密碼>` - 管理員登入

### 管理員指令 🔐

使用 `/admin <密碼>` 登入後，輸入 `/` 可看到以下管理員專屬指令：

- `/status` - 查看系統狀態（訂閱人數、檢查間隔、變化閾值等）
- `/interval <分鐘>` - 調整檢查間隔（例如：`/interval 10`）
- `/threshold <數量>` - 調整變化閾值，指物品的變化超過多少才發送提醒（例如：`/threshold 100`）
- `/broadcast <訊息>` - 廣播訊息給所有訂閱者
- `/help` - 顯示幫助訊息（包含管理員功能說明）

**設定管理員密碼：** 在 `.env` 文件中設定 `ADMIN_PASSWORD`

## 查看歷史庫存

```bash
cat stock_data.json
```