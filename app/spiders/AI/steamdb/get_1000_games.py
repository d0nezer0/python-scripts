"""
统计 CSV 中，release_date 在 8月18 ~ 8月22 之间，且最新粉丝数 > 1000 的所有游戏。

CSV 结构：
  id, name, release_date, url,
  steamDb_releaseDate-0708, followers-0708,
  steamDb_releaseDate-0709, followers-0709,
  ...
  steamDb_releaseDate-0724, followers-0724

release_date 格式示例：
  "31 Jul, 2026"  (英文缩写月)
  "13 Aug, 2026"
  "August 2026"   (英文全称月，无具体日)
  "Late August 2026"

followers 取最新日期（最后一组非空）的粉丝数。
"""

import csv
import re
from datetime import date


def parse_release_date(s: str) -> date | None:
    """解析 release_date 列，支持多种格式，返回 date 对象或 None。"""
    s = (s or "").strip().strip('"').strip()
    if not s:
        return None

    # 1) "31 Jul, 2026" / "13 Aug, 2026"
    m = re.search(r"^(\d{1,2})\s+(\w{3,9})\s*,?\s*(\d{4})$", s)
    if m:
        day, mon_str, year = int(m.group(1)), m.group(2), int(m.group(3))
        mon = _month_num(mon_str)
        if mon:
            return date(year, mon, day)

    # 2) "August 2026" / "Late August 2026" / "Early August 2026"
    m = re.search(r"(?:Early|Mid|Late)?\s*(\w{3,9})\s+(\d{4})$", s)
    if m:
        mon_str, year = m.group(1), int(m.group(2))
        mon = _month_num(mon_str)
        if mon:
            return date(year, mon, 1)  # 模糊日期，取当月 1 日

    return None


def _month_num(s: str) -> int | None:
    """将英文月份（缩写或全称）转为 1~12 数字。"""
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
        "december": 12,
    }
    return months.get(s.strip().lower())


def get_latest_followers(row: list[str]) -> tuple[int, str]:
    """
    从行数据中提取最新日期的粉丝数及对应的 steamDb_releaseDate。
    列结构：..., steamDb_releaseDate-0723, followers-0723, steamDb_releaseDate-0724, followers-0724
    从最后一组往前找，取第一个非空的 followers 值，同时返回对应的日期列。
    返回 (followers, steamDb_releaseDate)。
    """
    # 从第 4 列开始是日期/粉丝对，每两列一组
    for i in range(len(row) - 1, 3, -2):  # 从最后一对往前
        if i < len(row) and row[i].strip():
            try:
                return int(row[i].strip()), row[i - 1].strip()
            except ValueError:
                continue
    return 0, ""


def main(csv_path: str = "/Users/zhoudong/tmp/steam_aug_comingsoon.csv"):
    games = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            games.append(row)

    target_games = []
    for g in games:
        rd = parse_release_date(g.get("release_date", ""))
        if rd is None:
            continue
        followers, latest_date = get_latest_followers(list(g.values()))
        if followers > 1000 and date(2026, 8, 18) <= rd <= date(2026, 8, 22):
            target_games.append((g.get("id", ""), g.get("name", ""), rd, followers, latest_date))

    print(f"符合条件的游戏数量: {len(target_games)}")
    for appid, name, rd, followers, latest_date in target_games:
        print(f"id: {appid}, 游戏: {name}, 上映日期: {rd}, 粉丝数: {followers}, 最新记录日期: {latest_date}")


if __name__ == "__main__":
    main()