import re
import asyncio
import aiohttp
from aiohttp.client_exceptions import ContentTypeError
from retrie.trie import Trie
try:
    from . import message_regex
except ImportError:
    assert __name__ in ("__main__", "phish_detection")


phishing_domains_regex = re.compile("$.^")
url = "http://192.168.11.39:86/gimme-domains"


async def phish_loop(bot):
    global phishing_domains_regex
    while True:
        try:
            phishing_domains_regex = await get_phishing_domains()
        except ContentTypeError:
            pass
        else:
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
    return re.compile(rf"(?:://{trie.pattern()}\b)")


async def _profile_phish(messages):
    import timeit, statistics
    url_regex = re.compile(r"://([-a-zA-Z0-9:._]{1,256}\.[a-zA-Z0-9]{1,6})")
    url_regex_nogroup = re.compile(r"://[-a-zA-Z0-9:._]{1,256}\.[a-zA-Z0-9]{1,6}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            domains_set = set(await resp.json())
    domains_trie = await get_phishing_domains()

    trie_times = timeit.Timer(lambda: _profile_trie(domains_trie, messages)).repeat(number=1, repeat=100)
    print(f"Trie: min {min(trie_times):.4f}s avg {statistics.mean(trie_times):.4f}s")

    set_times = timeit.Timer(lambda: _profile_set(url_regex, domains_set, messages)).repeat(number=1, repeat=100)
    print(f"Set: min {min(set_times):.4f}s avg {statistics.mean(set_times):.4f}s")

    set_nogroup_times = timeit.Timer(lambda: _profile_set_nogroup(url_regex_nogroup, domains_set, messages)).repeat(number=1, repeat=100)
    print(f"Set (no group): min {min(set_nogroup_times):.4f}s avg {statistics.mean(set_nogroup_times):.4f}s")


def _profile_trie(domains_trie, messages):
    total_matches = 0
    for message in messages:
        if ":" not in message:
            continue
        if domains_trie.search(message):
            total_matches += 1
    return total_matches


def _profile_set(url_regex, domains_set, messages):
    total_matches = 0
    for message in messages:
        if ":" not in message:
            continue
        url_match = url_regex.search(message)
        if url_match and url_match.group(1) in domains_set:
            total_matches += 1
    return total_matches


def _profile_set_nogroup(url_regex, domains_set, messages):
    total_matches = 0
    for message in messages:
        if ":" not in message:
            continue
        url_match = url_regex.search(message)
        if url_match and url_match.group()[3:] in domains_set:
            total_matches += 1
    return total_matches


if __name__ == "__main__":
    import json
    with open(r"messages.jsonl") as messages_f:
        messages = [json.loads(l.strip("\n")) for l in messages_f.readlines()]

    asyncio.run(_profile_phish(messages))
