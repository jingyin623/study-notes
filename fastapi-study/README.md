# docs访问慢的问题
.venv\Lib\site-packages\fastapi\openapi\docs.py
修改
    # ] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
    ] = "/static/swagger-ui-bundle.js",
    # ] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    ] = "/static/swagger-ui.css",
    # ] = "https://fastapi.tiangolo.com/img/favicon.png",
    ] = "/static/favicon.png",
# 把项目下的static目录作为静态文件的访问目录（注册让api识别目录）
app.mount('/static', StaticFiles(directory='static'), name='my_static')

# fastapi 启动的方式
# 生产模式启动
uvicorn main:app --reload 
# main函数启动
 if __name__ == "__main__":
     import uvicorn
     uvicorn.run(app, host="127.0.0.1", port=8000)