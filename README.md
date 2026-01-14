# study-notes


# 1. 将本地代码强制回退到 3 个版本之前（假设你刚才推了3次）（文件会被删除的）
git reset --hard HEAD~3

# 2. 强制覆盖云端（注意：这一步需要网络通畅）
git push -f origin main

# 第一步：把最后一次提交撤回，但保留你写的代码文件
git reset --soft HEAD~1

# 第二步：如果你刚才已经 Push 到网页了，想让网页也撤回
git push -f origin main

# 正常打包exe
pyinstaller --name "daily_planner" daily_planner.py

# 文件的打包（--collect-submodules plyer 强制包含plyer的所有子模块，）
pyinstaller --noconsole --collect-submodules plyer daily_planner.py

