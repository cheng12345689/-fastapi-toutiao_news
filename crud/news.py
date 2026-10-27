from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from models.news import Category, News


async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_news_list(db: AsyncSession, category_id: int, page: int = 1, page_size: int = 10):
    """分页查询指定分类下的新闻，返回(当前页新闻列表, 该分类新闻总数)"""
    # 先查总数，用于前端判断是否还有更多数据
    total_stmt = select(func.count(News.id)).where(News.category_id == category_id)
    total = (await db.execute(total_stmt)).scalar_one()

    # 按发布时间倒序分页查询
    stmt = (
        select(News)
        .where(News.category_id == category_id)
        .order_by(News.publish_time.desc(), News.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), total

# 获得新闻详情
async def get_news(db: AsyncSession, news_id: int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalars().one_or_none()


async def increase_news_views(db: AsyncSession, news_id: int):
    """浏览量 +1，交给数据库自增，避免并发时丢失更新"""
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)
    await db.execute(stmt)


async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 3):
    """相关新闻：同分类下的其他新闻，按发布时间倒序"""
    stmt = (
        select(News.id, News.title, News.image)
        .where(News.category_id == category_id, News.id != news_id)
        .order_by(News.publish_time.desc(), News.id.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [dict(row) for row in result.mappings()]
