from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Favorite(Base):
    """新闻收藏表：用户和新闻的多对多关联

    表里只有 created_at，没有 updated_at，所以不混入 TimestampMixin。
    """
    __tablename__ = "favorite"
    # 同一用户对同一篇新闻只能收藏一次
    __table_args__ = (
        UniqueConstraint("user_id", "news_id", name="user_news_unique"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="收藏id")
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="用户id"
    )
    news_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("news.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="新闻id"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="收藏时间"
    )

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, news_id={self.news_id})>"
