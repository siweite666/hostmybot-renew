#!/usr/bin/env python3
"""HostMyBot auto-renewal script.
Checks balance and renews server if enough credits (50).
Sends result to Telegram.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

PANEL_URL = "https://client.hostmybot.net"
SERVER_ID = "51fcda5f"
RENEW_COST = 50

API_TOKEN = os.environ.get("HOSTMYBOT_TOKEN", "")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")


def api_get(path: str) -> dict:
    req = urllib.request.Request(
        f"{PANEL_URL}{path}",
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def api_post(path: str) -> dict:
    req = urllib.request.Request(
        f"{PANEL_URL}{path}",
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        data=b"{}",
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def send_tg(msg: str):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("[WARN] Telegram not configured, skipping notification")
        return
    try:
        data = urllib.parse.urlencode({
            "chat_id": TG_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            data=data,
        )
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        if result.get("ok"):
            print("[OK] Telegram notification sent")
        else:
            print(f"[WARN] Telegram API returned: {result}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[WARN] Telegram HTTP {e.code}: {body}")
    except Exception as e:
        print(f"[WARN] Telegram send failed: {e}")


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Step 1: Check renewal status
    try:
        status = api_get(f"/api/client/servers/{SERVER_ID}/renewal")
    except Exception as e:
        msg = f"❌ <b>HostMyBot 续期失败</b>\n⏰ {now}\n查询状态出错: {e}"
        print(msg)
        send_tg(msg)
        sys.exit(1)

    balance = status.get("balance", 0)
    can_renew = status.get("can_renew", False)
    suspended = status.get("suspended", False)
    renewable = status.get("renewable", False)
    days_to_add = status.get("days_to_add", 7)

    print(f"Balance: {balance} credits")
    print(f"Can renew: {can_renew}")
    print(f"Suspended: {suspended}")
    print(f"Cost: {RENEW_COST} credits → +{days_to_add} days")

    # Step 2: Decide action
    if suspended:
        msg = (
            f"⚠️ <b>HostMyBot 服务器已暂停</b>\n"
            f"⏰ {now}\n"
            f"💰 余额: {balance} credits\n"
            f"需要手动处理"
        )
        print(msg)
        send_tg(msg)
        sys.exit(1)

    if not renewable:
        msg = (
            f"ℹ️ <b>HostMyBot 服务器不可续期</b>\n"
            f"⏰ {now}\n"
            f"💰 余额: {balance} credits"
        )
        print(msg)
        send_tg(msg)
        return

    if balance < RENEW_COST:
        msg = (
            f"⏳ <b>HostMyBot 余额不足</b>\n"
            f"⏰ {now}\n"
            f"💰 余额: {balance}/{RENEW_COST} credits\n"
            f"还差 {RENEW_COST - balance} credits\n"
            f"预计 {RENEW_COST - balance} 分钟后够续期"
        )
        print(msg)
        send_tg(msg)
        return

    # Step 3: Renew!
    try:
        result = api_post(f"/api/client/servers/{SERVER_ID}/renewal")
        if "error" in result:
            msg = (
                f"❌ <b>HostMyBot 续期失败</b>\n"
                f"⏰ {now}\n"
                f"错误: {result['error']}\n"
                f"💰 余额: {balance} credits"
            )
        else:
            new_balance = result.get("balance", balance - RENEW_COST)
            msg = (
                f"✅ <b>HostMyBot 续期成功!</b>\n"
                f"⏰ {now}\n"
                f"📅 +{days_to_add} 天\n"
                f"💰 余额: {new_balance} credits"
            )
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            detail = err.get("error", body)
        except Exception:
            detail = body
        msg = (
            f"❌ <b>HostMyBot 续期失败</b>\n"
            f"⏰ {now}\n"
            f"HTTP {e.code}: {detail}\n"
            f"💰 余额: {balance} credits"
        )
    except Exception as e:
        msg = (
            f"❌ <b>HostMyBot 续期失败</b>\n"
            f"⏰ {now}\n"
            f"错误: {e}\n"
            f"💰 余额: {balance} credits"
        )

    print(msg)
    send_tg(msg)


if __name__ == "__main__":
    import urllib.parse
    main()
