import httpx
import time
from pathlib import Path

base_url = "http://beebo.xuanyibeikafei.xyz/cross/wall/post/audio"

query_params = {"url": "https://api.openai.com/v1/audio/transcriptions"}


audio_path = "/Users/zhoudong/Movies/001 开发相关/mp3/1.mp3"
headers = {
    "Authorization": f"Bearer xxxxxxxxxx",
    "User-Agent": "Mozilla/5.0"
}
data = {
    "model": "gpt-4o-transcribe",
}


def post_audion():

    # 检查文件是否存在
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"文件不存在: {audio_path}")

    # 获取文件大小（MB）
    file_size_mb = Path(audio_path).stat().st_size / (1024 * 1024)
    print(f"文件大小: {file_size_mb:.2f} MB")

    # 创建客户端
    client = httpx.Client(
        timeout=httpx.Timeout(timeout=30.0, connect=10.0),
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )

    try:
        # 以二进制读取模式打开文件
        with open(audio_path, "rb") as audio_file:

            # 使用 httpx 发送 POST 请求
            # with httpx.Client() as client:
            #     response = client.post(base_url, params=query_params, headers=headers, data=data, files=files)
            #
            #     # 检查响应状态码并打印结果
            #     response.raise_for_status()  # 如果请求失败 (状态码不是 2xx), 将会抛出异常
            #     print("请求成功!")
            #     print("响应内容:", response.json())
            files = {
                "file": (audio_path, audio_file, "audio/mpeg")
            }

            # 发送请求
            response = client.post(
                url=base_url,
                params=query_params,
                headers=headers,
                files=files
            )

            print(f"状态码: {response.status_code}")

            if response.status_code == 200:
                print("请求成功!")
                return response.json() if response.headers.get(
                    "content-type") == "application/json" else response.text
            else:
                print(f"服务器返回错误: {response.status_code}")
                print(f"响应内容: {response.text}")

    except httpx.ConnectError as e:
        print(f"连接错误: {e}")
    except httpx.ReadTimeout as e:
        print(f"读取超时: {e}")
    except httpx.WriteTimeout as e:
        print(f"写入超时: {e}")
    except httpx.PoolTimeout as e:
        print(f"连接池超时: {e}")
    except httpx.HTTPStatusError as e:
        print(f"HTTP状态错误: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"请求错误: {e}")
    except Exception as e:
        print(f"未知错误: {type(e).__name__} - {e}")
    finally:
        client.close()


if __name__ == '__main__':

    post_audion()