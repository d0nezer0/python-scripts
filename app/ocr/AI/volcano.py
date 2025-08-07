import json

import requests


ARK_API_KEY = "b2e0f0c6-2e77-4847-89d8-c0a174744d36"
# junjie bot
MODEL = "bot-20250605224120-k85d9"


# 文档： https://console.volcengine.com/ark/region:ark+cn-beijing/assistant/edit?id=bot-20250605224120-k85d9&botType=NoCode&formType=edit&templateType=InfoSource&tab=Edit
def get_by_request(content):
    url = 'https://ark.cn-beijing.volces.com/api/v3/bots/chat/completions'

    headers = {
        "Authorization": "Bearer " + ARK_API_KEY,
        'Content-Type': 'application/json'
    }

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    }

    print("原始内容： " + content)

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # 检查请求是否成功
        print("请求成功")
        data = json.dumps(response.json(), indent=4, ensure_ascii=False)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP错误: {http_err}")
        if response.status_code == 401:
            print("可能是API密钥无效或未授权")
        elif response.status_code == 404:
            print("请求的资源不存在")
        data = f"响应内容: {response.text}"
    except requests.exceptions.RequestException as req_err:
        data = f"请求异常: {req_err}"
    except json.JSONDecodeError as json_err:
        print(f"JSON解析错误: {json_err}")
        data = f"原始响应内容: {response.text}"

    print(data)
    return(data)


if __name__ == '__main__':
    # streaming()
    content = ""
    get_by_request(content)
