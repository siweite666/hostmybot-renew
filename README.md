# HostMyBot Auto Renewal

自动续期 [HostMyBot](https://client.hostmybot.net/) 免费 Discord Bot 托管服务器。

## 工作原理

- 每3天自动检查服务器续期状态
- 余额 ≥ 50 credits 时自动调用 API 续期（+7天）
- 续期结果通过 Telegram 通知

## API 信息

- 面板: `https://client.hostmybot.net`
- 服务器 ID: `51fcda5f`
- 续期成本: 50 credits / 7天
- 积分获取: 1 credit/分钟（自动累积）

## GitHub Secrets

需要设置以下 Secrets:

| Secret | 说明 |
|--------|------|
| `HOSTMYBOT_TOKEN` | HostMyBot API Token |
| `TG_BOT_TOKEN` | Telegram Bot Token |
| `TG_CHAT_ID` | Telegram Chat ID |

## 手动触发

GitHub Actions → Auto Renew HostMyBot Server → Run workflow
