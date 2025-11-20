import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from diskcache import Cache
from sqlalchemy import and_, join, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from .database import Base, Response, Trigger, WordbankFTS, async_session, engine


@dataclass
class TriggerCache:
    trigger_text: Optional[str]
    trigger_id: int
    trigger_config: Dict
    availability: bool
    responses: Dict[int, List[Response]] = field(default_factory=dict)

    def add_response(self, response: Response):
        if response.priority not in self.responses:
            self.responses[response.priority] = []
        self.responses[response.priority].append(response)


@dataclass
class WordbankCache:
    message_trigger_cache: dict[str, TriggerCache]
    extra_trigger_cache: dict[str, TriggerCache]


class ImageCache:
    def __init__(
        self,
        cache_dir: str = str(Path(__file__).parent / "imagecache"),
        size_limit=10 * 1024 * 1024 * 1024,
    ):
        self.cache = Cache(cache_dir, size_limit=size_limit)
        self.default_ttl = 7 * 24 * 60 * 60

    def check_image(self, filename: str):
        return filename in self.cache

    def get_image(self, filename: str) -> Optional[bytes]:
        return self.cache.get(filename)  # type: ignore

    def set_image(self, filename: str, image: bytes):
        if not self.check_image(filename):
            self.cache.set(filename, image, self.default_ttl)

    def delete_image(self, filename: str):
        self.cache.delete(filename)


async def init_wordbank() -> None:
    async with engine.begin() as conn:
        await conn.exec_driver_sql("drop table if exists public.wordbank_fts;")
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
    async with async_session() as session:
        await session.execute(
            insert(WordbankFTS).from_select(
                [
                    "trigger_id",
                    "trigger_text",
                    "response_id",
                    "response_text",
                    "created_by",
                    "created_at",
                    "trigger_config",
                    "response_rule_conditions",
                    "extra_info",
                ],
                select(
                    Trigger.trigger_id,
                    Trigger.trigger_text,
                    Response.response_id,
                    Response.response_text,
                    Response.created_by,
                    Response.created_at,
                    Trigger.trigger_config,
                    Response.response_rule_conditions,
                    Trigger.extra_info,
                )
                .select_from(
                    join(Trigger, Response, Trigger.trigger_id == Response.trigger_id)
                )
                .where(Response.availability, Trigger.availability),
            )
        )
        await session.commit()


async def generate_wordbank_cache() -> WordbankCache:
    await init_wordbank()
    message_trigger_cache = {}
    extra_trigger_cache = {}
    async with async_session() as session:
        join_condition = join(
            Trigger, Response, Trigger.trigger_id == Response.trigger_id
        )
        result = await session.execute(
            select(Trigger)
            .select_from(join_condition)
            .options(joinedload(Trigger.response_items))
            .where(and_(Response.availability))
        )
        for trigger in result.unique().scalars().all():
            trigger_cache = TriggerCache(
                trigger_text=trigger.trigger_text,
                trigger_id=trigger.trigger_id,
                trigger_config=trigger.trigger_config,
                availability=trigger.availability,
            )
            for response in trigger.response_items:
                trigger_cache.add_response(response)
            if trigger.trigger_text:
                message_trigger_cache[trigger.trigger_text] = trigger_cache
            else:
                extra_trigger_cache[trigger.extra_info] = trigger_cache
    return WordbankCache(message_trigger_cache, extra_trigger_cache)


image_cache = ImageCache()
