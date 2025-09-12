import requests
import re
from collections import defaultdict

from bs4 import BeautifulSoup

# 搜索结果页面URL
search_url = "https://ptclient.cirea.org.cn/jjclient/login/tabjjrpublicbrowse1"


def get_detail_url(rid):
    # 目标网页URL
    url = "https://ptclient.cirea.org.cn/jjclient/login/jjrpublicbrowse2new?rid=%s" % rid

    try:
        # 发送请求获取网页内容
        response = requests.get(url)
        response.encoding = response.apparent_encoding  # 自动识别编码
        html_content = response.text

        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 打印页面标题信息
        print("全国房地产经纪行业信息平台 - 个人信息解析结果")
        print("=" * 50)

        # 提取并打印所有表格内容
        tables = soup.find_all('table')
        table_titles = [
            "个人基本信息", "资格信息", "登记信息",
            "会员信息", "继续教育信息", "暂无良好记录", "暂无不良记录"
        ]

        for i, table in enumerate(tables):
            # 打印表格标题
            if i < len(table_titles):
                print(f"\n【{table_titles[i]}】")
            else:
                print(f"\n【未命名表格 {i + 1}】")
            print("-" * 40)

            # 解析表格行和列
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                # 清理文本并拼接
                row_text = [col.get_text(strip=True) for col in cols]
                # 过滤空值并打印
                if any(row_text):
                    print("\t".join(row_text))

    except Exception as e:
        print(f"解析出错: {str(e)}")


def get_data(rid):
    sample_content = get_real_estate_info(rid)

    parsed_info = parse_real_estate_info(sample_content)

    # 格式化打印结果
    for section, data in parsed_info.items():
        print(f"=== {section} ===")
        for key, values in data.items():
            if isinstance(values, list):
                print(f"{key}:")
                for v in values:
                    print(f"  - {v}")
            else:
                print(f"{key}: {values}")
        print("\n--- 分割线 ---\n")


def get_real_estate_info(rid):
    url = "https://ptclient.cirea.org.cn/jjclient/login/jjrpublicbrowse2new?rid=%s" % rid
    response = requests.get(url)
    return response.text


def parse_real_estate_info(content):
    info = defaultdict(dict)
    current_section = None

    # 定义各部分标题的正则模式
    section_patterns = {
        '个人基本信息': r'^姓名:',
        '资格信息': r'^考试年份:',
        '登记信息': r'^执业单位:',
        '会员信息': r'^会员编号:'
    }

    for line in content.split('\n'):
        line = line.strip()

        # 匹配各部分标题
        for section, pattern in section_patterns.items():
            if re.match(pattern, line):
                current_section = section
                break

        # 提取键值对
        if current_section and ':' in line:
            key, value = re.match(r'^(.*?):\s*(.*)$', line).groups()

            # 处理多值字段（如资格信息中的考试年份）
            if key in info[current_section] and isinstance(info[current_section][key], list):
                info[current_section][key].append(value)
            else:
                info[current_section][key] = [value] if current_section == '资格信息' else value

    return info


if __name__ == '__main__':
    rid = "8d1868848737379d9cfe2ebd29837eb6"
    get_detail_url(rid)
    # get_data(rid)
