import yaml
import asyncio
from rabbit_parsers import MessageRabbit


async def main(config):
    rabbit = MessageRabbit(config)
    await rabbit.connect()
    print("Connected")
    await rabbit.consume()


if __name__ == "__main__":
    with open("config.yaml") as conf_file:
        config = yaml.load(conf_file, Loader=yaml.SafeLoader)

    asyncio.run(main(config))
