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
from datetime import datetime

import requests

# 当前文件所在目录
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# CSV_PATH = os.path.join(CURRENT_DIR, "py_steam_aug_comingsoon.csv")
CSV_PATH = "/Users/zhoudong/tmp/steam_aug_comingsoon_test.csv"

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


def fetch_with_proxy(appid: str | int, max_retries: int = 3) -> dict | None:
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

            # 检查 f 字段是否正常（存在且为数字）
            f_value = data.get("data", {}).get("f")
            if f_value is not None and isinstance(f_value, (int, float)):
                return data

            print(f"  [重试 {attempt}/{max_retries}] appid={appid} f 字段异常: {f_value}")
        except Exception as e:
            print(f"  [重试 {attempt}/{max_retries}] appid={appid} 请求失败: {e}")

        if attempt < max_retries:
            time.sleep(1)

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


def process_csv():
    """主处理逻辑"""
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

    # 读取 CSV
    with open(CSV_PATH, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames.copy()
        rows = list(reader)

    print(f"\n读取到 {len(rows)} 行数据")
    print(f"当前字段: {fieldnames}")

    # 检查并添加今日字段
    need_add_today_release = today_release_col not in fieldnames
    need_add_today_followers = today_followers_col not in fieldnames

    if need_add_today_release:
        fieldnames.append(today_release_col)
        print(f"新增字段: {today_release_col}")
    if need_add_today_followers:
        fieldnames.append(today_followers_col)
        print(f"新增字段: {today_followers_col}")

    # 先写入表头（覆盖原文件）
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

    # 遍历每一行处理
    updated_count = 0
    skipped_count = 0
    api_fail_count = 0
    alarm_count = 0

    for i, row in enumerate(rows):
        app_id = row.get("id", "").strip()
        yesterday_release = row.get(yesterday_release_col, "").strip()
        yesterday_followers = row.get(yesterday_followers_col, "").strip()

        print(f"\n--- 行 {i + 1}: appid={app_id}, name={row.get('name', '')} ---")

        # 检查昨日的 releaseDate 是否为带小时的 UTC 时间
        if not is_utc_time_format(yesterday_release):
            print(f"  跳过: releaseDate 不是具体 UTC 时间 ('{yesterday_release}')")
            skipped_count += 1
            # 单行写入
            with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(row)
            continue

        print(f"  releaseDate 是具体 UTC 时间: {yesterday_release}")

        # 复制 releaseDate 到今日列
        row[today_release_col] = yesterday_release

        # 通过 API 获取 followers (f 字段)
        print(f"  正在通过 API 获取 followers...")
        data = fetch_with_proxy(app_id)

        if data is None:
            print(f"  API 请求失败，跳过 followers 更新")
            api_fail_count += 1
            # 报警：昨天有 followers 值，今天没获取到
            if yesterday_followers:
                print(f"  [报警] appid={app_id} 昨天有 followers={yesterday_followers}，今天 API 请求失败")
                alarm_count += 1
            # 单行写入
            with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(row)
            continue

        # 检查是否返回 {"success":false}
        if data.get("success") is False:
            print(f"  API 返回 success=false，followers 填入 '无'")
            row[today_followers_col] = "无"
            # 报警：昨天有 followers 值，今天返回 false
            if yesterday_followers:
                print(f"  [报警] appid={app_id} 昨天有 followers={yesterday_followers}，今天 API 返回 success=false")
                alarm_count += 1
            # 单行写入
            with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(row)
            continue

        f_value = data.get("data", {}).get("f")

        # 检查 f 值是否正常
        if f_value is not None and isinstance(f_value, (int, float)):
            row[today_followers_col] = str(f_value)
            print(f"  followers 更新成功: {f_value}")
            updated_count += 1
        else:
            print(f"  f 字段异常: {f_value}")
            api_fail_count += 1
            # 报警：昨天有 followers 值，今天 f 字段异常
            if yesterday_followers:
                print(f"  [报警] appid={app_id} 昨天有 followers={yesterday_followers}，今天 f 字段异常={f_value}")
                alarm_count += 1

        # 单行写入
        with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(row)

    print(f"\n{'=' * 50}")
    print(f"处理完成!")
    print(f"  更新行数: {updated_count}")
    print(f"  跳过行数: {skipped_count}")
    print(f"  API 失败: {api_fail_count}")
    print(f"  报警次数: {alarm_count}")
    print(f"  总行数: {len(rows)}")
    print(f"  当前字段: {fieldnames}")


def main():
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