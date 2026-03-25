import requests
from bs4 import BeautifulSoup
import csv
import re

def fetch_maoyan_box_office(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://piaofang.maoyan.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            print(f"HTTP错误: {response.status_code}")
            return None
    except Exception as e:
        print(f"网络请求失败: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    movies_data = []

    # 尝试多种选择器定位电影条目
    movie_items = soup.select('div.movie-list dd') or soup.find_all('dd', class_=re.compile('movie')) or soup.find_all('div', class_=re.compile('movie-item'))
    if not movie_items:
        print("无法定位电影条目，请检查HTML结构。")
        # 打印部分HTML以便调试
        print(soup.prettify()[:2000])
        return None

    for item in movie_items:
        try:
            # 获取所有文本内容，按位置提取（备用方案）
            texts = item.get_text(separator='|').split('|')
            # 实际解析仍优先使用选择器
            rank = item.select_one('.rank')
            rank = rank.text.strip() if rank else (texts[0] if texts else '')

            name = item.select_one('.name, .movie-name a')
            name = name.text.strip() if name else (texts[1] if len(texts)>1 else '')

            # 上映信息（包含总票房）
            sub = item.select_one('.movie-sub, .channel-detail .movie-sub')
            release_info = sub.text.strip() if sub else ''
            total_box = ''
            if release_info:
                match = re.search(r'([\d.]+)(亿|万)', release_info)
                if match:
                    total_box = match.group(1) + match.group(2)

            # 综合票房和占比
            numbers = item.select('.movie-item-number')
            box_office = ''
            percent = ''
            if numbers:
                spans = numbers[0].find_all('span')
                if spans:
                    box_office = spans[0].text.strip()
                    if len(spans) > 1:
                        percent = spans[1].text.strip()
            # 排片场次
            show = item.select_one('.show-count, [class*="show"]')
            show_count = show.text.strip() if show else ''

            if name and name != '未知':
                movies_data.append({
                    '排名': rank,
                    '电影名称': name,
                    '上映信息': release_info,
                    '总票房': total_box,
                    '综合票房': box_office,
                    '票房占比': percent,
                    '排片场次': show_count
                })
        except Exception as e:
            print(f"解析条目出错: {e}")
            continue

    return movies_data

# 其余保存代码不变...

def save_to_csv(data, filename='maoyan_box_office.csv'):
    """将数据保存为CSV文件"""
    if not data:
        print("没有数据可保存")
        return

    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    print(f"数据已保存到 {filename}")

if __name__ == "__main__":
    target_url = "https://piaofang.maoyan.com/i/dashboard/movie"
    print("开始抓取猫眼电影票房数据（增强版）...")
    movies = fetch_maoyan_box_office(target_url)

    if movies:
        print(f"成功抓取到 {len(movies)} 部电影的信息。")
        # 打印前5条数据作为预览
        for movie in movies[:5]:
            print(movie)
        save_to_csv(movies)
    else:
        print("抓取失败，未获取到数据。")