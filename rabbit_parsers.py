from rabbit_helper import Rabbit
import json


class MessageRabbit(Rabbit):
    EXCHANGE = "GUILD_STATE"

    def __init__(self, config):
        super(MessageRabbit, self).__init__(config["rabbit_uri"])
        self.postgres_uri = config["postgres_uri"]
        self.messages = []

    async def parse_message_create_raw_0(self, data):
        self.messages.append(data)
        if len(self.messages) % 100 == 0:
            print(len(self.messages))
        if len(self.messages) % 10000 == 0:
            with open("messages.json", "a") as json_f:
                json.dump(self.messages, json_f)
                self.messages = []

