import asyncio
import logging
import json

from datetime import datetime, timezone

import aiohttp

from pybit.unified_trading import HTTP

from redis.asyncio import Redis


class ByBit:
    @staticmethod
    async def get_kas_last_price() -> list:
        data: list = ["bybit", None]

        try:
            session: HTTP = HTTP(
                testnet=False,
                api_key="wbpRq2SeFQ5S45OS7c",
                api_secret="BtpsYppPwwTN5daS5M0CXT08nHZS4H7xguTh",
            )

            result: dict = session.get_tickers(
                category="spot",
                symbol="KASUSDT",
            )

            if result["retCode"] == 0:
                data[1] = float(result["result"]["list"][0]["lastPrice"])
            else:
                app_logger.error(f"Bybit error")
        except Exception as exc:
            app_logger.error(f"Bybit error: {exc}")

        return data


class Kraken:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://api.kraken.com/0/public/Ticker?pair=KASUSD"
        data: list = ["kraken", None]

        try:
            result: dict = await fetch(session, url)
            if result["error"]:
                app_logger.error("Kraken error")
            else:
                data[1] = float(result["result"]["KASUSD"]["c"][0])
        except Exception as exc:
            app_logger.error(f"Kraken error: {exc}")

        return data


class Kucoin:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=KAS-USDT"
        data: list = ["kucoin", None]

        try:
            result: dict = await fetch(session, url)
            if result["code"] == "200000":
                data[1] = float(result["data"]["price"])
            else:
                app_logger.error("Kucoin error")
        except Exception as exc:
            app_logger.error(f"Kucoin error: {exc}")

        return data


class Mexc:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://api.mexc.com/api/v3/ticker/price?symbol=KASUSDT"
        data: list = ["mexc", None]

        try:
            result: dict = await fetch(session, url)
            data[1] = float(result["price"])
        except Exception as exc:
            app_logger.error(f"Mexc error: {exc}")

        return data


class Coinex:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://api.coinex.com/v1/market/ticker?market=KASUSDT"
        data: list = ["coinex", None]

        try:
            result: dict = await fetch(session, url)

            if result["code"] == 0:
                data[1] = float(result["data"]["ticker"]["last"])
            else:
                app_logger.error("Coinex error")
        except Exception as exc:
            app_logger.error(f"Coinex error: {exc}")

        return data


class Gate:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://api.gateio.ws/api2/1/ticker/KAS_USDT"
        data: list = ["gate", None]

        try:
            result: dict = await fetch(session, url)

            if result["result"] == "true":
                data[1] = float(result["last"])
            else:
                app_logger.error("Gate error")
        except Exception as exc:
            app_logger.error(f"Gate error: {exc}")

        return data


class Digifinex:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://openapi.digifinex.com/v3/ticker?symbol=kas_usdt"
        data: list = ["digifinex", None]

        try:
            result: dict = await fetch(session, url)

            if result["code"] == 0:
                data[1] = float(result["ticker"][0]["last"])
            else:
                app_logger.error("Digifinex error")
        except Exception as exc:
            app_logger.error(f"Digifinex error: {exc}")

        return data


class Xeggex:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://api.xeggex.com/api/v2/market/info?id=251&symbol=KAS/USDT"
        data: list = ["xeggex", None]

        try:
            result: dict = await fetch(session, url)
            data[1] = float(result["lastPrice"])
        except Exception as exc:
            app_logger.error(f"Xeggex error: {exc}")

        return data


class Uphold:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://api.uphold.com/v0/ticker/KAS-USD"
        data: list = ["uphold", None]

        try:
            result: dict = await fetch(session, url)
            data[1] = float(result["ask"])
        except Exception as exc:
            app_logger.error(f"Uphold error: {exc}")

        return data


class Bitget:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://api.bitget.com/api/v2/spot/market/tickers?symbol=KASUSDT"
        data: list = ["bitget", None]

        try:
            result: dict = await fetch(session, url)

            if result["code"] == "00000":
                data[1] = float(result["data"][0]["lastPr"])
            else:
                app_logger.error("Bitget error")
        except Exception as exc:
            app_logger.error(f"Bitget error: {exc}")

        return data


class Lbank:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://api.lbkex.com/v2/ticker.do?symbol=kas_usdt"
        data: list = ["lbank", None]

        try:
            result: dict = await fetch(session, url)

            if result["result"] == "true":
                data[1] = float(result["data"][0]["ticker"]["latest"])
            else:
                app_logger.error("Lbank error")
        except Exception as exc:
            app_logger.error(f"Lbank error: {exc}")

        return data


class Bydfi:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://www.bydfi.com/b2b/rank/orderbook?market_pair=KAS_USDT&depth=1"
        data: list = ["bydfi", None]

        try:
            result: dict = await fetch(session, url)

            if result["code"] == 200:
                data[1] = float(result["asks"][0]["price"])
            else:
                app_logger.error("Bydfi error")
        except Exception as exc:
            app_logger.error(f"Bydfi error: {exc}")

        return data


class Btse:
    @staticmethod
    async def get_kas_last_price(session: aiohttp.ClientSession) -> list:
        url: str = "https://api.btse.com/spot/api/v3.2/price?symbol=KAS-USDT"
        data: list = ["btse", None]

        try:
            result: dict = await fetch(session, url)
            data[1] = float(result[0]["lastPrice"])
        except Exception as exc:
            app_logger.error(f"Btse error: {exc}")

        return data


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

redis_client: Redis = Redis(host="redis-server", decode_responses=True)


async def fetch(session, url):
    headers: dict = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                      " (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Accept": "application/json",
    }

    try:
        async with session.get(url, headers=headers, ssl=False) as response:
            response.raise_for_status()

            if response.content_type == "text/plain":
                return json.loads(await response.text())
            return await response.json()
    except asyncio.TimeoutError:
        app_logger.error(f"Timeout {url}")
    except Exception as e:
        app_logger.error(f"Unknown error {url}: {e}")


async def main():
    while await redis_client.get("fastapi-core-ready") is None:
        await asyncio.sleep(1)

    app_logger.info("App starting..")

    timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(
        total=10,
        connect=5,
        sock_connect=5,
        sock_read=5
    )

    while True:
        app_logger.info("Requests are being sent")

        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks: list = [
                ByBit.get_kas_last_price(),
                Kraken.get_kas_last_price(session),
                Kucoin.get_kas_last_price(session),
                Mexc.get_kas_last_price(session),
                Coinex.get_kas_last_price(session),
                Gate.get_kas_last_price(session),
                Digifinex.get_kas_last_price(session),
                Xeggex.get_kas_last_price(session),
                Uphold.get_kas_last_price(session),
                Bitget.get_kas_last_price(session),
                Lbank.get_kas_last_price(session),
                Bydfi.get_kas_last_price(session),
                Btse.get_kas_last_price(session)
            ]
            result: str = json.dumps({
                "data": await asyncio.gather(*tasks),
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000)
            })

            data: str = json.dumps({
                "method": "kas-rates",
                "data": result
            })

            await redis_client.set("kas-rates", result)
            await redis_client.publish("updates", data)

        await asyncio.sleep(5)


asyncio.run(main())
