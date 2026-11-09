from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
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
    """添加收藏；已经收藏过则返回 False（接口保持幂等）

    并发场景下两个请求可能同时通过 is_favorite 的检查，
    最终由 user_news_unique 唯一约束兜底，
    再用 SAVEPOINT 把冲突的回滚范围限制在这一条 INSERT 上。
    """
    # 快速路径：顺序重复（比如用户重复点击）直接返回，不制造异常
    if await is_favorite(db, user_id, news_id):
        return False

    try:
        # begin_nested() 在当前事务里打一个保存点，而不是新开事务；
        # 正常退出会 RELEASE SAVEPOINT，异常退出只 ROLLBACK 到保存点，
        # 外层事务（get_db 里统一 commit）不受影响
        async with db.begin_nested():
            db.add(Favorite(user_id=user_id, news_id=news_id))
            # flush 才真正发送 INSERT；重复收藏时错误在这里抛出
            await db.flush()
    except IntegrityError as e:
        # 只把 MySQL 的“重复键”当作“已收藏”处理，其他完整性错误继续往上抛
        # e.orig 是底层驱动（pymysql）的原始异常，args[0] 是错误码
        errno = (getattr(e.orig, "args", None) or (None,))[0]
        if errno == 1062:  # MySQL: Duplicate entry
            return False
        raise
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
