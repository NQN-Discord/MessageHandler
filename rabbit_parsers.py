from rabbit_helper import Rabbit
from message_regex import get_message_types


class MessageRabbit(Rabbit):
    EXCHANGE = "GUILD_STATE"

    def __init__(self, config):
        super(MessageRabbit, self).__init__(config["rabbit_uri"])
        self.postgres_uri = config["postgres_uri"]
        self.messages = []

    async def parse_message_create_raw_0(self, data):
        message_types = get_message_types(data["content"])
        if message_types:
            tokens = set(token for token, *data in message_types)
            if tokens == {"@someone"}:
                await self.send_at_someone(data)
            elif tokens == {"prefix"}:
                await self.send_command(data)
            else:
                await self.send_webhook(data, message_types)
                if "rendered_emote" in tokens:
                    await self.send_rendered_emote(message_types)

    @Rabbit.sender("AT_SOMEONE", 0)
    async def send_at_someone(self, data):
        return {
            "message_id": data["id"],
            "channel_id": data["channel_id"],
            "guild_id": data["guild_id"]
        }

    @Rabbit.sender("COMMAND", 0)
    async def send_command(self, data):
        return data

    @Rabbit.sender("WEBHOOK", 0)
    async def send_webhook(self, data, message_types):
        return {
            "message": data,
            "message_types": message_types
        }

    @Rabbit.sender("RENDERED_EMOTE", 0)
    async def send_rendered_emote(self, message_types):
        return [token for token_type, token in message_types if token_type == token]
