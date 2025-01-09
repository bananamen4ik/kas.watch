import re
import asyncio
import logging

from typing import Optional, List
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
    AsyncConnection,
    AsyncAttrs
)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class KRC20Transaction(Base):
    __tablename__ = "krc20_transcations"

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


logging.basicConfig(
    filename="app.log",
    format="[%(levelname)s] %(asctime)s: %(name)s %(message)s",
    level=logging.WARNING
)

app_logger = logging.getLogger("app_logger")
file_handler = logging.FileHandler("app.log")
console_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(asctime)s: %(name)s %(message)s")

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
client: TelegramClient = TelegramClient("profile", api_id, api_hash)
is_synced: bool = False


@client.on(events.NewMessage())
async def new_message(event: events.NewMessage.Event):
    global is_synced

    message: Message = event.message
    peer_id: TypePeer = message.peer_id
    from_id: Optional[TypePeer] = message.from_id
    message_text: str = message.message

    if not is_synced:
        return

    if not isinstance(peer_id, PeerChannel) or not isinstance(from_id, PeerUser):
        return

    if peer_id.channel_id != 2193761946 or from_id.user_id != 7338170991:
        return

    message_data: Optional[dict] = await get_message_data(message_text)
    if message_data is None:
        app_logger.warning(f"Skip new message: {message_text}")
        return

    async with async_session() as session:
        new_transaction: KRC20Transaction = KRC20Transaction(
            id_source=1,
            ticker=message_data["ticker"],
            krc20_amount=message_data["krc20_amount"],
            kas_amount=message_data["kas_amount"],
            created_at=message.date
        )

        session.add(new_transaction)
        await session.commit()

    app_logger.info("Added new transcation")
    app_logger.debug(message_text)


async def init_db():
    conn: AsyncConnection

    app_logger.info("Init DB")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
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


async def get_message_data(message_text: str) -> Optional[dict]:
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
        last_transaction: Optional[KRC20Transaction] = (await session.execute(
            select(KRC20Transaction).order_by(KRC20Transaction.created_at.desc()).limit(1)
        )).scalar()

        if last_transaction:
            to_date = last_transaction.created_at

        async for message in client.iter_messages(
                PeerChannel(2193761946),
                from_user=PeerUser(7338170991)
        ):
            message_data: Optional[dict] = await get_message_data(message.message)

            if message_data is None:
                app_logger.debug(f"SKIP {message.message}")
                continue

            if message.date <= to_date:
                break

            new_transaction: KRC20Transaction = KRC20Transaction(
                id_source=1,
                ticker=message_data["ticker"],
                krc20_amount=message_data["krc20_amount"],
                kas_amount=message_data["kas_amount"],
                created_at=message.date
            )

            session.add(new_transaction)
            await session.flush()

            app_logger.debug(f"Added new transaction {message.date}")

        await session.commit()


async def main():
    global is_synced

    app_logger.info("App starting..")

    await init_db()

    await client.start()
    await sync_krc20_transactions()

    await sync_krc20_transactions()
    is_synced = True

    app_logger.info("App started successfully")

    await client.run_until_disconnected()

    app_logger.info("App closed")


asyncio.run(main())
