from fastapi import FastAPI
from routers import news, users, favorite

from fastapi.middleware.cors import CORSMiddleware
from utils.exception_handlers import register_exception_handlers

app = FastAPI()

# 注册全局异常处理器（统一 {code, message, data} 错误响应）
register_exception_handlers(app)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的源，生产环境需要的指定源
    allow_credentials=True,  # 允许携带cookie
    allow_methods=["*"],  # 允许的请求方法
    allow_headers=["*"],   # 允许的请求头
)
#  挂载路由/注册路由
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


