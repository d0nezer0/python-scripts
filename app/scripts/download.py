import requests
import os
from urllib.parse import urlparse


def download_image(url, save_dir="images"):
    """原下载函数，无修改"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    filename = os.path.basename(urlparse(url).path)
    # filename = url
    # filename = urlparse(url)
    if not filename:
        filename = f"image_{hash(url)}.jpg"
    save_path = os.path.join(save_dir, filename)

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        print(f"✅ 下载成功：{url} -> {save_path}")
        return True
    except Exception as e:
        print(f"❌ 下载失败：{url}，错误：{str(e)}")
        # 写入失败URL到文件（追加模式）
        with open("fail_list.txt", "a", encoding="utf-8") as f:
            f.write(f"{url}\n")  # 每行一个URL，便于后续重新下载
        return False


def read_urls_from_txt(txt_path):
    """
    从txt文件读取URL列表（每行一个URL）
    :param txt_path: txt文件路径（相对/绝对路径均可）
    :return: 去重后的有效URL列表
    """
    url_list = []
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()  # 去除首尾空格、换行符
                # 过滤空行和无效URL（简单校验是否包含http）
                if url and ("http://" in url or "https://" in url):
                    url_list.append(url)
        # 去重（避免重复下载）
        url_list = list(set(url_list))
        print(f"📊 从 {txt_path} 读取到 {len(url_list)} 个有效URL")
        return url_list
    except Exception as e:
        print(f"❌ 读取txt文件失败：{str(e)}")
        return []


if __name__ == '__main__':
    # -------------------------- 核心配置 --------------------------
    txt_file_path = "weilong.txt"  # txt文件路径（改为你的文件路径，如 "./data/urls.txt"）
    save_dir = "weilong_downloaded_images"  # 图片保存目录
    # --------------------------------------------------------------

    # 1. 读取txt中的URL
    url_list = read_urls_from_txt(txt_file_path)
    if not url_list:
        print("❌ 无有效URL，退出下载")
        exit()

    # 2. 批量下载（单线程）
    print("🚀 开始下载...")
    for url in url_list:
        download_image(url, save_dir)
    print("📥 下载完成！")