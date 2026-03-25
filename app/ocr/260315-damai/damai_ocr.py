import cv2
import webbrowser


def scan_qrcode_with_opencv(image_path):
    # 直接读取本地图片文件
    image = cv2.imread(image_path)

    if image is None:
        print(f"无法读取图片: {image_path}")
        return None

    # 初始化 QRCode 检测器
    detector = cv2.QRCodeDetector()

    # 检测和解码二维码
    data, bbox, straight_qrcode = detector.detectAndDecode(image)

    if data:
        print(f"检测到二维码内容: {data}")
        # 打开链接
        webbrowser.open(data)
        print(f"页面打开正常， 待填入用户信息: {image}")
        return data
    else:
        print("未检测到二维码")
        return None


# 使用示例 - 使用本地文件路径
if __name__ == "__main__":
    image_path = "/Users/zhoudong/Downloads/damai/bangding.jpg"
    scan_qrcode_with_opencv(image_path)
