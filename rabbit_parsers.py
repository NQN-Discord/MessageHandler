from rabbit_helper import Rabbit
from message_regex import get_message_types


class MessageRabbit(Rabbit):
    def __init__(self, config, prefixes):
        super(MessageRabbit, self).__init__(config["rabbit_uri"])
        self.prefixes = prefixes

    async def parse_message_create_raw_0(self, data):
        message_types = get_message_types(data["content"], prefix=self.prefixes[data["guild_id"]])
        if message_types:
            tokens = set(token for token, *data in message_types)
            if tokens == {"@someone"}:
                await self.send_at_someone(data)
            elif tokens == {"prefix"}:
                await self.send_command(data, *message_types[0][1:])
            else:
                await self.send_webhook(data, message_types)
                if "rendered_emote" in tokens:
                    await self.send_rendered_emote(message_types)

    @Rabbit.sender("AT_SOMEONE", 0)
    def send_at_someone(self, data):
        return {
            "message_id": data["id"],
            "channel_id": data["channel_id"],
            "guild_id": data["guild_id"],
            "author": data["author"],
            "nickname": data["member"].get("nick")
        }

    @Rabbit.sender("COMMAND", 0)
    def send_command(self, data, prefix, unprefixed_content):
        return {
            "message": data,
            "server_prefix": prefix,
            "unprefixed_content": unprefixed_content
        }

    @Rabbit.sender("RENDER_MESSAGE", 0)
    def send_webhook(self, data, message_types):
        return {
            "message": data,
            "message_types": message_types
        }

    @Rabbit.sender("RENDERED_EMOTE", 0)
    def send_rendered_emote(self, message_types):
        return [token for token_type, token in message_types if token_type == token]
