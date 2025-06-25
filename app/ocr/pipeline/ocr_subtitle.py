from paddleocr import PaddleOCR
# import jieba.posseg as pos
# import cv2, os
# import re
# from glob import glob
# import json


class OcrSubtitlePipline:
    def __init__(self):
        self.ocr = PaddleOCR(
            use_angle_cls=False,
            use_gpu=False,
            use_onnx=True,
            show_log=False,
            det_model_dir='../pipeline/onnx/det_model.onnx',
            rec_model_dir='../pipeline/onnx/rec_model.onnx',
            cls_model_dir='../pipeline/onnx/cls_model.onnx'
        )


    def forward(self, img_path, show_res = False):
        # image = cv2.imread(img_path)
        preds = self.ocr.ocr(img_path)[0]
        return preds

        # pass
        #
        # lines, y, limit = [], 0, 5
        # for idx, pred in enumerate(preds):
        #
        #     left_up, right_up, right_low, left_low, text = self.get_line(pred)
        #
        #     if self.is_alpha(text) or len(text) < 2:
        #         continue
        #
        #     if idx < 5:
        #         limit = max((left_low[1] - left_up[1]) / 3, limit)
        #
        #     if abs(right_low[1] - y) < limit:
        #         lines[-1].append(pred)
        #     else:
        #         y = right_low[1]
        #         lines.append([pred])
        #
        #
        # json_info = {}
        # json_info['first_category'] = ''
        # json_info['first_category_en'] = ''
        # json_info['cast_info'] = []
        # for idx, line in enumerate(lines):
        #
        #     cur_json = {}
        #     cur_json['person_list'] = []
        #
        #     element = self.get_line(line[0])
        #
        #     if 'nr' not in [pair.flag for pair in pos.cut(element[4])]:
        #
        #         if idx != 0 and len(json_info['cast_info']) == 0 and len(line) == 1:
        #             continue
        #
        #         if show_res:
        #             cv2.rectangle(image, tuple(int(x) for x in element[0]), tuple(int(x) for x in element[2]),
        #                           (0, 255, 0), 2)
        #
        #         if idx == 0:
        #             json_info['first_category'] = element[4]
        #             continue
        #         else:
        #             cur_json['second_category'] = element[4]
        #             cur_json['second_category_en'] = ''
        #
        #     if 'second_category' in cur_json or len(json_info['cast_info']) == 0:
        #         role_name = []
        #     else:
        #         role_name = json_info['cast_info'][-1]['person_list']
        #
        #     if 'nr' in [pair.flag for pair in pos.cut(element[4])]:
        #         cur_json['person_list'].extend([{'person_name_cn': element[4],
        #                                          'person_en_name_en': ''}])
        #
        #     for jdx in range(1, len(line)):
        #         cur_element = self.get_line(line[jdx])
        #         role_name.append({'person_name_cn': cur_element[4],
        #                           'person_en_name_en': ''})
        #
        #     cur_json['person_list'] = role_name
        #
        #     if 'second_category' in cur_json or len(json_info['cast_info']) == 0:
        #         json_info['cast_info'].append(cur_json)
        #     else:
        #         json_info['cast_info'][-1]['person_list'] = cur_json['person_list']
        #
        # if show_res:
        #     out_dir = '../logs/res/'
        #     os.makedirs(out_dir, exist_ok=True)
        #     json_str = json.dumps(json_info, ensure_ascii=False, indent=4)
        #     with open(os.path.join(out_dir, img_path.split('/')[-1] + '.json'), 'w') as f:
        #         f.write(json_str)
        #
        #     cv2.imwrite(os.path.join(out_dir, img_path.split('/')[-1]), image)
        #
        # return json_info

    def get_line(self, line):
        box = line[0]
        # 左上
        left_up = box[0]
        # 右上
        right_up = box[1]
        # 右下
        right_low = box[-2]
        # 左下
        left_low = box[-1]
        # 文本框
        text_box = line[1]
        # 文本
        text = text_box[0]

        return left_up, right_up, right_low, left_low, text


    def is_alpha(self, text):

        ch = 0
        for char in text:
            if '\u4e00' <= char <= '\u9fa5':
                ch += 1

        return True if ch == 0 else False


if __name__ == '__main__':
    ocr_subtitle = OcrSubtitlePipline()

    # img_dir = '/data1/Developer/shentingting/vqa/project/ocr_subtitle/data/crop/'
    # ocr_subtitle.forward('/Users/weilongshi/Downloads/ocr3.png', show_res=True)
    # img_paths = glob(os.path.join(img_dir, '*.png'))
    # for img_path in img_paths:
    #     ocr_subtitle.forward(img_path, show_res = True)
    # 有座位
    # img_path = "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/train/20250227174847063272.pdf---image_page1_3.png"
    # 无座位
    # img_path = "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf//ComplexCon 2025 Mar 23/maoyan/Mar 23 Sun T1S T1站位 1788/maoyan_178張/Block C/20250227164433882102.pdf---image_page1_3.png"
    # 异常
    # img_path = "/Users/zhoudong/projects/maoyan/movie-data-automation/performance/ocr/pdf/ComplexCon 2025 Mar 23/maoyan/Mar 23 Sun T3M 坐位 988/maoyan_584張/Block 11/20250227180153093256.pdf---image_page1_3.png"
    img_path = "/Users/zhoudong/Pictures/jj/WechatIMG32.jpg"
    preds = ocr_subtitle.forward(img_path,  show_res=True)
    print(preds)
    print(type(preds))

