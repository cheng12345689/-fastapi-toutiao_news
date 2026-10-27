
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import news

## 创建APIrouter
router = APIRouter(prefix="/api/news", tags=["news"])

# 接口实现的流程：
# 1.模块化路由->API接口规范文档
# 2.定义模型类→数据库表（数据库设计文档）
# 3.在crud文件夹里面创建文件，封装操作数据库的方法
# 4.在路由处理函数里面调crud封装好的方法，响应结果

@router.get("/categories")
async def get_categories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # 先获取数据库里是新闻分类数据->先定义模型类->封装查询新闻分类的数据
    categories = await news.get_categories(db, skip, limit)
    return {
        "code": 200,
        "message": "获取新闻分类成功",
        "data": categories
    }
@router.get("/list")
async def get_news_list(
        category_id: int = Query(..., alias="categoryId"),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, alias="pageSize", le=100),
        db: AsyncSession = Depends(get_db)
):
    news_list, total = await news.get_news_list(db, category_id, page, page_size)
    return {
        "code": 200,
        "message": "获取新闻列表成功",
        "data": {
            "list": news_list,
            "total": total,
            "hasMore": page * page_size < total
    }
    }

@router.get("/detail")
async def get_news_detail(
        news_id: int = Query(..., alias="id"),
        db: AsyncSession = Depends(get_db)
):
    #  获取新闻，阅读后浏览量+1操作，相关新闻
    detail = await news.get_news(db, news_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="新闻不存在")

    # 浏览量 +1（数据库侧自增，返回值直接 +1 给前端展示）
    await news.increase_news_views(db, news_id)
    related_news = await news.get_related_news(db, news_id, detail.category_id)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": detail.id,
            "title": detail.title,
            "content": detail.content,
            "image": detail.image,
            "author": detail.author,
            "publishTime": detail.publish_time,
            "categoryId": detail.category_id,
            "views": detail.views + 1,
            "relatedNews": related_news
        }
    }