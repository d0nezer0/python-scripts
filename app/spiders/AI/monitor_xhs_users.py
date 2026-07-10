#!/usr/bin/env python3
"""
小红书用户内容监控脚本 v2
通过 HTTP 直接请求用户主页，解析 SSR 数据获取帖子列表。
不需要登录、不需要 cookie、不需要 xsec_token。

被监控账号:
  637e3123000000001f01ea73  (周杰伦官方粉丝社区)
  5b8eb188cb86550001ecdcf8  (林俊杰)
"""

import json
import re
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# ============ 配置 ============
USER_IDS = [
    "637e3123000000001f01ea73",
    "5b8eb188cb86550001ecdcf8",
]

STATE_DIR = Path("/Users/zhoudong/WorkBuddy/automation-claw-20260414103057/scripts/xhs_monitor_state")
LOG_FILE = Path("/Users/zhoudong/WorkBuddy/automation-claw-20260414103057/scripts/xhs_monitor.log")

STATE_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ============ 工具函数 ============

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def alert(user_id: str, username: str, new_titles: list):
    """报警：系统通知 + 日志"""
    new_count = len(new_titles)
    latest_title = new_titles[0] if new_titles else ""
    msg = (
        f"🔔 小红书新内容提醒\n"
        f"账号: {username} ({user_id})\n"
        f"新增帖子数: {new_count}\n"
        f"最新帖子: {latest_title}\n"
        f"链接: https://www.xiaohongshu.com/user/profile/{user_id}"
    )
    log(f"【报警】{msg}")

    # macOS 系统通知
    try:
        notif_msg = f"{username} 发布了 {new_count} 篇新内容：{latest_title}"
        subprocess.run(
            [
                "osascript", "-e",
                f'display notification "{notif_msg}" with title "小红书监控报警" sound name "Glass"',
            ],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass


# ============ 数据获取：HTTP + SSR 解析 ============

def fetch_user_profile(user_id: str) -> dict:
    """
    通过 HTTP 直接请求用户主页，解析 SSR 返回的 __INITIAL_STATE__。
    不需要登录，不需要 cookie，不需要 xsec_token。

    返回 {"posts": [{"title": str, "type": str}], "username": str} 或 {"error": str}
    """
    url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
    req = urllib.request.Request(url, headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return {"error": f"http_request_failed: {e}"}

    if len(html) < 5000:
        return {"error": f"response_too_short: {len(html)} bytes"}

    # 提取 __INITIAL_STATE__
    match = re.search(
        r"window\.__INITIAL_STATE__\s*=\s*(\{.+?\})\s*</script>", html, re.DOTALL
    )
    if not match:
        return {"error": "no_initial_state"}

    try:
        raw = match.group(1).replace("undefined", "null")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": f"json_parse_failed: {e}"}

    # 提取用户信息
    user_data = data.get("user", {})
    user_page = user_data.get("userPageData") or {}
    username = user_page.get("nickname") or user_id

    # 也尝试从 noteCard 里的 user 字段获取
    notes_data = user_data.get("notes")
    if not notes_data or not isinstance(notes_data, list) or not notes_data[0]:
        return {"error": "no_notes_data"}

    # 取第一个 tab 的帖子列表
    notes_list = notes_data[0]
    if not isinstance(notes_list, list):
        return {"error": "notes_not_list"}

    posts = []
    for n in notes_list:
        if not isinstance(n, dict):
            continue
        nc = n.get("noteCard") or {}
        title = nc.get("displayTitle") or n.get("displayTitle") or ""
        if isinstance(title, dict):
            title = title.get("text", "")
        note_type = nc.get("type", "unknown")
        if title:
            posts.append({"title": str(title).strip(), "type": note_type})

    if not posts:
        return {"error": "empty_notes_list"}

    # 如果 userPageData 没有昵称，从帖子卡片里取
    if username == user_id and posts:
        first_card_user = notes_list[0].get("noteCard", {}).get("user", {})
        username = first_card_user.get("nickname") or first_card_user.get("nickName") or user_id

    return {"posts": posts, "username": username}


# ============ 核心：检查单个用户 ============

def check_user(user_id: str):
    state_file = STATE_DIR / f"{user_id}.titles.json"
    log(f"检查用户 {user_id} ...")

    result = fetch_user_profile(user_id)

    if "error" in result:
        log(f"  ⚠️ 获取失败: {result['error']}")
        return

    posts = result.get("posts", [])
    username = result.get("username", user_id)
    log(f"  获取到 {len(posts)} 篇帖子（用户: {username}）")

    # 用标题集合做对比
    current_titles = [p["title"] for p in posts]

    # 初次运行：保存初始状态
    if not state_file.exists():
        state_file.write_text(
            json.dumps(current_titles, ensure_ascii=False), encoding="utf-8"
        )
        log(f"  ✅ 初始化完成，记录 {len(current_titles)} 篇帖子")
        return

    # 读取旧状态，对比
    old_titles = json.loads(state_file.read_text(encoding="utf-8"))
    old_set = set(old_titles)
    current_set = set(current_titles)

    # 检测新增（在当前有但旧状态没有的）
    new_titles = [t for t in current_titles if t not in old_set]

    # 检测删除（在旧状态有但当前没有的，可能是下架）
    removed_titles = [t for t in old_titles if t not in current_set]

    if new_titles:
        alert(user_id, username, new_titles)
    else:
        log("  ✅ 无新内容")

    if removed_titles:
        log(f"  ℹ️ 检测到 {len(removed_titles)} 篇帖子被移除/下架")

    # 只要标题列表有变化就更新状态
    if new_titles or removed_titles or current_titles != old_titles:
        state_file.write_text(
            json.dumps(current_titles, ensure_ascii=False), encoding="utf-8"
        )
        log("  状态已更新")


# ============ 主流程 ============

def main():
    log("===== 开始监控检查 =====")
    for uid in USER_IDS:
        try:
            check_user(uid)
        except Exception as e:
            log(f"  ❌ 检查 {uid} 时发生异常: {e}")
        time.sleep(2)
    log("===== 检查完成 =====")


if __name__ == "__main__":
    main()
