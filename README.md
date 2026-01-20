# uv安装
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# 安装指定版本
uv python install 3.9
# 查看已经安装的python
uv python list
# 初始化安装
cd D:\Programs\German_IT_Project\fastAPI
uv init 
# 虚拟化
uv venv
# 退出虚拟环境
deactivate
# 安装依赖包
uv add fastapi
# 从项目中移除一个依赖项。
uv remove fastapi
# 将项目的依赖项与环境同步。
uv sync fastapi

# 1. 将本地代码强制回退到 3 个版本之前（假设你刚才推了3次）（文件会被删除的）
git reset --hard HEAD~3
# 第一步：把最后一次提交撤回，但保留你写的代码文件
git reset --soft HEAD~1

git push -f origin main


