import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def query():
    url = "http://beebo.xuanyibeikafei.xyz/cross/wall/post/audio?url=https://api.openai.com/v1/audio/transcriptions"

    payload = {'model': 'gpt-4o-transcribe'}
    files = [
        ('file', ('1.mp3', open('/Users/zhoudong/Movies/001开发相关/mp3/1.mp3', 'rb'), 'audio/mpeg'))
    ]
    headers = {
        'source': 'My-BEEBO-Group'
    }

    # 配置重试策略
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        response = session.request("POST", url, headers=headers, data=payload, files=files, timeout=10)
        response.raise_for_status()  # 检查HTTP错误
        print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")


if __name__ == '__main__':
    query()

