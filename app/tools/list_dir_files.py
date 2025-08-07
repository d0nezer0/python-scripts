import os


def print_directory_contents(path):
    for child in os.listdir(path):
        child_path = os.path.join(path, child)
        if os.path.isdir(child_path):
            print(f"目录: {child_path}")
            print_directory_contents(child_path)  # 递归调用以打印子目录内容
        else:
            print(f"文件: {child_path}")


def capture_directory_contents(path):
    for child in os.listdir(path):
        child_path = os.path.join(path, child)
        if os.path.isdir(child_path):
            # directory_contents.append(f"目录: {child_path}")
            capture_directory_contents(child_path)  # 递归调用以捕获子目录内容
            print(f"----------{child_path}----------")
        else:
            if (child_path.startswith(".")):
                print("隐藏文件： " + child_path)
                continue
            directory_contents.append(f"文件: {child_path}")
            print(f"文件: {child_path}")
    return directory_contents


if __name__ == '__main__':
    # 示例：打印当前工作目录下的内容
    current_working_directory = "/Users/zhoudong/Movies/Template2"
    directory_contents = []

    directory_contents = capture_directory_contents(current_working_directory)
    print(len(directory_contents))
    print(directory_contents)  # 展示前10条结果，避免输出过长
