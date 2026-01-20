# study-notes

# 虚拟环境的安装(k可选不推荐)
D:\python\Python38\python -m venv .venv

# 安装包
pip install numpy==1.24.3
# 更新包
pip install --upgrade 包名
# 删除包
pip uninstall 包1 包2 包3
# 删除所有包（先导出包到文件，然后根据包文件删除所有包）
pip freeze > requirements.txt
pip uninstall -r requirements.txt -y







# 正常打包exe
pyinstaller --name "daily_planner" daily_planner.py
pyinstaller --noconsole --onefile --clean --name "upserver" Server_GUI.py
# 文件的打包（--collect-submodules plyer 强制包含plyer的所有子模块，）
pyinstaller --noconsole --collect-submodules plyer daily_planner.py

