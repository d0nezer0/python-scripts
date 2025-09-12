import requests
from bs4 import BeautifulSoup

# 设置请求头模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def scrape_person_info(page):
    url = 'https://www.hfrea.org.cn/oaPerson/page-%s' % page

    try:
        # 发送HTTP请求
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'  # 设置编码

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 假设信息在表格中，查找table标签
            table = soup.find('table')
            if table:
                # 提取表头
                table_headers = [th.get_text(strip=True) for th in table.find_all('th')]
                print("表头信息:", table_headers)

                # 提取表格数据
                print("\n人员信息:")
                for row in table.find_all('tr')[1:]:  # 跳过表头行
                    cells = [td.get_text(strip=True) for td in row.find_all('td')]
                    print(cells)
            else:
                print("未找到表格数据")
        else:
            print(f"请求失败，状态码: {response.status_code}")

    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == '__main__':
    for page in range(1, 275):  # 假设共有10页数据
        print(f"\n正在抓取第 {page} 页数据...")
        scrape_person_info(page)
