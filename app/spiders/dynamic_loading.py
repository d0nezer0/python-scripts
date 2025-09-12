from selenium import webdriver


# // 获取动态网页内容；
def get_dynamic_content(url):
    driver = webdriver.Chrome()
    driver.get(url)
    dynamic_content = driver.page_source
    driver.quit()
    return dynamic_content


if __name__ == '__main__':
    url = 'https://www.baidu.com/'
    dynamic_content = get_dynamic_content(url)
    print(dynamic_content)
