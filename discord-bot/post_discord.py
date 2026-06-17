#!/usr/bin/env python3
import os
import sys
import json
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
load_dotenv(SCRIPT_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(SCRIPT_DIR / "post.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
MESSAGE = os.getenv("DISCORD_MESSAGE")

if not BOT_TOKEN or not MESSAGE:
    log.error(".env に DISCORD_BOT_TOKEN と DISCORD_MESSAGE を設定してください")
    sys.exit(1)

THREADS_FILE = SCRIPT_DIR / "threads.txt"
LAST_MESSAGES_FILE = SCRIPT_DIR / "last_messages.json"
HEADERS = {"Authorization": f"Bot {BOT_TOKEN}"}

_http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
_https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
PROXIES = {}
if _http_proxy:
    PROXIES["http"] = _http_proxy
if _https_proxy:
    PROXIES["https"] = _https_proxy


def load_thread_ids():
    if not THREADS_FILE.exists():
        log.error(f"{THREADS_FILE} が見つかりません")
        sys.exit(1)
    ids = []
    for line in THREADS_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ids.append(line)
    return ids


def load_last_messages() -> dict:
    if LAST_MESSAGES_FILE.exists():
        return json.loads(LAST_MESSAGES_FILE.read_text())
    return {}


def save_last_messages(data: dict):
    LAST_MESSAGES_FILE.write_text(json.dumps(data, indent=2))


def delete_message(thread_id: str, message_id: str):
    url = f"https://discord.com/api/v10/channels/{thread_id}/messages/{message_id}"
    resp = requests.delete(url, headers=HEADERS, proxies=PROXIES, timeout=10)
    if resp.status_code == 204:
        log.info(f"削除OK thread={thread_id} message={message_id}")
    else:
        log.warning(f"削除FAIL thread={thread_id} message={message_id} status={resp.status_code}")


def post_to_thread(thread_id: str) -> str | None:
    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
    resp = requests.post(
        url,
        headers=HEADERS,
        json={"content": MESSAGE},
        proxies=PROXIES,
        timeout=10,
    )
    if resp.status_code == 200:
        message_id = resp.json()["id"]
        log.info(f"投稿OK thread={thread_id} message={message_id}")
        return message_id
    else:
        log.error(f"投稿FAIL thread={thread_id} status={resp.status_code} body={resp.text}")
        return None


def main():
    thread_ids = load_thread_ids()
    if not thread_ids:
        log.warning("threads.txt にスレッドIDが1件もありません")
        return

    last_messages = load_last_messages()
    log.info(f"{len(thread_ids)} スレッドへ投稿開始")

    ok, ng = 0, 0
    for tid in thread_ids:
        new_message_id = post_to_thread(tid)
        if new_message_id:
            # 新規投稿成功後に前回のメッセージを削除
            if tid in last_messages:
                delete_message(tid, last_messages[tid])
            last_messages[tid] = new_message_id
            ok += 1
        else:
            ng += 1

    save_last_messages(last_messages)
    log.info(f"完了: 成功={ok} 失敗={ng}")
    if ng > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
