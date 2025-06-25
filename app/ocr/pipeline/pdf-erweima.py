# coding=utf-8
import csv
import os
import re

import fitz  # PyMuPDF
# import pdfplumber
import cv2
from PIL import Image
import qrcode
import pytesseract
from performance.ocr.pipeline.ocr_subtitle import OcrSubtitlePipline


# # pyzbar 不支持 python 3.11 及以上版本
# from pyzbar.pyzbar import decode


# # 打开PDF文件
# def test_pdfplumber(pdf_path):
#     with pdfplumber.open(pdf_path) as pdf:
#         # 遍历每一页
#         for page in pdf.pages:
#             text = page.extract_text()
#             print(text)


def test_fitz(pdf_path):
    # 打开PDF文件
    doc = fitz.open(pdf_path)

    # 遍历每一页
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        print(text)


# 部分图片识别不出二维码， 所以把第三张指定为 二维码图；
def extract_images_from_pdf(pdf_path, output_folder):
    img_list = []
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    # 遍历每一页
    for page_num in range(len(doc)):
        page = doc[page_num]
        # 获取页面上的图片列表
        image_list = page.get_images(full=True)
        # 遍历图片列表
        for img_index, img in enumerate(image_list, start=1):
            xref = img[0]  # XREF是图片在PDF中的引用编号
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            # 获取图片的文件名和扩展名
            image_ext = base_image["ext"]
            image_filename = f"{pdf_path}" + f"---image_page{page_num + 1}_{img_index}.{image_ext}"
            # 只保持第三张，
            if "---image_page1_3" in image_filename:
                # 图片输出路径
                image_path = os.path.join(output_folder, image_filename)
                # 保存图片
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                return image_filename
        print(f"处理异常， 无第三张二维码图， path = {pdf_path}")


# # python3.11 版本不支持
# def decode_qrcode(img_path):
#     # 读取图像文件
#     image = cv2.imread(img_path)
#     # 使用pyzbar库解码二维码
#     qr_codes = decode(image)
#     # 遍历找到的所有二维码
#     for qr_code in qr_codes:
#         # 打印二维码数据
#         print(f"QR Code Data: {qr_code.data.decode('utf-8')}")

def get_qrcode(img_path):
    # 如果是 page1_3.png 结尾的， 当做 pdf 来的图片， 进行截取后识别召回率会变高；
    if "page1_3.png" in img_path:
        with Image.open(img_path) as img:
            # 设置裁剪区域为一个元组（左, 上, 右, 下）
            # 注意：坐标是从左上角开始计算的，且第一个数字是x坐标，第二个数字是y坐标
            # area = (100, 100, 400, 400)  # 例如，裁剪从(100, 100)到(400, 400)的区域
            area = (900, 110, 1120, 310)  # 例如，裁剪从(100, 100)到(400, 400)的区域
            # 裁剪图像
            cropped_img = img.crop(area)
            # 保存裁剪后的图像
            cropped_img.save(img_path + "cut.png")
        # 使用新图截取；
        img_path += "cut.png"

    det = cv2.QRCodeDetector()
    image = cv2.imread(img_path)

    try:
        val, pts, st_code = det.detectAndDecode(image)
        return val
    except Exception as e:
        print(f"eeee = {e}")
        return None


def detect_qr_code(image_path):
   # 读取图片
   image = cv2.imread(image_path)
   # 初始化 OpenCV 的二维码检测器
   detector = cv2.QRCodeDetector()
   # 解析二维码
   data, bbox, _ = detector.detectAndDecode(image)
   if bbox is not None and data:
       print(f"检测到二维码: {data}")
       # 画出二维码边界
       for i in range(len(bbox)):
           point1 = tuple(bbox[i][0])
           point2 = tuple(bbox[(i + 1) % len(bbox)][0])
           cv2.line(image, (int(point1[0]), int(point1[1])), (int(point2[0]), int(point2[1])), (0, 255, 0), 2)
       # 显示标注后的图片
       cv2.imshow("QR Code Detection", image)
       cv2.waitKey(0)
       cv2.destroyAllWindows()
   else:
       print("未检测到二维码")


def generate_qrcode(data, name):
    # 创建二维码对象
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    # 添加数据
    qr.add_data(data)
    qr.make(fit=True)

    # 保存为图片文件
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"extracted_images/{name}.png")


# def suanfa_ocr(img_path):
#     ocr_subtitle = OcrSubtitlePipline()
#     preds = ocr_subtitle.forward(img_path, show_res=True)
#
#     # 在这里解析了。
#     # 如果无座位， 处理；
#     zone, price, seatZone, seatNum = None, None, None, None
#     if "FREE STANDING" in str(preds) or "FREESTANDING" in str(preds):
#         if "BLOCK" in str(preds[17]):
#             zone = preds[17][1][0]
#         if "HKD" in str(preds[20]):
#             price = preds[20][1][0]
#         seatZone, seatNum = "FREE STANDING", "不設位"
#     else:
#         if "BLOCK" in str(preds[16]):
#             zone = preds[16][1][0]
#         if "HKD" in str(preds[19]):
#             price = preds[19][1][0]
#         # 存在识别座位字符串连在一起的情况  如 "z22"
#         # 正则表达式匹配字母和数字，字母和数字之间可能有空格（多个）
#         pattern = re.compile(r'([a-zA-Z]+)(?:\s*)(\d+)')
#         match = pattern.search(preds[-2][1][0])
#         if match:
#             # 将匹配的字母和数字分别添加到结果列表中
#             seatZone, seatNum = match.group(1), match.group(2)
#     if zone is None or price is None:
#         print(f"行数不对， 重新赋值")
#         for pred in preds:
#             if zone is None and "BLOCK" in str(pred):
#                 zone = pred[1][0]
#             if price is None and "HKD" in str(pred):
#                 price = pred[1][0]
#     if seatZone is None:
#         print(f"sss = {preds[-2]}")
#         print(f"sss = {preds[-2][1][0]}")
#
#     # 返回 区域、 价格、 座位号；
#     return zone, price, seatZone, seatNum


# 这种票格式不一样；
def suanfa_ocr(img_path):
    ocr_subtitle = OcrSubtitlePipline()
    preds = ocr_subtitle.forward(img_path, show_res=True)

    # 在这里解析了。
    # 如果无座位， 处理；
    zone, price, seatZone, seatNum = None, None, None, None
    if "FREE STANDING" in str(preds) or "FREESTANDING" in str(preds):
        if "BLOCK" in str(preds[17]):
            zone = preds[17][1][0]
        if "HKD" in str(preds[20]):
            price = preds[20][1][0]
        seatZone, seatNum = "FREE STANDING", "不設位"
    elif "潮流市集" in str(preds):
        zone = "特殊处理"
        if "HKD" in str(preds[18]):
            price = preds[18][1][0]
        seatZone = "潮流市集"
        if "2025/" in str(preds[19]):
            seatNum = preds[19][1][0]
        if price is None or seatNum is None:
            for pred in preds:
                if price is None and "HKD" in str(pred):
                    price = pred[1][0]
                if seatNum is None and "2025/" in str(pred):
                    seatNum = pred[1][0]
    else:
        if "BLOCK" in str(preds[16]):
            zone = preds[16][1][0]
        if "HKD" in str(preds[19]):
            price = preds[19][1][0]
        # 存在识别座位字符串连在一起的情况  如 "z22"
        # 正则表达式匹配字母和数字，字母和数字之间可能有空格（多个）
        pattern = re.compile(r'([a-zA-Z]+)(?:\s*)(\d+)')
        match = pattern.search(preds[-2][1][0])
        if match:
            # 将匹配的字母和数字分别添加到结果列表中
            seatZone, seatNum = match.group(1), match.group(2)
    if zone is None or price is None:
        print(f"行数不对， 重新赋值")
        for pred in preds:
            if zone is None and "BLOCK" in str(pred):
                zone = pred[1][0]
            if price is None and "HKD" in str(pred):
                price = pred[1][0]
    if seatZone is None:
        print(f"sss = {preds[-2]}")
        print(f"sss2 = {preds[-2][1][0]}")

    # 返回 区域、 价格、 座位号；
    return zone, price, seatZone, seatNum


def extract_text_from_image(image_path):
    # Read the image using OpenCV
    img = cv2.imread(image_path)

    # Use Tesseract OCR to extract text
    text_data = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
    """
    COMPLEXCON if assweiersno semanas a
    a
    cpa rg ne
    
    For concert tickets, age limit for Standing zone: 12 or above and Height limit: 140 em or above. ono Fa} oF
    
    OBST > ARERR © RARE > RETR: OMSL - pee Lee
    
    One person per ticket. are ae i
    S ei OF yo
    
    SRR) - OP es
    
    Tickets sold are non-transferable, non-refundable and non exchangeable.
    
    jE ELBTPIRRR - RALBEK + RABEL - AWA
    
    No re-issue of any lost ticket will be processed under any circumstances. 2025/03/21
    
    FLA > BAW BA - (FRI)
    
    —_—_—Rt’}’\\€’‘w}?},”?’Ti‘ilrle oo — BLOCK 4
    
    Date Ai Ticket Type HKD1,790
    
    2025/03/21 STANDARD A 25
    
    Concert Zone 305 iat Price SF Seat Haft PRINTED: 28JAN10:33
    
    BLOCK 4 HKD1,790 A 25 20250128103300866001#
    """
    # 默认站席
    seat_info = "FREE STANDING"

    try:
        if "FREE STANDING" not in text_data:
            seat_info = text_data.split("STANDARD ")[1].split("Concert Zone")[0].strip()
    except Exception as e:
        try:
            seat_info = text_data.split("Marketplace ")[1].split("Concert Zone")[0].strip()
        except Exception as e2:
            seat_info = "未解析出座位"
            print(f"文件位置 = {image_path}")

    return seat_info


if __name__ == '__main__':
    # pdf_path = 'Complexcon 2025 E-ticket.pdf'
    # img_path = 'extracted_images/image_page1_3.png'

    # 使用示例  读不出文字；
    # test_pdfplumber(pdf_path)
    # test_fitz(pdf_path)

    output_folder = 'extracted_images'  # 图片输出文件夹

    pdf_list = []
    directory = '/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/20250317_MAOYAN-batch8'

    # 列出指定目录下的所有.txt文件
    # for filename in os.listdir(directory):
    #     if filename.endswith(".pdf"):  # 仅匹配.txt文件
    #         filepath = os.path.join(directory, filename)
    #         pdf_list.append(filepath)
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            if filename.endswith(".pdf"):  # 仅匹配.txt文件
                filepath = os.path.join(root, filename)
                pdf_list.append(filepath)

    print(f"pdf 文件数量 = {len(pdf_list)}")

    # pdf_list.append("/Users/zhoudong/projects/maoyan/movie-data-automation/performance/pdf/ComplexCon 2025 Mar 23/maoyan/Mar 23 Sun T1M 坐位 1788/maoyan_367張/Block 14/20250227182934129128.pdf")

    with open("0317-batch8-qrcode.csv", mode='a', newline='', encoding='utf-8') as file:
        # 创建CSV写入对象
        writer = csv.writer(file)
        # 写入数据
        writer.writerow(["filePath", "qrcode", "zone", "price", "seatZone", "seatNum"])

    for pdf_path in pdf_list:
        # 单个 pdf 文件处理；
        img_path = extract_images_from_pdf(pdf_path, output_folder)
        qrcode_str = get_qrcode(img_path)
        print(f"doing path = {img_path}")
        if len(qrcode_str) < 10:
            print(f"二维码识别失败， 请注意！！！ path = {img_path}")
        # # 不准， 使用下面算法同学的结果；
        # seat_info = extract_text_from_image(img_path)
        # 算法的 orc 识别；
        zone, price, seatZone, seatNum = suanfa_ocr(img_path)
        # print(f"img_path = {img_path.split('---image_page')[0]}, qrcode = {qrcode_str} , "
        #       f"seat_info = {seatZone}, ' ', {seatNum}")
        row = [img_path, qrcode_str, zone, price, seatZone, seatNum]
        # with open('0310-qrcode.txt', 'a') as file:
        #     # 写入一行文本
        #     file.write(f"img_path = {img_path.split('---image_page')[0]}, qrcode = {qrcode_str} , "
        #                f"seat_info = {seatZone}, ' ', {seatNum}\n")
        with open("0317-batch8-qrcode.csv", mode='a', newline='', encoding='utf-8') as file:
            # 创建CSV写入对象
            writer = csv.writer(file)
            # 写入数据
            writer.writerow(row)
        # generate_qrcode(qrcode_str, qrcode)

        # qrcode = get_qrcode(img_path)
        # print(f"img_path = {img_path}, qrcode = {qrcode}")

        # Assuming the QR data is a string containing all ticket details
        # seat_info = extract_seat_info(qr_data)

    # img_path = "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/ComplexCon 2025 Mar 23/maoyan/Mar 23 Sun T3M 坐位 988/maoyan_584張/Block 8/20250227184033146047.pdf---image_page1_3.png"
    #
    # img_list = [
    #     "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/ComplexCon 2025 Mar 23/uutix/Mar 23_T2S 站位 1388/uutix_114張/20250227173230020224.pdf---image_page1_3.png",
    #     "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/ComplexCon 2025 Mar 23/uutix/Mar 23_T2S 站位 1388/uutix_114張/20250227173230020250.pdf---image_page1_3.png",
    #     "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/ComplexCon 2025 Mar 23/uutix/Mar 23_T2S 站位 1388/uutix_114張/20250227173230020324.pdf---image_page1_3.png",
    #     "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/ComplexCon 2025 Mar 23/uutix/Mar 23_T2S 站位 1388/uutix_114張/20250227173230020281.pdf---image_page1_3.png",
    #     "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/ComplexCon 2025 Mar 23/uutix/Mar 23_T2S 站位 1388/uutix_114張/20250227173230020280.pdf---image_page1_3.png"
    # ]
    #
    # # img_path = "/Users/zhoudong/downloads/zz.png"
    # for img_path in img_list:
    #     qrcode_str = get_qrcode(img_path)
    #     print(f"sss = {qrcode_str}")

    # img_path = "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/0314-ComplexCon_Market Place_GA/Mar 22 Sat GA/20250304114020397149.pdf---image_page1_3.png"
    # "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/0314-ComplexCon_Market Place_GA/Mar 22 Sat GA/20250304114020397149.pdf---image_page1_3.png"
    # img_path = "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/0314-ComplexCon_Market Place_GA/Mar 23 Sun GA/20250304152241228100.pdf---image_page1_3.png"
    # zone, price, seatZone, seatNum = suanfa_ocr(img_path)
