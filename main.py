import yaml
import asyncio
from rabbit_parsers import MessageRabbit
from prefixes import Prefixes
from aiopg import connect


async def main(config):
    prefixes = Prefixes()
    rabbit = MessageRabbit(config, prefixes)
    async with connect(config["postgres_uri"]) as conn:
        await prefixes.init(conn)
    await rabbit.connect()
    print("Connected")
    await rabbit.consume()


if __name__ == "__main__":
    with open("config.yaml") as conf_file:
        config = yaml.load(conf_file, Loader=yaml.SafeLoader)

    asyncio.run(main(config))
