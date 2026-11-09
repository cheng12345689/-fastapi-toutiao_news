from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.history import History
from models.news import News


async def record_history(db: AsyncSession, user_id: int, news_id: int) -> datetime:
    """记录一次浏览，返回本次浏览时间

    同一用户对同一篇新闻只保留一条记录：
    先尝试更新 view_time，没命中再插入新记录。
    （表上没有唯一约束，极端并发下仍可能插出重复行，正常浏览场景不会触发）
    """
    now = datetime.now()
    stmt = (
        update(History)
        .where(History.user_id == user_id, History.news_id == news_id)
        .values(view_time=now)
    )
    result = await db.execute(stmt)
    if result.rowcount == 0:
        db.add(History(user_id=user_id, news_id=news_id, view_time=now))
        # flush 才真正发送 INSERT，让唯一性/外键错误在这里暴露
        await db.flush()
    return now


async def get_history_list(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 50):
    """分页查询浏览历史，返回 (当前页数据, 历史总数)

    每项是 (News 对象, 浏览时间) 的元组，拼装响应交给路由层。
    """
    # 先查总数，用于前端判断是否还有更多数据
    total_stmt = select(func.count(History.id)).where(History.user_id == user_id)
    total = (await db.execute(total_stmt)).scalar_one()

    # 最近浏览的排在前面
    stmt = (
        select(News, History.view_time)
        .join(History, History.news_id == News.id)
        .where(History.user_id == user_id)
        .order_by(History.view_time.desc(), History.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return result.all(), total


async def delete_history(db: AsyncSession, user_id: int, news_id: int) -> bool:
    """删除一条浏览历史（按新闻id），返回是否真的删除了记录"""
    stmt = delete(History).where(
        History.user_id == user_id,
        History.news_id == news_id
    )
    result = await db.execute(stmt)
    return result.rowcount > 0


async def clear_history(db: AsyncSession, user_id: int) -> int:
    """清空该用户的全部浏览历史，返回删除条数"""
    result = await db.execute(delete(History).where(History.user_id == user_id))
    return result.rowcount
