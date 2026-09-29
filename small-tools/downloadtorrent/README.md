"""
Docstring for small-tools.downloadtorrent.download_torrents
- * download_torrents.py   
- * 功能：自动化下载指定网站的种子文件，支持分页下载和批量点击下载按钮。
- *      用户可配置下载保存路径、起始页码、结束页码及按钮范围。
- * 主要步骤：
- * 1. 使用 Playwright 自动化浏览器操作，登录目标网站。
- * 2. 遍历指定页码范围，访问每一页的种子列表。
- * 3. 定位并点击下载按钮，捕获下载事件并保存种子文件。
- * 4. 支持随机等待时间，避免触发网站的反爬虫机制。
- * 注意事项：
- * - 需要预先安装 Playwright 并配置浏览器环境。
- * - 登录过程需手动完成，脚本会等待登录成功后继续执行。
- * - 下载过程中可能会遇到浏览器拦截或 API 限制，需适当调整等待时间。
"""


# URL登录 网址
LOGIN_URL = "http://qkjpw.ayuanwl.com/loginByPhone"
# 登录账号输入框
LOGIN_XPATH_PHONE = '//*[@id="app"]/div[1]/form/div[1]/div/div/input'
# 请求验证码按钮
YANZHENGMA_XPATH = '//*[@id="app"]/div[1]/form/div[2]/div/div/div/button'
# 验证码输入框
YANZHENGMA_XPATH_INPUT = '//*[@id="app"]/div[1]/form/div[2]/div/div/input'
# 登录按钮
LOGIN_XPATH_BUTTON = '//*[@id="app"]/div[1]/form/div[4]/button'
# 跳转后页面的A标签
MAIN_PAGE_A = 'http://qkjpw.ayuanwl.com/main/first'
# 单击a标签
PRGRAM_A= '//*[@id="app"]/div[1]/div[1]/div/div[1]/a[3]'
# 信息div
INFO_DIV = '//*[@id="goodsMap-2"]'

以上是需要用到的元素 XPath
1.创建一个用户面板(包含关键字输入框,手机号输入框,开始按钮,退出按钮)
LOGIN_URL = "http://qkjpw.ayuanwl.com/loginByPhone"
MAIN_PAGE_A = 'http://qkjpw.ayuanwl.com/main/first'
INFO_DIV = '//*[@id="goodsMap-2"]'
PRGRAM_A= '//*[@id="app"]/div[1]/div[1]/div/div[1]/a[3]'
2,用户点击开始后 运行逻辑 LOGIN_URL，输入手机号，点击获取验证码，(弹窗等待用户输入验证码->确定)获取用户验证码-填入验证码-，点击登录，等待跳转到 MAIN_PAGE_A ->
进入无限循环(
点击 PRGRAM_A -> 等待 INFO_DIV 出现，抓取所有INFO_DIV的文本内容,比对文本内容是否包含你想要的关键词,如果包含，弹窗提示用户，并且退出程序；如果不包含，等待一段时间后刷新页面，继续循环)
用 Playwright 库实现
请写除每个步骤的说明,