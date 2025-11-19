from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    String,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from src.config.general_config import general_config

Base = declarative_base()

DATABASE_URL = f"postgresql+asyncpg://{general_config.pg_username}:{general_config.pg_password}@{general_config.pg_host}:{general_config.pg_port}/senrin_water"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=general_config.pg_pool_size,
    max_overflow=general_config.pg_max_overflow,
)
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
)


async def get_session():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.commit()
            await session.close()


class WaterInfo(Base):
    __tablename__ = "water_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(32), nullable=False)
    group_id: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )


async def init_water_info() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
