import yaml
import asyncio
from rabbit_parsers import MessageRabbit
from prefixes import Prefixes
from aiopg import connect
import sentry_sdk
from logging import basicConfig, INFO, getLogger
from sys import stderr


basicConfig(stream=stderr, level=INFO, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = getLogger(__name__)


async def main(config):
    if config.get("sentry"):
        sentry_sdk.init(config["sentry"])
    prefixes = Prefixes()
    rabbit = MessageRabbit(config, prefixes)
    async with connect(config["postgres_uri"]) as conn:
        await prefixes.init(conn)
    await rabbit.connect()
    log.info("Connected")
    await rabbit.consume()


if __name__ == "__main__":
    with open("config.yaml") as conf_file:
        config = yaml.load(conf_file, Loader=yaml.SafeLoader)

    asyncio.run(main(config))
