
class Prefixes:
    def __init__(self):
        self.prefixes = {}

    async def init(self, conn):
        async with conn.cursor() as cur:
            await cur.execute("SELECT guild_id, prefix FROM guild_settings")
            for guild_id, prefix in await cur.fetchall():
                self[str(guild_id)] = prefix

    def __setitem__(self, guild_id: str, prefix: str):
        if prefix == "!":
            self.prefixes.pop(guild_id, None)
        else:
            self.prefixes[guild_id] = prefix

    def __getitem__(self, guild_id: str):
        return self.prefixes.get(guild_id, "!")

    def __delitem__(self, guild_id: str):
        self.prefixes.pop(guild_id, None)
