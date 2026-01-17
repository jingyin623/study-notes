# study-notes

# 虚拟环境的安装
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



# 1. 将本地代码强制回退到 3 个版本之前（假设你刚才推了3次）（文件会被删除的）
git reset --hard HEAD~3
# 第一步：把最后一次提交撤回，但保留你写的代码文件
git reset --soft HEAD~1

# 2. 强制覆盖云端（注意：这一步需要网络通畅）
git push -f origin main



# 正常打包exe
pyinstaller --name "daily_planner" daily_planner.py
pyinstaller --noconsole --onefile --clean --name "无限循环清理专家" main.py
# 文件的打包（--collect-submodules plyer 强制包含plyer的所有子模块，）
pyinstaller --noconsole --collect-submodules plyer daily_planner.py

