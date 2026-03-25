import subprocess
import time
import sys


def execute_pssh_curl(id_num):
    """
    执行指定ID的pssh + curl命令
    :param id_num: 要替换的ID数字
    :return: 元组 (执行状态, 标准输出, 标准错误)
    """
    # 构建完整的pssh命令（替换URL中的ID占位符）
    # 使用三引号处理复杂的命令字符串，避免引号转义混乱
    cmd = f'''pssh com.sankuai.movie.crawler.scratch "curl 'https://www.maoyan.com/films/celebrity/{id_num}' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,zh-TW;q=0.8' \
  -H 'Cache-Control: max-age=0' \
  -H 'Connection: keep-alive' \
  -b '__mta=218980006.1750662322264.1768533825176.1768535214856.66; __mta=218980006.1750662322264.1767670845367.1767670852874.58; _lxsdk_cuid=19781d653bbc8-0650a47c0ac5fa8-18525636-16a7f0-19781d653bbc8; _ga=GA1.1.1713604259.1750662320; _csrf=b7b0205b585dec33e1c738366a322d9ff976151e38fc196d7a71d3fac7551539; HMACCOUNT=07E48A9EF247162F; openPlatform=[\"1000315\",\"\",\"6wlpzgas6wl\",\"\"]; openPlatform.sig=7hOBx6dWCP-eoHG8h-8_70xvwQU; old-moviepage-ci=1; hotMovieIds=78463,356895,1142033,247161,1535383,1572282,4430,346650,1254449,1504105,584,1399234,1507422,1531816,376806,1505603,1251880,583,1427340,1519760,1502849,1551280,1528598,1529761,1434989,1443396,1281834,1501173,1565329,248580,1371005,1298554,1522966,1374168,1500265,1482432,1501291,1547217,1427802,1529788,1522761,1528466,1495771,1603579,1502253,1447633,1485017,59452,330,1489329,1510966,1454962,1531082,1522764,1310138,1307114,7284,285540,2265,1295,1340,32124,78602,341628,1342431,1187439,1233260,1354754,1478862,1432020,1435608,1478942,1478868; Hm_lvt_e0bacf12e04a7bd88ddbd9c74ef2b533=1766124636; __mta=218980006.1750662322264.1766487820817.1766487828836.48; uuid_n_v=v1; uuid=706507E0E92011F084B07FE9CD57F5C122FE621829744A4894E7570B1BA325E1; WEBDFPID=3z36uxu1uvxw582911y75zvx0u1w7545801u6w2v987579589xu4wx89-1767613523020-1756437667036SUIOAOM75613c134b6a252faa6802015be905512635; utm_source_rg=AM%256ecZXZX%25380; _lxsdk=706507E0E92011F084B07FE9CD57F5C122FE621829744A4894E7570B1BA325E1; sso.meituan.movie.erp.movieerp-hr-econtract_ssoid=fe247d9019c7b8215d74fde1a59a5edd*850e6c7a39c72ed53dc27c45288ec607; Hm_lpvt_e0bacf12e04a7bd88ddbd9c74ef2b533=1768535214; _ga_WN80P4PSY7=GS2.1.s1768533810$o53$g1$t1768535213$j58$l0$h0; _lx_utm=utm_source%3Dsmarter%26utm_campaign%3DopenPlatform%253D1000315; _lxsdk_s=19bc4d45cf4-363-41b-0b%7C%7C12' \
  -H 'Sec-Fetch-Dest: document' \
  -H 'Sec-Fetch-Mode: navigate' \
  -H 'Sec-Fetch-Site: none' \
  -H 'Sec-Fetch-User: ?1' \
  -H 'Upgrade-Insecure-Requests: 1' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: \"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: \"macOS\"'"'''

    try:
        # 执行命令，捕获stdout和stderr，设置超时时间（避免卡住）
        result = subprocess.run(
            cmd,
            shell=True,  # 启用shell解析复杂命令
            check=False,  # 不主动抛出异常，手动处理返回码
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',  # 输出转成字符串（而非字节）
            timeout=30  # 单个命令超时时间30秒
        )
        # 返回执行状态（0为成功）、标准输出、标准错误
        return (result.returncode == 0, result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        return (False, "", f"ID {id_num}: 命令执行超时（30秒）")
    except Exception as e:
        return (False, "", f"ID {id_num}: 执行异常 - {str(e)}")


def main():
    """主函数：循环执行1-100的ID请求"""
    # 定义循环范围（1到100）
    start_id = 1
    end_id = 1000
    # 每次请求后延迟1秒（可根据需要调整）
    delay = 1

    print(f"开始执行pssh + curl请求，ID范围：{start_id}-{end_id}")
    print("-" * 60)

    # 记录失败的ID，方便后续排查
    failed_ids = []

    for id_num in range(start_id, end_id + 1):
        print(f"正在处理 ID: {id_num}/{end_id}")

        # 执行命令
        success, stdout, stderr = execute_pssh_curl(id_num)

        # 打印执行结果
        if success:
            print(f"ID {id_num}: 执行成功")
            # 可选：打印输出（如果需要查看curl返回内容）
            # print(f"输出: {stdout[:200]}...")  # 只打印前200字符，避免刷屏
        else:
            print(f"ID {id_num}: 执行失败")
            print(f"错误信息: {stderr}")
            failed_ids.append(id_num)

        # 非最后一次循环则添加延迟
        if id_num != end_id:
            time.sleep(delay)

    # 执行完成后汇总结果
    print("-" * 60)
    print("执行完成！")
    print(f"成功数量: {end_id - start_id + 1 - len(failed_ids)}")
    print(f"失败数量: {len(failed_ids)}")
    if failed_ids:
        print(f"失败的ID列表: {failed_ids}")


if __name__ == "__main__":
    # 检查Python版本（可选，确保兼容性）
    if sys.version_info < (3, 6):
        print("错误：需要Python 3.6及以上版本")
        sys.exit(1)
    # 启动主函数
    main()