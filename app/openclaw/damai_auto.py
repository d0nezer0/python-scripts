#!/usr/bin/env python3
"""
大麦网自动填写脚本 - 完全自动版
流程：扫描二维码 -> 启动浏览器 -> 点击接收 -> 判断登录 -> 填写表单 -> 点击确认
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright
import cv2


def scan_qr_code(image_path):
    """从图片扫描二维码"""
    print(f"📸 扫描二维码: {image_path}")
    
    if not Path(image_path).exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"无法读取图片: {image_path}")
    
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(image)
    
    if not data:
        raise ValueError("未检测到二维码")
    
    print(f"✅ 二维码内容: {data}")
    return data


async def main():

    # 二维码图片路径
    # 个人信息
    personal_info = {
        'qr_image_path': '/Users/zhoudong/Downloads/damai/bangding.jpg',
        'real_name': '周栋',
        'id_number': '110101199001011234',
        'code': '12345678',
    }
    
    # 从 info.json 读取
    script_dir = Path(__file__).parent
    info_file = script_dir / 'info.json'
    if info_file.exists():
        import json
        with open(info_file, 'r', encoding='utf-8') as f:
            personal_info = json.load(f)
        print(f"📋 个人信息: {personal_info}")
    
    print("\n🚀 启动浏览器...")
    
    playwright = await async_playwright().start()
    
    # 优先使用 Chrome 用户数据目录
    chrome_user_data = Path.home() / "Library/Application Support/Google/Chrome"
    use_chrome_data = True
    
    # 检查 Chrome 是否正在运行
    import subprocess
    chrome_running = subprocess.run(['pgrep', '-x', 'Google Chrome'], capture_output=True).returncode == 0
    
    if chrome_running:
        print("⚠️  检测到 Chrome 正在运行")
        print("💡 将使用独立配置目录（保留之前的登录状态）")
        playwright_user_data = Path.home() / ".playwright-chrome-profile"
        use_chrome_data = False
    else:
        print("✅ Chrome 未运行，将使用 Chrome 登录状态")
        playwright_user_data = chrome_user_data

    # 扫描二维码获取链接
    try:
        qr_url = scan_qr_code(personal_info['qr_image_path'])
    except Exception as e:
        print(f"❌ 二维码扫描失败: {e}")
        return
    
    try:
        # 启动浏览器
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(playwright_user_data),
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        print("✅ 浏览器已启动")
        
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
        
        # 访问页面
        print(f"🌐 访问页面...")
        await page.goto(qr_url, timeout=30000, wait_until='domcontentloaded')
        await asyncio.sleep(3)
        
        # 截图 - 初始状态
        await page.screenshot(path=str(script_dir / personal_info['code'] / 'step1_initial.png'), full_page=True)
        print("📸 step1_initial.png")
        
        title = await page.title()
        print(f"📄 标题: {title}")
        
        # 自动点击接收按钮
        print("\n🔍 查找并点击接收按钮...")
        await asyncio.sleep(3)  # 增加等待时间
        
        # 先尝试查找所有可能的按钮元素
        print("  📋 查找页面上所有按钮...")
        all_buttons = await page.query_selector_all('button, a.btn, div[class*="btn"], input[type="button"], input[type="submit"]')
        print(f"  📊 找到 {len(all_buttons)} 个按钮元素")
        
        # 打印所有按钮的文本内容（调试用）
        for idx, btn in enumerate(all_buttons[:10]):  # 只显示前10个
            try:
                text = await btn.text_content()
                is_visible = await btn.is_visible()
                print(f"    按钮 {idx}: '{text}' (可见: {is_visible})")
            except:
                pass
        
        accept_keywords = ['接收', '接受', '立即接收', '确认接收', '领取', '确定']
        clicked = False
        
        for keyword in accept_keywords:
            try:
                print(f"\n  🔍 尝试查找包含 '{keyword}' 的元素...")
                
                # 使用更精确的选择器
                selectors = [
                    f'button:has-text("{keyword}")',
                    f'button >> :text("{keyword}")',
                    f'[role="button"]:has-text("{keyword}")',
                    f'a:has-text("{keyword}")',
                    f'div[class*="btn"]:has-text("{keyword}")',
                    f':text-is("{keyword}")',
                ]
                
                for selector in selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            print(f"    找到 {len(elements)} 个元素: {selector}")
                            for elem in elements:
                                try:
                                    is_visible = await elem.is_visible()
                                    if is_visible:
                                        # 滚动到元素
                                        await elem.scroll_into_view_if_needed()
                                        await asyncio.sleep(0.5)
                                        
                                        # 尝试多种点击方式
                                        try:
                                            # 方式1: 直接点击
                                            await elem.click(timeout=3000)
                                            print(f"    ✅ 已点击: {keyword} (方式1: 直接点击)")
                                            clicked = True
                                        except:
                                            try:
                                                # 方式2: 使用 JavaScript 点击
                                                await page.evaluate('el => el.click()', elem)
                                                print(f"    ✅ 已点击: {keyword} (方式2: JS点击)")
                                                clicked = True
                                            except:
                                                try:
                                                    # 方式3: 模拟鼠标点击
                                                    await elem.dispatch_event('click')
                                                    print(f"    ✅ 已点击: {keyword} (方式3: 事件点击)")
                                                    clicked = True
                                                except:
                                                    continue
                                        
                                        if clicked:
                                            await asyncio.sleep(3)
                                            break
                                except Exception as e:
                                    print(f"    ⚠️ 元素点击失败: {e}")
                                    continue
                        if clicked:
                            break
                    except Exception as e:
                        continue
                if clicked:
                    break
            except:
                continue
        
        # 如果所有选择器都没找到，尝试通过文本内容查找
        if not clicked:
            print("\n  🔍 尝试通过文本内容查找...")
            for btn in all_buttons:
                try:
                    text = await btn.text_content()
                    if text and any(keyword in text for keyword in accept_keywords):
                        if await btn.is_visible():
                            await btn.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            await btn.click()
                            print(f"    ✅ 已点击: '{text}'")
                            clicked = True
                            await asyncio.sleep(3)
                            break
                except:
                    continue
        
        # 截图 - 点击接收后
        await page.screenshot(path=str(script_dir / personal_info['code'] / 'step2_after_accept.png'), full_page=True)
        print("📸 step2_after_accept.png")
        
        # 判断是否进入登录页
        current_url = page.url
        current_title = await page.title()
        
        print(f"\n📄 当前页面: {current_title}")
        print(f"📄 当前 URL: {current_url}")
        
        if '登录' in current_title:
            print("\n" + "="*60)
            print("⚠️  检测到进入登录页！")
            print("💡 请在浏览器中手动登录大麦网")
            print("💡 登录成功后脚本会自动继续填写表单...")
            print("="*60)
            
            # 等待登录（最多120秒）
            for i in range(120):
                await asyncio.sleep(1)
                current_url = page.url
                current_title = await page.title()
                
                if '登录' not in current_title and 'login' not in current_url.lower():
                    print("\n✅ 登录成功，继续执行...")
                    await asyncio.sleep(2)
                    break
                
                if i % 10 == 0:
                    print(f"  ⏳ 等待登录... ({i}/120秒)")
            else:
                print("\n⚠️  登录超时，继续尝试填写...")
        
        # 填写表单
        print("\n📝 填写表单...")
        await asyncio.sleep(2)
        
        # 1. 姓名
        try:
            name_input = await page.wait_for_selector('input[placeholder*="姓名"]', timeout=5000)
            if name_input:
                await name_input.fill(personal_info['real_name'])
                print(f"  ✅ 姓名: {personal_info['real_name']}")
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️ 姓名填写失败: {e}")
        
        # 2. 证件号码
        try:
            id_input = await page.wait_for_selector('input[placeholder*="证件号码"]', timeout=5000)
            if id_input:
                await id_input.fill(personal_info['id_number'])
                print(f"  ✅ 证件号码: {personal_info['id_number']}")
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️ 证件号码填写失败: {e}")
        
        # 3. 领取码
        try:
            code_input = await page.wait_for_selector('input[placeholder*="领取码"]', timeout=5000)
            if code_input:
                code = personal_info.get('code', '12345678')
                await code_input.fill(code)
                print(f"  ✅ 领取码: {code}")
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️ 领取码填写失败: {e}")
        
        # 截图 - 填写后
        await page.screenshot(path=str(script_dir / personal_info['code'] / 'step3_filled.png'), full_page=True)
        print("📸 step3_filled.png")
        
        # 自动点击确认按钮
        print("\n🔍 查找并点击确认按钮...")
        await asyncio.sleep(1)
        
        confirm_keywords = ['确定', '确认', '提交', '立即领取', '完成']
        submitted = False
        
        for keyword in confirm_keywords:
            try:
                selectors = [
                    f'button:has-text("{keyword}")',
                    f'a:has-text("{keyword}")',
                    f'input[type="button"][value*="{keyword}"]',
                    f':text("{keyword}")',
                ]
                
                for selector in selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            for elem in elements:
                                try:
                                    if await elem.is_visible():
                                        await elem.scroll_into_view_if_needed()
                                        await asyncio.sleep(0.5)
                                        await elem.click()
                                        print(f"  ✅ 已点击: {keyword}")
                                        submitted = True
                                        await asyncio.sleep(3)
                                        break
                                except:
                                    continue
                        if submitted:
                            break
                    except:
                        continue
                if submitted:
                    break
            except:
                continue
        
        # 截图 - 提交后
        await page.screenshot(path=str(script_dir / personal_info['code'] / 'step4_submitted.png'), full_page=True)
        print("📸 step4_submitted.png")
        
        print("\n" + "="*60)
        if submitted:
            print("✅ 表单已自动提交！")
        else:
            print("⚠️  未找到确认按钮，请手动点击")
        print("="*60)
        print("\n💡 浏览器将保持打开 10 秒后自动关闭")
        
        await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        print("\n👋 退出")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 浏览器将保持打开，按 Ctrl+C 退出")
        await asyncio.Future()
    finally:
        try:
            await context.close()
        except:
            pass


if __name__ == '__main__':
    asyncio.run(main())
