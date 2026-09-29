import asyncio
from playwright.async_api import async_playwright
import time
import sys

# --- [配置参数] ---
LOCAL_CHROME_PATH = r"D:\Program Files (x86)\Google\Chrome Dev\Application\chrome.exe"
LOGIN_URL = "http://qkjpw.ayuanwl.com/loginByPhone"
MAIN_PAGE_A = 'http://qkjpw.ayuanwl.com/main/first'
INFO_DIV_XPATH = '//*[@id="goodsMap-2"]'
PROGRAM_A_XPATH = '//*[@id="app"]/div[1]/div[1]/div/div[1]/a[3]'
TARGET_KEYWORDS = ["您想要的关键词1", "您想要的关键词2", "重要提示"] # <--- 请在这里填写您想要比对的关键词列表
# -----------------

async def run_automation():
    """
    主自动化流程：登录 -> 循环抓取 -> 关键词比对 -> 退出/循环。
    """
    async with async_playwright() as p:
        # 启动浏览器实例 (使用headless=False可以实时看到浏览器操作)
        browser = p.chromium.launch(
            headless=False,
            executable_path=LOCAL_CHROME_PATH  # 直接点对点定位
            )
        page = await browser.new_page()

        print("=====================================================")
        print("✅ [第一阶段] 流程开始：正在导航到登录页面...")
        print("=====================================================")
        await page.goto(LOGIN_URL)

        # --- 步骤 1: 输入手机号并获取验证码 ---
        print("➡️ 步骤 1/3: 请在页面上输入手机号码...")
        # 假设手机号输入框的 selector 是 input[type="tel"] 或其他可定位的元素
        await page.fill('input[type="tel"]', '您的手机号码') 
        
        print("➡️ 步骤 2/3: 点击获取验证码...")
        await page.click('button:has-text("获取验证码")') # 假设按钮包含该文本
        
        # --- 步骤 3: 等待用户输入验证码 ---
        print("\n=====================================================")
        print("🛑 [暂停] 等待您的输入...")
        print("请在命令行中输入收到的验证码，然后按 Enter 键继续...")
        print("=====================================================\n")
        
        # 阻塞脚本，等待用户输入
        user_code = input(">>> 请输入验证码: ") 
        
        # 填入验证码并点击登录
        print("➡️ 步骤 3/3: 正在填入验证码并点击登录...")
        await page.fill('input[name="verification_code"]', user_code) # 假设验证码输入框的 name
        await page.click('button:has-text("登录")') # 假设登录按钮的文本
        
        # --- 步骤 4: 等待跳转到主页 ---
        print("⏳ 正在等待页面跳转到主页...")
        try:
            await page.wait_for_url(MAIN_PAGE_A, timeout=30000)
            print("🎉 登录成功！已进入主页面。开始进入无限循环抓取模式...")
        except Exception:
            print("❌ 登录失败或页面跳转超时。请检查 URL 和登录元素选择器。")
            await browser.close()
            return

        # --- 第二阶段：无限循环抓取与判断 ---
        while True:
            print("\n=====================================================")
            print("🔄 进入循环抓取模式... 正在点击进入信息区域...")
            print("=====================================================")
            
            try:
                # 1. 点击进入信息区域
                await page.click(PROGRAM_A_XPATH)
                
                # 2. 等待目标信息区域出现
                await page.wait_for_selector(INFO_DIV_XPATH, timeout=15000)
                
                # 3. 抓取所有文本内容
                info_element = page.locator(INFO_DIV_XPATH)
                full_text = await info_element.inner_text()
                print(f"✅ 成功抓取到信息区域内容 (总长度: {len(full_text)} 字符)。")
                
                # 4. 关键词比对
                found_keywords = []
                for keyword in TARGET_KEYWORDS:
                    if keyword in full_text:
                        found_keywords.append(keyword)
                
                # 5. 判断与退出/循环
                if found_keywords:
                    print("\n=====================================================")
                    print("🛑 🚨 任务完成！在信息中找到了关键词：", ", ".join(found_keywords))
                    print("脚本将安全退出。")
                    print("=====================================================\n")
                    await browser.close()
                    break # 退出无限循环
                else:
                    print("✅ 内容中未发现目标关键词。等待 5 秒后刷新页面，继续循环...")
                    await asyncio.sleep(5)
                    await page.reload() # 刷新页面
                    
            except Exception as e:
                print(f"❌ 循环抓取中发生错误：{e}")
                print("尝试等待 10 秒后刷新页面，继续尝试...")
                await asyncio.sleep(10)
                await page.reload()

        await browser.close()
        print("\n🎉 所有任务流程已安全结束。")


if __name__ == "__main__":
    try:
        asyncio.run(run_automation())
    except KeyboardInterrupt:
        print("\n[用户中断] 脚本被用户手动停止。")