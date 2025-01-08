import re
from typing import Optional

import asyncio

from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
from telethon.tl.types import TypePeer, PeerChannel, PeerUser

api_id: int = 25341299
api_hash: str = "6594f728fbae8e3a7ede766ef7c494bd"
client: TelegramClient = TelegramClient("profile", api_id, api_hash)


@client.on(events.NewMessage())
async def new_message(event: events.NewMessage.Event):
    message: Message = event.message
    peer_id: TypePeer = message.peer_id
    from_id: Optional[TypePeer] = message.from_id
    message_text: str = message.message

    if not isinstance(peer_id, PeerChannel) or not isinstance(from_id, PeerUser):
        return

    if peer_id.channel_id != 2193761946 or from_id.user_id != 7338170991:
        return

    ticker_pattern: str = r"Ticker: (.+?)\\"
    krc20_amount_pattern: str = r"KRC20 Amount: (.+?)\\"
    kas_amount_pattern: str = r"KAS Amount: (.+?)\\"
    price_per_unit_pattern: str = r"Price per unit: (.+?)\\"
    contract_address_pattern: str = r"Contract Address: (.+?)"

    message_text = "🚀 New Transaction\n\n🔹 Ticker: PEPE\n📊 KRC20 Amount: 476574\n💰 KAS Amount: 115\n💵 Price per unit: 0.00024131\n\n🔗 Contract Address: kaspa:qp772xwvjlfa54kajvxz2zyn52mmjf7usctm8e64635885z0eq4rjku0cm962"

    ticker: str = re.search(ticker_pattern, message_text).group(1)
    krc20_amount: float = float(re.search(krc20_amount_pattern, message_text).group(1))
    kas_amount: float = float(re.search(kas_amount_pattern, message_text).group(1))
    price_per_unit: float = float(re.search(price_per_unit_pattern, message_text).group(1))
    contract_address: str = str(re.search(contract_address_pattern, message_text).group(1))

    print("_{}_".format(ticker))
    print("_{}_".format(krc20_amount))
    print("_{}_".format(kas_amount))
    print("_{}_".format(price_per_unit))
    print("_{}_".format(contract_address))


async def main():
    await client.start()
    await client.run_until_disconnected()


asyncio.run(main())
