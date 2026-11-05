from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import favorite as favorite_crud
from crud import news as news_crud
from models.users import User
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/favorite", tags=["favorite"])


@router.get("/check")
async def check_favorite(
        news_id: int = Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """查询当前用户是否收藏了指定新闻"""
    favorited = await favorite_crud.is_favorite(db, user.id, news_id)
    return success_response(message="success", data={"isFavorite": favorited})


@router.post("/add")
async def add_favorite(
        news_id: int = Body(..., alias="newsId", embed=True),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """添加收藏：先确认新闻存在，重复收藏也返回成功（幂等）"""
    if await news_crud.get_news(db, news_id) is None:
        raise HTTPException(status_code=404, detail="新闻不存在")

    added = await favorite_crud.add_favorite(db, user.id, news_id)
    return success_response(
        message="收藏成功" if added else "已经收藏过了",
        data={"isFavorite": True}
    )


@router.delete("/remove")
async def remove_favorite(
        news_id: int = Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """取消收藏：没收藏过也返回成功，前端不用处理额外情况"""
    await favorite_crud.remove_favorite(db, user.id, news_id)
    return success_response(message="取消收藏成功", data={"isFavorite": False})


@router.delete("/clear")
async def clear_favorites(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """清空当前用户的全部收藏"""
    count = await favorite_crud.clear_favorites(db, user.id)
    return success_response(message=f"已清空{count}条收藏", data={"count": count})


@router.get("/list")
async def get_favorite_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, alias="pageSize", ge=1, le=100),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """分页获取当前用户的收藏列表"""
    rows, total = await favorite_crud.get_favorite_list(db, user.id, page, page_size)
    data = {
        "list": [
            {
                "id": news.id,
                "title": news.title,
                "image": news.image,
                "author": news.author,
                "publishTime": news.publish_time,
                "favoriteTime": created_at
            }
            for news, created_at in rows
        ],
        "total": total,
        "hasMore": page * page_size < total
    }
    return success_response(message="获取收藏列表成功", data=data)
