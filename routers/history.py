from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import history as history_crud
from crud import news as news_crud
from models.users import User
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("/add")
async def add_history(
        news_id: int = Body(..., alias="newsId", embed=True),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """添加浏览历史：同一新闻重复浏览只刷新浏览时间"""
    if await news_crud.get_news(db, news_id) is None:
        raise HTTPException(status_code=404, detail="新闻不存在")

    view_time = await history_crud.record_history(db, user.id, news_id)
    return success_response(
        message="添加浏览历史成功",
        data={"newsId": news_id, "viewTime": view_time}
    )


@router.get("/list")
async def get_history_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(50, alias="pageSize", ge=1, le=100),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """分页获取当前用户的浏览历史，默认一次返回50条（前端历史页不分页）"""
    rows, total = await history_crud.get_history_list(db, user.id, page, page_size)
    data = {
        "list": [
            {
                "id": news.id,
                "title": news.title,
                "image": news.image,
                "author": news.author,
                "publishTime": news.publish_time,
                "viewTime": view_time
            }
            for news, view_time in rows
        ],
        "total": total,
        "hasMore": page * page_size < total
    }
    return success_response(message="获取浏览历史成功", data=data)


@router.delete("/delete/{news_id}")
async def delete_history(
        news_id: int = Path(..., ge=1),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """删除一条浏览历史：列表项里的 id 是新闻id，这里也按新闻id删除"""
    deleted = await history_crud.delete_history(db, user.id, news_id)
    return success_response(
        message="删除成功" if deleted else "该记录不存在或已删除",
        data={"deleted": deleted}
    )


@router.delete("/clear")
async def clear_history(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """清空当前用户的全部浏览历史"""
    count = await history_crud.clear_history(db, user.id)
    return success_response(message=f"已清空{count}条浏览历史", data={"count": count})
