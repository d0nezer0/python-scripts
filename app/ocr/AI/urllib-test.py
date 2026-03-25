import urllib3
import os
from urllib3.fields import RequestField
from urllib3.filepost import encode_multipart_formdata

http = urllib3.PoolManager()

url = "http://43.153.42.246:8080/cross/wall/post/audio"
params = {
    "url": "https://api.openai.com/v1/audio/transcriptions"
}

headers = {
    "source": "My-BEEBO-Group",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

filepath = "/Users/zhoudong/Movies/001 开发相关/mp3/1.mp3"
form_data = {
    "model": "gpt-4o-transcribe"
}

try:
    # 读取文件内容
    with open(filepath, "rb") as audio_file:
        file_content = audio_file.read()

    # 创建multipart表单数据
    fields = []

    # 添加文件字段
    file_field = RequestField(
        name="file",
        data=file_content,
        filename=os.path.basename(filepath),
        headers={"Content-Type": "audio/mpeg"}
    )
    fields.append(file_field)

    # 添加其他表单字段
    for name, value in form_data.items():
        fields.append((name, value))

    # 编码multipart表单数据
    body, content_type = encode_multipart_formdata(fields)

    # 添加Content-Type头
    headers["Content-Type"] = content_type

    # 发送请求
    response = http.request(
        "POST",
        url,
        fields=params,
        body=body,
        headers=headers,
        timeout=urllib3.Timeout(connect=10.0, read=60.0)
    )

    print(f"状态码: {response.status}")
    print(f"响应内容: {response.data.decode('utf-8')}")

except Exception as e:
    print(f"请求时发生错误: {e}")
