"""
SteamDB 扩展 API 爬虫
根据 curl 请求封装 Python 请求方法
本爬虫抓取 确定日期的游戏的 followers 数据，
#### 游戏日期 需要从 steamdb 获取， 目前只有 workbuddy 的 webfetch 方式可行；
"""

import csv
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import discover_aug

# 当前文件所在目录
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# CSV_PATH = os.path.join(CURRENT_DIR, "py_steam_aug_comingsoon.csv")
CSV_PATH = "/Users/zhoudong/tmp/steam_aug_comingsoon.csv"

# 代理配置
PROXY_URL = "https://dps.kdlapi.com/api/getdps/?orderid=906160381754999&num=500&pt=1&f_et=1&format=json&sep=1&f_loc=1"
PROXY_AUTH = "358962325:iay9pihq"


def fetch_steamdb_app_info(appid: str | int) -> dict:
    """
    获取 SteamDB 应用信息

    Args:
        appid: Steam 应用 ID

    Returns:
        dict: API 返回的 JSON 数据
    """
    url = f"https://extension.steamdb.info/api/ExtensionApp/?appid={appid}"

    headers = {
        "Accept": "application/json",
        "User-Agent": "curl/7.87.0",
        "X-Requested-With": "SteamDB",
        "Origin": "chrome-extension://kdbmhfkmnlmbkgbabkdealhhbfhlmmon",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_with_proxy(appid: str | int, max_retries: int = 5) -> dict | None:
    """
    使用代理获取 SteamDB 应用信息，带重试机制

    Args:
        appid: Steam 应用 ID
        max_retries: 最大重试次数

    Returns:
        dict | None: API 返回的 JSON 数据，失败返回 None
    """
    url = f"https://extension.steamdb.info/api/ExtensionApp/?appid={appid}"

    headers = {
        "Accept": "application/json",
        "User-Agent": "curl/7.87.0",
        "X-Requested-With": "SteamDB",
        "Origin": "chrome-extension://kdbmhfkmnlmbkgbabkdealhhbfhlmmon",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }

    for attempt in range(1, max_retries + 1):
        try:
            # 如果是最后一次尝试，不用代理，直接请求
            if attempt > 3:
                print(f"  [最后一次尝试] appid={appid} 直连请求...")
                response = requests.get(url, headers=headers, timeout=30)
            else:
                # 每次请求获取新的代理
                proxy_resp = requests.get(PROXY_URL, timeout=10)
                proxy_resp.raise_for_status()
                proxy_data = proxy_resp.json()
                proxy_list = proxy_data.get("data", {}).get("proxy_list", [])
                if not proxy_list:
                    print(f"  [重试 {attempt}/{max_retries}] appid={appid} 代理列表为空")
                    continue
                proxy_item = random.choice(proxy_list)
                proxy_ip = proxy_item.split(",")[0]
                # 检查代理 IP 格式，如果格式不对则不用代理
                # proxy_ip = proxy_resp.text.strip()
                proxy_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$"
                if re.match(proxy_pattern, proxy_ip):
                    proxies = {
                        "http": f"http://{PROXY_AUTH}@{proxy_ip}",
                        "https": f"http://{PROXY_AUTH}@{proxy_ip}",
                    }
                    response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
                else:
                    print(f"  代理 IP 格式无效: {proxy_ip}，跳过代理")
                    response = requests.get(url, headers=headers, timeout=30)

            response.raise_for_status()
            data = response.json()

            # 如果返回 {"success":false}，返回字符串 "无"
            if data.get("success") is False:
                return "无"

            # 检查 f 字段是否正常（存在且为数字）
            f_value = data.get("data", {}).get("f")
            if f_value is not None and isinstance(f_value, (int, float)):
                return data

            print(f"  [重试 {attempt}/{max_retries}] appid={appid} f 字段异常: {f_value}")
        except Exception as e:
            print(f"  [重试 {attempt}/{max_retries}] appid={appid} 请求失败: {e}")

        if attempt < max_retries:
            time.sleep(0.01)

    return None


def is_utc_time_format(value: str) -> bool:
    """
    判断 releaseDate 是否为带小时的 UTC 时间格式
    例如: "31 August 2026 – 10:00:00 UTC"
    """
    if not value or not isinstance(value, str):
        return False
    pattern = r"\d{1,2}\s+\w+\s+\d{4}\s*[–-]\s*\d{2}:\d{2}:\d{2}\s*UTC"
    return bool(re.search(pattern, value.strip()))


def get_today_suffix() -> str:
    """获取今日日期后缀，如 0709"""
    return datetime.now().strftime("%m%d")


def get_yesterday_suffix() -> str:
    """获取昨日日期后缀，如 0708"""
    from datetime import timedelta

    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%m%d")


def process_single_row(
    index: int,
    row: dict,
    yesterday_followers_col: str,
    today_followers_col: str,
) -> tuple[int, dict, str, bool]:
    """
    处理单行：调用 API 获取 followers 数据

    Returns:
        (index, modified_row, status, is_alarm)
        status: "skipped" | "updated" | "no_followers" | "api_fail"
    """
    app_id = (row.get("id") or "").strip()
    yesterday_followers = (row.get(yesterday_followers_col) or "").strip()
    today_followers = (row.get(today_followers_col) or "").strip()

    # 如果今日已有 followers 值，跳过
    if today_followers:
        return index, row, "skipped", False

    # 通过 API 获取 followers
    result = fetch_with_proxy(app_id)
    is_alarm = False

    # 检查是否返回字符串 "无"（对应 API 返回 success=false）
    if result == "无":
        row[today_followers_col] = "无"
        if yesterday_followers and yesterday_followers != "无":
            row[today_followers_col] = yesterday_followers
            is_alarm = True
            print(f"  [报警] appid={app_id} 昨天有 followers={yesterday_followers}，今天 API 返回 success=false")
        return index, row, "no_followers", is_alarm

    if result is None:
        row[today_followers_col] = "无"
        if yesterday_followers and yesterday_followers != "无":
            row[today_followers_col] = yesterday_followers
            is_alarm = True
            print(f"  [报警] appid={app_id} 昨天有 followers={yesterday_followers}，今天 API 请求失败")
        return index, row, "api_fail", is_alarm

    # 正常返回 data 字典，提取 f 值
    f_value = result.get("data", {}).get("f")
    if f_value is not None and isinstance(f_value, (int, float)):
        row[today_followers_col] = str(f_value)
        return index, row, "updated", False

    # f 字段异常
    if yesterday_followers:
        is_alarm = True
        print(f"  [报警] appid={app_id} 昨天有 followers={yesterday_followers}，今天 f 字段异常={f_value}")
    return index, row, "api_fail", is_alarm


def process_csv():
    """主处理逻辑（多并发版本）"""
    today_suffix = get_today_suffix()
    yesterday_suffix = get_yesterday_suffix()

    today_release_col = f"steamDb_releaseDate-{today_suffix}"
    today_followers_col = f"followers-{today_suffix}"
    yesterday_release_col = f"steamDb_releaseDate-{yesterday_suffix}"
    yesterday_followers_col = f"followers-{yesterday_suffix}"

    print(f"今日日期后缀: {today_suffix}")
    print(f"昨日日期后缀: {yesterday_suffix}")
    print(f"今日 releaseDate 列: {today_release_col}")
    print(f"今日 followers 列: {today_followers_col}")
    print(f"昨日 releaseDate 列: {yesterday_release_col}")
    print(f"昨日 followers 列: {yesterday_followers_col}")

    # 读取 CSV 获取字段名和数据（使用 utf-8-sig 自动去除 BOM）
    with open(CSV_PATH, mode="r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames.copy()
        rows = list(reader)

    print(f"当前字段: {fieldnames}")
    print(f"读取到 {len(rows)} 行数据")

    # 检查并添加今日字段
    need_add_today_release = today_release_col not in fieldnames
    need_add_today_followers = today_followers_col not in fieldnames

    if need_add_today_release:
        fieldnames.append(today_release_col)
        print(f"新增字段: {today_release_col}")
    if need_add_today_followers:
        fieldnames.append(today_followers_col)
        print(f"新增字段: {today_followers_col}")

    # 如果新增了字段，需要重写表头+全部数据
    need_rewrite = need_add_today_release or need_add_today_followers
    if need_rewrite:
        cleaned_rows = []
        for row in rows:
            cleaned_row = {k: v for k, v in row.items() if k is not None}
            cleaned_rows.append(cleaned_row)
        with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows)
        print("表头已更新，数据已重写")

    # 并发处理每一行
    updated_count = 0
    skipped_count = 0
    api_fail_count = 0
    no_followers_count = 0
    alarm_count = 0

    # 收集结果（按 index 排序）
    results: dict[int, dict] = {}

    CONCURRENCY = 8
    print(f"\n开始并发抓取（并发数={CONCURRENCY}）...")
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = {}
        for i, row in enumerate(rows):
            future = executor.submit(
                process_single_row,
                i, row, yesterday_followers_col, today_followers_col,
            )
            futures[future] = i

        done_count = 0
        for future in as_completed(futures):
            i, row, status, is_alarm = future.result()
            results[i] = row

            if status == "skipped":
                skipped_count += 1
            elif status == "updated":
                updated_count += 1
            elif status == "no_followers":
                no_followers_count += 1
            elif status == "api_fail":
                api_fail_count += 1
            if is_alarm:
                alarm_count += 1

            done_count += 1
            if done_count % 50 == 0 or done_count == len(rows):
                print(f"  进度: {done_count}/{len(rows)} 已完成")

    # 按原始顺序写回 CSV
    tmp_csv_path = CSV_PATH + ".tmp"
    with open(tmp_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(len(rows)):
            writer.writerow(results[i])

    # 用临时文件替换原文件
    os.replace(tmp_csv_path, CSV_PATH)

    print(f"\n{'=' * 50}")
    print(f"处理完成!")
    print(f"  更新行数: {updated_count}")
    print(f"  跳过行数: {skipped_count}")
    print(f"  无followers: {no_followers_count}")
    print(f"  API失败: {api_fail_count}")
    print(f"  报警次数: {alarm_count}")
    print(f"  总行数: {len(rows)}")
    print(f"  当前字段: {fieldnames}")


def main():
    # 第一步， 新游戏发现；
    print("=" * 50)
    print("第一步：发现 8 月新游戏...")
    print("=" * 50)
    discover_aug.main(csv_path=CSV_PATH)

    # 第二步， 全量 followers 抓取；
    print("\n" + "=" * 50)
    print("第二步：全量 followers 抓取...")
    print("=" * 50)

    # 开始抓取时间
    start_time = datetime.now()
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    process_csv()

    # 结束抓取时间
    end_time = datetime.now()
    elapsed = end_time - start_time
    print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总用时: {elapsed.total_seconds():.2f} 秒")


if __name__ == "__main__":
    main()
