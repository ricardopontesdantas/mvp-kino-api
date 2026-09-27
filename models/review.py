from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, false, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from .base import Base

class Review(Base):
    __tablename__ = 'reviews'

    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'tmdb_movie_id',
            name='uq_reviews_user_movie'
        ),
        CheckConstraint(
            'rating IS NULL OR rating BETWEEN 0 AND 10',
            name='ck_reviews_rating_between_0_and_10'
        )
    )

    review_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'), nullable=False)
    tmdb_movie_id: Mapped[int] = mapped_column(nullable=False)
    tmdb_movie_title: Mapped[str] = mapped_column(String(255), nullable=False)
    watched: Mapped[bool] = mapped_column(server_default=false(), nullable=False)
    rating: Mapped[int | None] = mapped_column(nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
