from typing import Dict, Tuple
from asyncio import ensure_future
from aiohttp import ClientSession
from humanfriendly import format_timespan
from rabbit_helper import Rabbit
from message_regex import get_message_types


class RateLimiter:
    def __init__(self, redis, label: str, limit: int, time: int, overrides: Dict[str, Tuple[int, int]]):
        self.redis = redis
        self.label = label
        self.limit = limit, time
        self.overrides = overrides

    async def is_rate_limited(self, key: str) -> int:
        limit, time = self.overrides.get(key, self.limit)
        key = f"{self.label}.{time}.{key}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, time)
        return max(count, limit) - limit

    def __str__(self):
        return f"{self.label} ({self.limit[0]}/{format_timespan(self.limit[1])})"


class MessageRabbit(Rabbit):
    rate_limits = {}

    def __init__(self, config, redis, prefixes):
        super(MessageRabbit, self).__init__(config["rabbit_uri"])
        self.webhook_url = config.get("ratelimit_webhook")
        self.prefixes = prefixes
        # 300 every half hour
        self.someone_rate_limiter = RateLimiter(redis, "someone_rate_limit", 300, 1800, {})
        # 400 every half hour
        self.command_rate_limiter = RateLimiter(redis, "command_rate_limit", 400, 1800, {})
        # 2500 every hour
        self.message_rate_limiter = RateLimiter(redis, "message_rate_limit", 2500, 3600, {})

    async def parse_message_create_raw_0(self, data):
        message_types = get_message_types(data["content"], prefix=self.prefixes[data.get("guild_id")])
        if message_types:
            tokens = set(token for token, *data in message_types)

            is_bot = data["author"].get("bot")
            if not is_bot:
                if tokens == {"@someone"}:
                    if "guild_id" in data and not await self.is_rate_limited(data, self.someone_rate_limiter):
                        await self.send_at_someone(data)
                elif tokens == {"prefix"}:
                    if not await self.is_rate_limited(data, self.command_rate_limiter):
                        await self.send_command(data, *message_types[0][1:])
                else:
                    if "guild_id" in data and not await self.is_rate_limited(data, self.message_rate_limiter):
                        await self.send_webhook(data, message_types)
            # Allow rendered emote events to be picked up regardless of if they were sent by bots
            if "rendered_emote" in tokens and "guild_id" in data:
                await self.send_rendered_emote(data, message_types)

    async def parse_guild_prefix_set_0(self, data):
        self.prefixes[str(data["guild_id"])] = data["prefix"]

    async def parse_guild_delete_0(self, guild):
        del self.prefixes[guild["id"]]

    async def is_rate_limited(self, data, limiter: RateLimiter) -> bool:
        key = data.get("guild_id") or data["channel_id"]
        over_limit = await limiter.is_rate_limited(key)
        if over_limit:
            ensure_future(self.post_webhook(key, limiter, over_limit))
        return bool(over_limit)

    async def post_webhook(self, key: str, limiter: RateLimiter, over_limit: int):
        if self.webhook_url and over_limit % 10 == 1:
            async with ClientSession() as session:
                await session.post(self.webhook_url, json={"content": f"{limiter} ({key}), {over_limit} over limit"})

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
