from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News


async def is_favorite(db: AsyncSession, user_id: int, news_id: int) -> bool:
    """判断用户是否已收藏该新闻"""
    stmt = select(Favorite.id).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def add_favorite(db: AsyncSession, user_id: int, news_id: int) -> bool:
    """添加收藏；已经收藏过则返回 False（接口保持幂等）"""
    if await is_favorite(db, user_id, news_id):
        return False

    db.add(Favorite(user_id=user_id, news_id=news_id))
    await db.flush()
    return True


async def remove_favorite(db: AsyncSession, user_id: int, news_id: int) -> bool:
    """取消收藏，返回是否真的删除了记录"""
    stmt = delete(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id
    )
    result = await db.execute(stmt)
    return result.rowcount > 0


async def clear_favorites(db: AsyncSession, user_id: int) -> int:
    """清空该用户的全部收藏，返回删除条数"""
    result = await db.execute(delete(Favorite).where(Favorite.user_id == user_id))
    return result.rowcount


async def get_favorite_list(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10):
    """分页查询收藏列表，返回 (当前页数据, 收藏总数)

    每项是 (News 对象, 收藏时间) 的元组，拼装响应交给路由层。
    """
    # 先查总数，用于前端判断是否还有更多数据
    total_stmt = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
    total = (await db.execute(total_stmt)).scalar_one()

    stmt = (
        select(News, Favorite.created_at)
        .join(Favorite, Favorite.news_id == News.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc(), Favorite.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return result.all(), total
