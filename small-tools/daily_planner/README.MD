"""
Docstring for small-tools.daily_planner.daily_planner
纪律生活小助手 - 日程提醒工具
功能：
1. 实时显示当前时间
2. 显示当前任务和下一个任务
3. 支持自定义日程表
4. 提供窗口拖动和最小化功能
5. 支持自动提醒功能，弹出通知并播放提示音
使用方法：
1. 运行脚本后，点击右上角的齿轮按钮打开日程管理窗口
2. 在日程管理窗口中添加、删除或修改任务
3. 关闭管理窗口后，主窗口会根据设置的日程自动提醒
"""

并记录一些自己常用的命令
# 正常打包exe
pyinstaller --name "daily_planner" daily_planner.py
pyinstaller --noconsole --onefile --clean --name "upserver" daily_planner.py
# 文件的打包（--collect-submodules plyer 强制包含plyer的所有子模块，并外置配置文件）
pyinstaller --noconsole --onefile --clean --name "daily_planner" --add-data "disciplined_life.json;." --collect-submodules plyer daily_planner.py