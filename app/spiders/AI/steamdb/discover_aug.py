#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自动发现 Steam coming-soon 中「2026 年 8 月」发售的新游戏，
把 CSV 里缺失的条目追加进去（id / name(中文) / release_date(英文) / url，
其余跟踪列留空）。

设计要点：
- 扫描 store.steampowered.com 的 comingsoon 无限滚动接口，按发售日升序。
- 用 schinese 语言拿中文名；日期为中文格式，统一转成英文
  （"13 Aug, 2026" / "August 2026" / "Late August 2026"）以匹配主表。
- 只取「2026 年 8 月」的条目（含具体日和「August 2026」模糊日）。
- 与现有 CSV 的 id 集合做差集，只追加缺失项 -> 天然幂等，可每日重跑。
- 每页请求带重试与退避；单页彻底失败则跳过并记录，不中断整体。

用法：
    python3 discover_aug.py [--csv PATH] [--dry-run]
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.request
from datetime import date

CSV_DEFAULT = "/Users/zhoudong/tmp/steam_aug_comingsoon.csv"
EN_MONTHS = {
    "1": "Jan", "2": "Feb", "3": "Mar", "4": "Apr", "5": "May", "6": "Jun",
    "7": "Jul", "8": "Aug", "9": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}
SEARCH_URL = (
    "https://store.steampowered.com/search/results/"
    "?query&start={start}&count={count}&filter=comingsoon&hwtype=0&ndl=1"
    "&infinite=1&sort_by=Released_ASC&l=schinese&cc=cn"
)


def fetch_json(url, tries=10):
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    )
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8", "ignore"))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(min(2.0 + i * 0.5, 8.0))  # 渐进退避，封顶 8s
    sys.stderr.write(f"[warn] 页面请求失败 {url}: {last}\n")
    return {}


def cn_date_to_en(s):
    """把 '2026 年 8 月 13 日' / '2026 年 8 月' / '2026 年 8 月下旬' 转英文。"""
    s = (s or "").strip()
    if not s:
        return s
    m = re.search(
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(上旬|中旬|下旬|上|中|下)?\s*(\d{1,2})?\s*日?",
        s,
    )
    if not m:
        return s  # 已是英文或无法解析，原样返回
    year, mon = m.group(1), EN_MONTHS.get(m.group(2), m.group(2))
    qual, day = m.group(3), m.group(4)
    base = f"{int(day)} {mon}, {year}" if day else f"{mon} {year}"
    if qual in ("上旬", "上"):
        base = "Early " + base
    elif qual in ("中旬", "中"):
        base = "Mid " + base
    elif qual in ("下旬", "下"):
        base = "Late " + base
    return base


def parse_page(html):
    """返回 [(appid, name, cn_date), ...]"""
    out = []
    # 每个结果行是一个 <a href=".../app/<id>/..."> ... </a>
    for m in re.finditer(
        r'<a\s+[^>]*href="https://store\.steampowered\.com/app/(\d+)/[^"]*"[^>]*>(.*?)</a>',
        html,
        re.S,
    ):
        appid, chunk = m.group(1), m.group(2)
        name_m = re.search(r'class="title">(.*?)</span>', chunk, re.S)
        date_m = re.search(r'class="search_released[^"]*">(.*?)</div>', chunk, re.S)
        if not name_m or not date_m:
            continue
        name = name_m.group(1).strip().strip("《》").strip()
        cn_date = date_m.group(1).strip()
        out.append((appid, name, cn_date))
    return out


def date_ym(s):
    """从中文日期提取 (year, month) 用于判断是否已过 8 月。"""
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", s or "")
    if m:
        return (int(m.group(1)), int(m.group(2)))
    # 英文兜底
    me = re.search(r"(\w{3})\w*\s*,?\s*(\d{4})", s or "")
    if me:
        inv = {v: k for k, v in EN_MONTHS.items()}
        return (int(me.group(2)), int(inv.get(me.group(1), 0)))
    return (0, 0)


def is_aug_2026(cn_date):
    return bool(re.search(r"2026\s*年\s*8\s*月", cn_date or ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=CSV_DEFAULT)
    ap.add_argument("--dry-run", action="store_true", help="只报告，不写入")
    args = ap.parse_args()

    # 读现有 id
    existing = set()
    header = None
    with open(args.csv, newline="", encoding="utf-8") as f:
        rd = csv.reader(f)
        header = next(rd)
        for row in rd:
            if row:
                existing.add(row[0])
    width = len(header)

    # 扫描 coming-soon（升序），收集 8 月条目
    found = {}  # appid -> (name, en_date)
    seen_aug = False
    skipped_pages = []
    start = 0
    page = 0
    MAX_PAGES = 150
    while page < MAX_PAGES:
        d = fetch_json(SEARCH_URL.format(start=start, count=100))
        html = d.get("results_html", "")
        if not html:
            skipped_pages.append(start)
            start += 100
            page += 1
            continue
        rows = parse_page(html)
        page_aug = 0
        ym_list = []
        for appid, name, cn_date in rows:
            ym_list.append(date_ym(cn_date))
            if is_aug_2026(cn_date):
                seen_aug = True
                if appid not in found:
                    found[appid] = (name, cn_date_to_en(cn_date))
                    page_aug += 1
        # 停止判定：已见过 8 月，且本页零 8 月匹配，且本页所有日期都 >= 2026-09
        past_aug = all((y, mo) >= (2026, 9) for (y, mo) in ym_list) if ym_list else False
        if seen_aug and page_aug == 0 and past_aug:
            break
        start += 100
        page += 1

    # 差集
    new_ids = [a for a in found if a not in existing]
    rows_to_add = []
    for appid in new_ids:
        name, en_date = found[appid]
        row = [appid, name, en_date, f"https://store.steampowered.com/app/{appid}/"]
        row += [""] * (width - len(row))
        rows_to_add.append(row)

    if args.dry_run:
        print(f"[dry-run] 扫描到 8 月候选 {len(found)} 个；CSV 已有 {len(existing)} 个 id")
        print(f"[dry-run] 将新增 {len(rows_to_add)} 个：")
        for r in rows_to_add[:20]:
            print("   ", r[0], "|", r[1], "|", r[2])
        if len(rows_to_add) > 20:
            print(f"   ... 共 {len(rows_to_add)} 个")
        if skipped_pages:
            print(f"[dry-run] 跳过的失败页 start={skipped_pages}")
        return

    if rows_to_add:
        with open(args.csv, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for r in rows_to_add:
                w.writerow(r)
        print(f"已追加 {len(rows_to_add)} 个新 8 月游戏到 {args.csv}")
    else:
        print("无需追加：未发现有缺失的 8 月新游戏")
    if skipped_pages:
        print(f"警告：以下页请求失败被跳过 start={skipped_pages}（可重跑补齐）")


if __name__ == "__main__":
    main()
