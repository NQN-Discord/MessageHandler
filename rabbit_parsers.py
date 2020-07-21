from rabbit_helper import Rabbit
from message_regex import get_message_types


class MessageRabbit(Rabbit):
    def __init__(self, config, prefixes):
        super(MessageRabbit, self).__init__(config["rabbit_uri"])
        self.prefixes = prefixes

    async def parse_message_create_raw_0(self, data):
        message_types = get_message_types(data["content"], prefix=self.prefixes[data.get("guild_id")])
        if message_types:
            tokens = set(token for token, *data in message_types)

            is_bot = data["author"].get("bot")
            if not is_bot:
                if tokens == {"@someone"}:
                    await self.send_at_someone(data)
                elif tokens == {"prefix"}:
                    await self.send_command(data, *message_types[0][1:])
                else:
                    await self.send_webhook(data, message_types)
            # Allow rendered emote events to be picked up regardless of if they were sent by bots
            if "rendered_emote" in tokens and "guild_id" in data:
                await self.send_rendered_emote(data, message_types)

    async def parse_guild_prefix_set_0(self, data):
        self.prefixes[str(data["guild_id"])] = data["prefix"]

    async def parse_guild_delete_0(self, guild):
        del self.prefixes[guild["id"]]

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

    @Rabbit.sender("RENDERED_EMOTE", 1)
    def send_rendered_emote(self, data, message_types):
        return {
            "tokens": [token for token_type, token in message_types if token_type == "rendered_emote"],
            "guild_id": data["guild_id"],
            "channel_id": data["channel_id"]
        }
