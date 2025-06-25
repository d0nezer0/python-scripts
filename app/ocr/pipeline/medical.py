# coding=utf-8
import re

import requests

from app.ocr.pipeline.ocr_subtitle import OcrSubtitlePipline

# 定义指标名称与数据库字段的映射关系
target_mapping = {
    "Fk506": "fk506_concentration",
    "血肌酐": "serum_creatinine",
    "尿素氮": "blood_urea_nitrogen",
    "尿酸": "uric_acid",
    "血红蛋白": "hemoglobin",
    "血小板": "platelets",
    "白细胞": "white_blood_cells",
    "C反应蛋白": "c_reactive_protein",
    "霉芬酸三点法": "mycophenolic_acid_method",
    "血糖": "blood_glucose",
    "丙氨酸氨基转移酶": "alt",
    "天门冬氨酸氨基转移酶": "ast",
    "总胆红素": "total_bilirubin",
    "直接胆红素": "direct_bilirubin",
    "总蛋白": "total_protein",
    "白蛋白": "albumin",
    "尿素": "urea",
    "血肌酐": "serum_creatinine_duplicate",
    "肾小球滤过率": "glomerular_filtration_rate",
    "钾": "potassium",
    "钠": "sodium",
    "总胆固醇": "total_cholesterol",
    "甘油三酯": "triglycerides",
    "高密度脂蛋白胆固醇": "hdl_cholesterol",
    "低密度脂蛋白胆固醇": "ldl_cholesterol",
    "巨细胞病毒DNA载量": "cmv_dna_load",
    "血BK病毒定性检测": "blood_bkv",
    "血BK病毒DNA载量": "blood_bkv_dna_load",
    "尿蛋白定性": "urine_protein",
    "24小时尿蛋白定量": "urine_protein_24h",
    "尿BK病毒定性检测": "urine_bkv",
    "尿BK病毒DNA载量": "urine_bkv_dna_load",
    "PRA抗体": "pra_antibody"
}


def ocr_by_url(img_url):
    response = requests.get(img_url)
    if response.status_code == 200:
        with open("tmp.png", 'wb') as f:
            f.write(response.content)
            data = ocr_by_path("tmp.png")
            return data
    else:
        print(f"Failed to download image, status code: {response.status_code}")
        return None


def ocr_by_path(img_path):
    ocr_subtitle = OcrSubtitlePipline()
    preds = ocr_subtitle.forward(img_path, show_res=True)
    # 在这里解析了， 返回对应 json ；
    print(preds)
    # 用于存储匹配后的数据，结构和数据库字段对应
    result_data = {
        "fk506_concentration": None, 		# 'Fk506浓度(ng/mL)'
        "serum_creatinine": None, 			# '血肌酐(μmol/L)'
        "blood_urea_nitrogen": None, 		# '尿素氮(mmol/L)'
        "uric_acid": None, 					# '尿酸(μmol/L)'
        "hemoglobin": None, 				# '血红蛋白(g/L)'
        "platelets": None, 					# '血小板(×10^9/L)'
        "white_blood_cells": None, 			# '白细胞(×10^9/L)'
        "c_reactive_protein": None, 		# 'C反应蛋白(mg/L)'
        "mycophenolic_acid_method": None, 	# '霉芬酸三点法'
        "blood_glucose": None, 				# '血糖(mmol/L)'
        "alt": None, 					    # '丙氨酸氨基转移酶(U/L)'
        "ast": None, 					    # '天门冬氨酸氨基转移酶(U/L)'
        "total_bilirubin": None, 			# '总胆红素(μmol/L)'
        "direct_bilirubin": None, 			# '直接胆红素(μmol/L)'
        "total_protein": None, 				# '总蛋白(g/L)'
        "albumin": None, 					# '白蛋白(g/L)'
        "urea": None, 					    # '尿素(mmol/L)'
        "serum_creatinine_duplicate": None, # '血肌酐(重复项μmol/L)'
        "glomerular_filtration_rate": None, # '肾小球滤过率(mL/min/1.73m²)'
        "potassium": None, 					# '钾(mmol/L)'
        "sodium": None, 					# '钠(mmol/L)'
        "total_cholesterol": None, 			# '总胆固醇(mmol/L)'
        "triglycerides": None, 				# '甘油三酯(mmol/L)'
        "hdl_cholesterol": None, 			# '高密度脂蛋白胆固醇(mmol/L)'
        "ldl_cholesterol": None, 			# '低密度脂蛋白胆固醇(mmol/L)'
        "cmv_dna_load": None, 				# '巨细胞病毒DNA载量'
        "blood_bkv": None, 					# '血BK病毒定性检测'
        "blood_bkv_dna_load": None, 		# '血BK病毒DNA载量(copies/mL)'
        "urine_protein": None, 				# '尿蛋白定性'
        "urine_protein_24h": None, 			# '24小时尿蛋白定量(g/24h)'
        "urine_bkv": None, 					# '尿BK病毒定性检测'
        "urine_bkv_dna_load": None, 		# '尿BK病毒DNA载量(copies/mL)'
        "pra_antibody": None, 				# 'PRA抗体'
    }

    # 使用索引遍历，便于访问下一个元素
    i = 0
    while i < len(preds):
        item = preds[i]
        text = item[1][0]

        # 检查当前项是否包含目标指标名称
        for keyword, field in target_mapping.items():
            if keyword in text:
                # 找到指标名称后，尝试获取下一个 item 中的值
                if i + 1 < len(preds):
                    next_item = preds[i + 1]
                    next_text = next_item[1][0]

                    # 使用正则提取数值部分
                    value_match = re.search(r'(\d+(?:\.\d+)?)', next_text)
                    if value_match:
                        value = value_match.group(1)

                        # 根据字段类型转换数据
                        if field == "platelets":
                            result_data[field] = int(float(value))
                        else:
                            result_data[field] = float(value)

                        # 成功匹配后，跳过已处理的下一个 item
                        i += 1
                        break  # 跳出内层循环

            # 移动到下一个 item
            i += 1


    print(result_data)

    return result_data


if __name__ == '__main__':

    # preds = ocr_by_url("https://p0.pipi.cn/mediaplus/bigdata_mmdb_mmdbtask/0fa3345bea45c249489a139250855171e8d67.png?imageView2/1/w/464/h/644")
    preds = ocr_by_path("/Users/zhoudong/Pictures/jj/WechatIMG32.jpg")


    # 列出指定目录下的所有.txt文件
    # for filename in os.listdir(directory):
    #     if filename.endswith(".pdf"):  # 仅匹配.txt文件
    #         filepath = os.path.join(directory, filename)
    #         pdf_list.append(filepath)

    # pdf_list.append("/Users/zhoudong/projects/maoyan/movie-data-automation/performance/pdf/ComplexCon 2025 Mar 23/maoyan/Mar 23 Sun T1M 坐位 1788/maoyan_367張/Block 14/20250227182934129128.pdf")
