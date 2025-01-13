import logging
import json

import asyncio
from asyncio.tasks import Task

from typing import Optional, List, Sequence, Tuple
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from sqlalchemy import (
    DateTime,
    String,
    Float,
    Integer,
    ForeignKey,
    select
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncConnection,
    AsyncAttrs
)

from redis.asyncio.client import Redis, PubSub

from fastapi import FastAPI, WebSocket, WebSocketDisconnect


class Base(AsyncAttrs, DeclarativeBase):
    pass


class KRC20Transaction(Base):
    __tablename__ = "krc20_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_source: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(6), nullable=False)
    krc20_amount: Mapped[float] = mapped_column(Float, nullable=False)
    kas_amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    source: Mapped["Source"] = relationship(back_populates="krc20_transactions")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    link: Mapped[Optional[str]] = mapped_column(String)

    krc20_transactions: Mapped[List["KRC20Transaction"]] = relationship(back_populates="source")


config: dict = {
    "last_krc20_transactions_count": 100,
    "last_krc20_transactions_kspr_count": 100
}

logging.basicConfig(
    filename="app.log",
    format="[%(levelname)s] %(asctime)s: %(name)s %(message)s",
    level=logging.WARNING
)

app_logger: logging.Logger = logging.getLogger("app_logger")
file_handler: logging.FileHandler = logging.FileHandler("app.log")
console_handler: logging.StreamHandler = logging.StreamHandler()
formatter: logging.Formatter = logging.Formatter("[%(levelname)s] %(asctime)s: %(name)s %(message)s")

app_logger.setLevel(logging.DEBUG)
file_handler.setLevel(logging.INFO)
console_handler.setLevel(logging.DEBUG)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

app_logger.addHandler(file_handler)
app_logger.addHandler(console_handler)

app_logger.propagate = False

engine: AsyncEngine = create_async_engine(
    "postgresql+asyncpg://main:vHkSbSY&526_*22a@db/main"
)
async_session: async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

redis_client: Redis = Redis(host="redis-server", decode_responses=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    last_krc20_transactions, last_krc20_transactions_kspr = await get_last_krc20_transactions()

    last_krc20_transactions_redis: list[str] = await krc20_transactions_to_redis(
        last_krc20_transactions
    )
    last_krc20_transactions_kspr_redis: list[str] = await krc20_transactions_to_redis(
        last_krc20_transactions_kspr
    )

    await init_redis(last_krc20_transactions_redis, last_krc20_transactions_kspr_redis)
    yield


app: FastAPI = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan
)


async def get_last_krc20_transactions() -> Tuple[Sequence[KRC20Transaction], Sequence[KRC20Transaction]]:
    async with async_session() as session:
        last_krc20_transactions: Sequence[KRC20Transaction] = (await session.execute(
            select(KRC20Transaction).order_by(
                KRC20Transaction.created_at.desc()
            ).limit(
                config["last_krc20_transactions_count"]
            )
        )).scalars().all()

        last_krc20_transactions_kspr: Sequence[KRC20Transaction] = (await session.execute(
            select(KRC20Transaction).where(
                KRC20Transaction.id_source == 1
            ).order_by(
                KRC20Transaction.created_at.desc()
            ).limit(
                config["last_krc20_transactions_count"]
            )
        )).scalars().all()

    return last_krc20_transactions, last_krc20_transactions_kspr


async def krc20_transactions_to_redis(transactions: Sequence[KRC20Transaction]) -> list[str]:
    transactions_redis: list[str] = []

    for transaction in transactions:
        transaction_redis: str = json.dumps({
            "id_source": transaction.id_source,
            "ticker": transaction.ticker,
            "krc20_amount": transaction.krc20_amount,
            "kas_amount": transaction.kas_amount,
            "created_at": int(transaction.created_at.timestamp() * 1000)
        })

        transactions_redis.append(transaction_redis)

    return transactions_redis


async def init_redis(
        last_krc20_transactions: list[str],
        last_krc20_transactions_kspr: list[str]
):
    await redis_client.delete("last_krc20_transactions", "last_krc20_transactions_kspr")

    await redis_client.rpush("last_krc20_transactions", *last_krc20_transactions)
    await redis_client.rpush("last_krc20_transactions_kspr", *last_krc20_transactions_kspr)


async def init_db():
    conn: AsyncConnection

    app_logger.info("Init DB")

    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        source: Optional[Source] = (await session.execute(
            select(Source).limit(1)
        )).scalar()

        if source is None:
            app_logger.info("Sources not found - INIT")

            session.add(
                Source(id=1, name="KSPR Bot", link="https://t.me/kspr_home_bot?start=AXGfUlw")
            )

            await session.commit()


async def add_pupsub_reader(pubsub: PubSub, websocket: WebSocket):
    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.2)

        if message:
            await websocket.send_text(message["data"])


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()

    pubsub: PubSub = redis_client.pubsub()
    await pubsub.subscribe("updates")
    pubsub_reader: Task = asyncio.create_task(add_pupsub_reader(pubsub, websocket))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await pubsub.unsubscribe()
        pubsub_reader.cancel()
