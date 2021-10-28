import re
import asyncio
import aiohttp
from retrie.trie import Trie
from . import message_regex


phishing_domains_regex = re.compile("$.^")
url = "http://192.168.11.39:86/gimme-domains"


async def phish_loop(bot):
    global phishing_domains_regex
    while True:
        phishing_domains_regex = await get_phishing_domains()
        message_regex.message_regex = re.compile(message_regex.colon_regex.format(phishing=f"(?P<phish>{phishing_domains_regex.pattern})|"))
        await asyncio.sleep(30)


async def get_phishing_domains() -> re.Pattern:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            phishing_domains = await resp.json()
    assert isinstance(phishing_domains, list)
    trie = Trie()
    for domain in phishing_domains:
        trie.add(domain)
    return re.compile(rf"(?:\b{trie.pattern()}\b)")
