# small-tools
本项目主要是收集各种自己适用的小工具
顺便自己练习一些python的语法，


并记录一些自己常用的命令
# 正常打包exe
pyinstaller --name "daily_planner" daily_planner.py
pyinstaller --noconsole --onefile --clean --name "upserver" Server_GUI.py
# 文件的打包（--collect-submodules plyer 强制包含plyer的所有子模块，）
pyinstaller --noconsole --collect-submodules plyer daily_planner.py

