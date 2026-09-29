'''
Docstring for small-tools.downloadtorrent.download_torrents copy
其他专用智能工资下载脚本
'''
import asyncio
import os
import random
from playwright.async_api import async_playwright

# --- 配置区域 ---
SAVE_DIR = r"C:\Users\MR.jiang\Desktop\DWON" 

# 1. 页面配置
PAGE_START = 0      
PAGE_END = 2        # 会执行 0 到 6 页

# 2. 按钮配置
LINK_START = 0      
LINK_MAX = 100       

# URL 地址设置
LOGIN_URL = "https://example.com/login"
# 重点：确认该 URL 在浏览器中手动能打开且能看到种子列表
URL_TEMPLATE = "https://pt.btschool.club/torrents.php?allsec=1&inclbookmarked=1&incldead=0&spstate=0&page={i}"

# --- 逻辑升级版 ---

async def run():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        # 模拟真实浏览器，防止被反爬识别
        context = await browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("🚀 正在打开登录页面...")
        await page.goto(LOGIN_URL)

        try:
            print("💡 请在浏览器中完成登录/验证码...")
            # 兼容更多跳转路径，只要登录后通常会回到 index, browse 或 special
            await page.wait_for_url(lambda url: "login" not in url, timeout=120000)
            print("✅ 登录检测通过！")
            await asyncio.sleep(3) 
        except Exception:
            print("❌ 登录超时。")

        for p_idx in range(PAGE_START, PAGE_END):
            target_url = URL_TEMPLATE.format(i=p_idx)
            print(f"\n🌐 正在进入第 {p_idx} 页: {target_url}")

            await page.goto(target_url, wait_until="networkidle")
            
            # --- 改进点 1: 动态等待 ---
            # 不再等待特定的 #torrenttable，而是等待包含 download.php 的链接出现
            try:
                await page.wait_for_selector('a[href*="download.php"]', timeout=15000)
            except:
                print(f"⚠️ 页面加载完成，但未发现任何下载链接。")
                # 调试用：保存一张截图看看页面长啥样
                # await page.screenshot(path=f"error_page_{p_idx}.png")
                continue

            # --- 改进点 2: 更精准的定位器 ---
            # 搜索所有包含 download.php 且 id= 的链接
            download_selectors = page.locator('a[href*="download.php?id="]')
            total_found = await download_selectors.count()
            print(f"🔍 本页共识别到 {total_found} 个种子下载链接")

            if total_found == 0:
                continue

            for i in range(LINK_START, min(total_found, LINK_MAX)):
                button = download_selectors.nth(i)
                
                try:
                    # 获取文件名（可选，部分站点在 title 属性里）
                    title = await button.get_attribute("title") or f"seed_{i}"
                    
                    await button.scroll_into_view_if_needed()
                    await asyncio.sleep(random.uniform(0.5, 1.5))

                    async with page.expect_download(timeout=60000) as download_info:
                        print(f"⬇️ 正在下载第 {i+1} 个: {title[:30]}...")
                        await button.click(force=True)
                    
                    download = await download_info.value
                    file_name = download.suggested_filename
                    await download.save_as(os.path.join(SAVE_DIR, file_name))
                    print(f"✅ 下载完成: {file_name}")

                    # 间隔保护
                    wait_time = random.uniform(10, 20)
                    print(f"☕ 休息 {wait_time:.1f} 秒...")
                    await asyncio.sleep(wait_time)

                except Exception as e:
                    print(f"❌ 第 {i+1} 个处理失败: {e}")
                    await asyncio.sleep(5)
                    continue

        print(f"\n✨ 全部任务已尝试完成！")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())