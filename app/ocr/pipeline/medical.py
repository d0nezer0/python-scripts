# coding=utf-8
import requests

from app.ocr.pipeline.ocr_subtitle import OcrSubtitlePipline


def ocr_by_url(img_url):
    response = requests.get(img_url)
    if response.status_code == 200:
        with open("tmp.png", 'wb') as f:
            f.write(response.content)
            ocr_subtitle = OcrSubtitlePipline()
            preds = ocr_subtitle.forward("tmp.png", show_res=True)
            # 在这里解析了， 返回对应 json ；
            print(preds)
            return preds
    else:
        print(f"Failed to download image, status code: {response.status_code}")
        return None


def ocr_by_path(img_path):
    ocr_subtitle = OcrSubtitlePipline()
    preds = ocr_subtitle.forward(img_path, show_res=True)

    # 在这里解析了， 返回对应 json ；

    return preds


if __name__ == '__main__':

    output_folder = 'extracted_images'  # 图片输出文件夹
    preds = ocr_by_url("https://p0.pipi.cn/mediaplus/bigdata_mmdb_mmdbtask/0fa3345bea45c249489a139250855171e8d67.png?imageView2/1/w/464/h/644")



    # 列出指定目录下的所有.txt文件
    # for filename in os.listdir(directory):
    #     if filename.endswith(".pdf"):  # 仅匹配.txt文件
    #         filepath = os.path.join(directory, filename)
    #         pdf_list.append(filepath)

    # pdf_list.append("/Users/zhoudong/projects/maoyan/movie-data-automation/performance/pdf/ComplexCon 2025 Mar 23/maoyan/Mar 23 Sun T1M 坐位 1788/maoyan_367張/Block 14/20250227182934129128.pdf")
