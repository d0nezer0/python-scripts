import time
import boto3
from botocore.exceptions import ClientError
from boto3.session import Config
import csv
import requests
import json
import os
from meituan_auto_crawl_util import query_data_list
from datetime import datetime

def create_s3_client(endpoint_url, access_key):
	"""
	初始化 S3 客户端 (path style)
	:param endpoint_url: S3 兼容服务的 Endpoint 地址，例如 "https://s3.meituan.com"
	:param access_key: 账号的 Access Key (APP_KEY)
	:param secret_key: 账号的 Secret Key
	:param region: 区域 (默认 us-east-1，兼容 S3 服务一般都能用)
	:return: s3 client
	"""
	s3 = boto3.client(
		"s3",
		aws_access_key_id="SRV_R7vPGoCfcnXAEVFp6bL1hve4xsWQhGju",
		aws_secret_access_key="8wif1yLIsc7uq058aYIsnJlcB8npeFll",
		endpoint_url=endpoint_url,
		# region_name=region,
		config=Config(s3={"addressing_style": "path"})  # 等价于 Java 的 setPathStyleAccess(true)
	)
	return s3


def download_from_s3(s3_client, bucket_name, object_key, local_file):
	"""
	下载 S3 文件到本地
	"""
	try:
		s3_client.download_file(bucket_name, object_key, local_file)
		print(f"✅ 下载成功: s3://{bucket_name}/{object_key} -> {local_file}")
	except ClientError as e:
		print("❌ AWS 客户端异常")
		print("Error Message:", e.response["Error"]["Message"])
		print("HTTP Status Code:", e.response["ResponseMetadata"]["HTTPStatusCode"])
		print("Error Code:", e.response["Error"]["Code"])
		print("Request ID:", e.response["ResponseMetadata"]["RequestId"])
	except Exception as e:
		print("❌ 其他异常:", str(e))


def read_and_split_txt(file_path):
	data_list = []
	with open(file_path, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if line:  # 跳过空行
				parts = line.split("##&**&@@")
				data_list.append(parts)
	return data_list


##发邮件
def send_message(push_id: int, mail_model: object):
	base_url = "http://message-inf.sankuai.com/api/send/message/v2/mail"
	
	# 公共参数
	common = {
		"pushId": push_id,
		"uniqueId": str(int(time.time() * 1000)) + "csv",
		"idempotent": 1,
		"sendTime": int(time.time() * 1000),
		"expireTime": int(time.time() * 1000)
	}
	print("发送邮件UniqueId：", common["uniqueId"])
	mail_model["common"] = common
	mail_models = [mail_model]
	# 转换为 JSON
	data = json.dumps(mail_models, ensure_ascii=False)
	headers = {
		"Content-Type": "application/json",
		"appkey":"com.sankuai.movie.basedata.library"
	}
	# 发送 POST 请求
	response = requests.post(base_url, data=data.encode("utf-8"), headers=headers)
	return response.text

def upload_file(path_name: str) -> str | None:
	url = "http://message-inf.sankuai.com/api/file/upload"  # 替换成实际地址
	try:
		with open(path_name, "rb") as f:
			files = {"file": f}
			response = requests.post(url, files=files)
		if response.status_code == 200:
			result = response.text
			json_object = json.loads(result)
			if json_object.get("status") != 0:
				print(f"upload fail, error message: {json_object.get('errMsg')}")
				return None
			# 返回上传后的文件名（data 字段）
			return json_object.get("data")
		print(f"upload fail, error message: {response.status_code}")
		return None
	except Exception as e:
		print("upload exception:", e)
		return None

def merge_search_res_to_list():
	file2_path = "meituan_search_res.csv"
	file1_path = "meituan_search_query_list.csv"
	output_path = "meituan_search_query_list_output.csv"

	# 读取 file2，构建映射（第一列 -> 第二列）
	mapping = {}
	mapping_detail = {}
	with open(file2_path, "r", encoding="utf-8") as f2:
	    reader2 = csv.reader(f2)
	    for row in reader2:
	        if len(row) >= 2:  
	            mapping[row[0]] = row[2]
	            mapping_detail[row[0]] = row[4]

	# 处理 file1 并写入新文件
	with open(file1_path, "r", encoding="utf-8") as f1, \
	     open(output_path, "w", encoding="utf-8", newline="") as fout:
	    reader1 = csv.reader(f1)
	    writer = csv.writer(fout)
	    # 写表头
	    writer.writerow(['项目id','项目名','类别','状态','点评shopid','商家名','商家地址','美团poiid','美团商家名','美团商家地址', '搜索词', "是否展示演出模块", "美团景点poi_id"])
	    for row in reader1:
	        if len(row) >= 5:  # 确保有5列
	            col1, col2, col3,  col6, col7, col8, col9, col10, col11, col12, col13 = row[0], row[1], row[2], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12]
	            mapped_value = mapping.get(col13, "")  # 找到映射值，如果没有就空
	            poid_id = mapping_detail.get(col13, "")
	            writer.writerow([col1, col2, col3, col6, col7, col8, col9, col10, col11, col12, col13, mapped_value, poid_id])
	print(f"处理完成，结果已保存到 {output_path}")


if __name__ == "__main__":

	s3_file_res = requests.request('GET', 'http://10.19.129.163:8080/loki/public/getMtSearchPoiS3FileId').json()
	print(s3_file_res)
	# # === 配置参数 ===
	ENDPOINT = "http://mss.vip.sankuai.com"	 # Java 里的 ENDPOINT_NET
	APP_KEY = "com.sankuai.movie.bigdata.moviemeta"			# Java 里的 APP_KEY
	
	BUCKET = "data-train"
	OBJECT_KEY = "mt_dasou_scenic_spots_show_project_info/" + str(json.loads(s3_file_res)['objectName'])	 # S3 里的 key
	LOCAL_PATH = "meituan_search_query_list.txt"		   # 本地保存路径

	# # # === 初始化客户端 ===
	s3_client = create_s3_client(ENDPOINT, APP_KEY)

	# # # === 下载文件 ===
	download_from_s3(s3_client, BUCKET, OBJECT_KEY, LOCAL_PATH)

	data_list = read_and_split_txt('meituan_search_query_list.txt')

	search_query_list = []
	file = 'meituan_search_query_list.csv'
	for i in range(len(data_list)):
		project_name = data_list[i][1]
		print(project_name)
		res = requests.request('GET', 'https://smart.maoyan.com/movie/algo/common/service/meituan/show/search-keyword?showIntro=' + str(project_name),verify=False)
		print(res.text)
		res_data = json.loads(res.text)
		if res_data['code'] == 200:
			searchKeyword = res_data['data']['searchKeyword']
			data_list[i].append(searchKeyword)
			search_query_list.append(searchKeyword)
		else:
			data_list[i].append('')

		with open(file, 'a', encoding='utf-8', newline='') as csvfile:
			header = ['项目id','项目名','类别','售卖渠道','售卖渠道id','状态','商家id','商家名','商家地址','美团商家id','美团商家名','美团商家地址', '搜索词']
			dictWriter = csv.DictWriter(csvfile, fieldnames=header)
			file_exists = os.path.isfile(file)
			if not file_exists:
				dictWriter.writeheader()
			dictWriter.writerow({'项目id': data_list[i][0], '项目名': data_list[i][1], '类别': data_list[i][2], '售卖渠道': data_list[i][3], '售卖渠道id':data_list[i][4], "状态":data_list[i][5],  "商家id":data_list[i][6], "商家名":data_list[i][7], "商家地址":data_list[i][8], "美团商家id":data_list[i][9], "美团商家名":data_list[i][10], "美团商家地址":data_list[i][11], "搜索词":data_list[i][12] })
	# === 配置抓取 === 
	# search_query_list = ['蜀韵园川剧变脸', '音乐剧《熊猫》', '红色娘子军演出', '亲子魔术嘉年', '印象刘三姐', '恰同学少年沉浸式剧场', '梦幻腾冲', '又见平遥', '今夕共西溪', '琴岛之夜', '丝绸之路 千年印象','蜀风雅韵变脸秀','嘻哈包袱铺相声','苍穹VR沉浸体验','重庆·1949','七彩鸿星萌宠乐园','鲁镇社戏','极限快乐2','ERA时空之旅2','芙蓉国粹川剧变脸秀','灵玲国际大马戏','名流相声茶馆','西岸相声专场','大唐女皇']
	# print(search_query_list)

	restart_app_times = int(len(search_query_list)/40)+1
	print(search_query_list)
	for i in range(restart_app_times):
		print('----------------------------------------------')
		# print(search_query_list[i*30: (i+1)*30])
		query_data_list(search_query_list[i*40:(i+1)*40])
		print('----------------------------------------------')

	# == 数据合并 ==
	merge_search_res_to_list()
	# === 发送邮件 === 
	# print(upload_file('meituan_search_query_list_output.csv'))

	file_name = upload_file('meituan_search_query_list_output.csv')

	to = 'niuran@maoyan.com'
	to1 = 'lizhihao07@maoyan.com'
	now = datetime.now()
	formatted = now.strftime("%Y-%m-%d")
	msg = str(formatted) + '美团大搜景点重合意图POI搜索效果自动化监控'

	title = str(formatted) + '美团大搜景点重合意图POI搜索效果自动化监控'
	mail_model = {
		"tos": [to,to1],
		 "subject": title,
		 "content": msg,
		 "attachments": {
		 	"美图搜索重合POI结果.csv":str(file_name)
		 }
	}

	result = send_message(
		 push_id=24234,
		 mail_model = mail_model
	)
	print(result)