import asyncio
import os
import random
from playwright.async_api import async_playwright

# --- 配置区域 ---
SAVE_DIR = r"C:\Users\MR.jiang\Desktop\DWON" 

# 1. 页面配置
PAGE_START = 5      # 从第几页开始
PAGE_END = 10       # 到第几页结束 (含)

# 2. 按钮配置
BUTTON_START = 1    # 每页从第几个按钮开始
BUTTON_END = 100    # 每页点到第几个按钮结束

# URL 地址设置
LOGIN_URL = "https://kp.m-team.cc/login"
# 3. 模板配置 (关键：使用 {i} 作为占位符)
# 如果你想换搜索条件，直接改这里的 URL 即可
URL_TEMPLATE = "https://kp.m-team.cc/browse?pageNumber={i}&sort=size%3Aascend&team=44&team=9&team=43"
# 如果网站改版，直接改这里的 XPath 即可
XPATH_TEMPLATE = '//*[@id="app-content"]/div/div[4]/div[1]/div/div/div/div/table/tbody/tr[{i}]/td[7]/button[2]'
# ----------------

async def run():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print("🚀 正在登录...")
        await page.goto(LOGIN_URL)

        try:
            await page.wait_for_url("**/browse*", timeout=120000)
            print("✅ 登录成功！")
            await asyncio.sleep(5) 
        except Exception:
            print("❌ 登录超时或未检测到跳转。")
            # 如果没跳转，脚本会继续尝试，或者你可以选择 return

        # 外层循环：遍历每一页
        # 注意：我把变量名改成了 p_idx，避免和里层的 i 冲突
        for p_idx in range(PAGE_START, PAGE_END):
            target_url = URL_TEMPLATE.format(i=p_idx)
            print(f"\n🌐 正在进入第 {p_idx} 页: {target_url}")

            await page.goto(target_url)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(5) # 等待 API 数据渲染

            print(f"⏳ 开始执行批量点击...")
            
            # 内层循环：遍历当前页面的按钮
            for i in range(BUTTON_START, BUTTON_END):
                # 从配置区获取模板并填充当前的行号 i
                current_xpath = XPATH_TEMPLATE.format(i=i)
                button = page.locator(f"xpath={current_xpath}")
                
                if await button.count() > 0:
                    try:
                        await button.scroll_into_view_if_needed()
                        await asyncio.sleep(1)

                        try:
                            async with page.expect_download(timeout=30000) as download_info:
                                print(f"⬇️ 正在点击 Row {i}...")
                                await button.click()
                            
                            download = await download_info.value
                            file_name = download.suggested_filename
                            await download.save_as(os.path.join(SAVE_DIR, file_name))
                            print(f"✅ 下载成功: {file_name}")
                        except Exception as e:
                            print(f"❌ Row {i} 下载失败或超时 (可能被拦截)。")
                            await asyncio.sleep(20)
                            continue
                        
                        # 随机休息，保护账号
                        wait_time = random.uniform(10, 20)
                        print(f"☕ 休息 {wait_time:.1f} 秒...")
                        await asyncio.sleep(wait_time) 
                        
                    except Exception as e:
                        print(f"⚠️ 处理 Row {i} 时出错: {e}")
                else:
                    # 如果连续几行找不到按钮，说明这页到头了
                    if i > 15: 
                        print(f"🏁 第 {p_idx} 页任务结束，未发现更多按钮。")
                        break

        print(f"\n✨ 所有配置页处理完成！")
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())