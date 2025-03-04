import re
import asyncio
import logging
import json
import os

from datetime import datetime, timezone

from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
from telethon.tl.types import TypePeer, PeerChannel, PeerUser

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
    AsyncAttrs
)

from redis.asyncio import Redis


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
        nullable=False
    )

    source: Mapped["Source"] = relationship(back_populates="krc20_transactions")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    link: Mapped[str | None] = mapped_column(String)

    krc20_transactions: Mapped[list["KRC20Transaction"]] = relationship(back_populates="source")


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

api_id: int = 25341299
api_hash: str = "6594f728fbae8e3a7ede766ef7c494bd"
client: TelegramClient = TelegramClient(os.getenv("TG_SESSION_FILE_NAME", "profile-dev"), api_id, api_hash)
is_synced: bool = False

redis_client: Redis = Redis(host="redis-server", decode_responses=True)


@client.on(events.NewMessage())
async def new_message(event: events.NewMessage.Event):
    global is_synced

    message: Message = event.message
    peer_id: TypePeer = message.peer_id
    from_id: TypePeer | None = message.from_id
    message_text: str = message.message

    if not is_synced:
        return

    if not isinstance(peer_id, PeerChannel) or not isinstance(from_id, PeerUser):
        return

    if peer_id.channel_id != 2193761946 or from_id.user_id != 7338170991:
        return

    message_data: dict | None = await get_message_data(message_text)
    if message_data is None:
        app_logger.warning(f"Skip new message: {message_text}")
        return

    message_data["id_source"] = 1
    message_data["created_at"] = message.date

    async with async_session() as session:
        new_transaction: KRC20Transaction = KRC20Transaction(
            id_source=message_data["id_source"],
            ticker=message_data["ticker"],
            krc20_amount=message_data["krc20_amount"],
            kas_amount=message_data["kas_amount"],
            created_at=message_data["created_at"]
        )

        session.add(new_transaction)
        await session.commit()

    message_data["created_at"] = int(message.date.timestamp() * 1000)
    await send_krc20_transaction_to_redis(message_data)

    app_logger.info("Added new transaction")
    app_logger.debug(message_text)


async def send_krc20_transaction_to_redis(message_data: dict):
    message_data_json: str = json.dumps(message_data)
    data: str = json.dumps({
        "method": "last_krc20_transaction",
        "data": message_data_json
    })

    await redis_client.lpush("last_krc20_transactions_kspr", message_data_json)
    await redis_client.lpush("last_krc20_transactions", message_data_json)

    if (await redis_client.llen("last_krc20_transactions_kspr")) > config["last_krc20_transactions_kspr_count"]:
        await redis_client.rpop("last_krc20_transactions_kspr")

    if (await redis_client.llen("last_krc20_transactions")) > config["last_krc20_transactions_count"]:
        await redis_client.rpop("last_krc20_transactions")

    await redis_client.publish("updates", data)


async def get_message_data(message_text: str) -> dict | None:
    ticker_pattern: str = r"Ticker: (.+?)\n"
    krc20_amount_pattern: str = r"KRC20 Amount: (.+?)\n"
    kas_amount_pattern: str = r"KAS Amount: (.+?)\n"

    try:
        ticker: str = re.search(ticker_pattern, message_text).group(1)
        krc20_amount: float = float(re.search(krc20_amount_pattern, message_text).group(1))
        kas_amount: float = float(re.search(kas_amount_pattern, message_text).group(1))
    except AttributeError:
        return None

    return {
        "ticker": ticker,
        "krc20_amount": krc20_amount,
        "kas_amount": kas_amount
    }


async def sync_krc20_transactions():
    message: Message

    to_date: datetime = datetime(
        2025,
        1,
        1,
        0,
        0,
        0,
        0,
        timezone.utc
    )

    app_logger.info("Started sync krc20 transactions")

    async with async_session() as session:
        last_transaction: KRC20Transaction | None = (await session.execute(
            select(KRC20Transaction).order_by(KRC20Transaction.created_at.desc()).limit(1)
        )).scalar()
        last_transactions: list[dict] = []

        if last_transaction:
            to_date = last_transaction.created_at

        async for message in client.iter_messages(PeerChannel(2193761946)):
            if message.from_id == PeerUser(7338170991):
                break

        async for message in client.iter_messages(
                PeerChannel(2193761946),
                from_user=PeerUser(7338170991)
        ):
            message_data: dict | None = await get_message_data(message.message)

            if message_data is None:
                app_logger.debug(f"SKIP {message.message}")
                continue

            if message.date <= to_date:
                break

            message_data["id_source"] = 1
            message_data["created_at"] = message.date

            new_transaction: KRC20Transaction = KRC20Transaction(
                id_source=message_data["id_source"],
                ticker=message_data["ticker"],
                krc20_amount=message_data["krc20_amount"],
                kas_amount=message_data["kas_amount"],
                created_at=message_data["created_at"]
            )

            session.add(new_transaction)
            await session.flush()

            message_data["created_at"] = int(message.date.timestamp() * 1000)
            if len(last_transactions) < config["last_krc20_transactions_count"]:
                last_transactions.append(message_data)

            app_logger.debug(f"Added new transaction {message.date}")

        await session.commit()

        for transaction in reversed(last_transactions):
            await send_krc20_transaction_to_redis(transaction)


async def main():
    global is_synced

    while await redis_client.get("fastapi-core-ready") is None:
        await asyncio.sleep(1)

    app_logger.info("App starting..")

    await client.start()
    await sync_krc20_transactions()

    await sync_krc20_transactions()
    is_synced = True

    app_logger.info("App started successfully")

    await client.run_until_disconnected()

    app_logger.info("App closed")


asyncio.run(main())
