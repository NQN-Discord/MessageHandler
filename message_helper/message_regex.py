from typing import List
import re
from sys import intern
import asyncio

colon_regex = (
    r"(?P<persona>^(?!http)[a-zA-Z0-9_-]{{1,80}}(?=:))|"
    r"(?P<rendered_emote><a?:[a-zA-Z0-9_]+:\d+>)|"
    r"(?P<unrendered_emote>:(?:[a-zA-Z0-9_]+-)?[a-zA-Z0-9_]+:(?!\d+>))|"
    r"(?P<message_link>\b(?:https?://(?:[a-z]+\.)?)?discord(?:app)?\.com/channels/\d+/\d+/\d+\b(?!>))|"
    r"(?P<sticker>:[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+:)|"
    r"{phishing}"
    r"(?P<masked_url>\[.*\]\(<?(?:https?|button)://[-a-zA-Z0-9:._]{{1,256}}\.[a-zA-Z0-9]{{1,6}}\b[-a-zA-Z0-9@:%_+.~#?&/=]*>?\))"
)
message_regex = re.compile(colon_regex.format(phishing=""))


def get_message_types(content, prefix: str = "!") -> List[List[str]]:
    if not content:
        return []
    if content.startswith(prefix):
        return [["prefix", prefix, content.replace(prefix, "", 1).lstrip(" ")]]
    elif content[:21] in {
        "<@!559426966151757824", "<@559426966151757824>",
        "<@!561541673750888481", "<@561541673750888481>",
        "<@!734103864785109022", "<@734103864785109022>",
    }:
        return [["prefix", prefix, content[21:].lstrip("> ")]]
    elif ":" in content:
        return [[intern(m.lastgroup), m.group()] for m in message_regex.finditer(content)]
    elif content == "@someone":
        return [["@someone"]]
    return []


async def run_profiling(messages: List[str]):
    global message_regex
    phishing_domains_regex = await get_phishing_domains()
    message_regex = re.compile(colon_regex.format(phishing=f"(?P<phish>{phishing_domains_regex.pattern})|"))

    print(_profile(messages))

    times = timeit.Timer(lambda: _profile(messages)).repeat(number=1, repeat=10)
    print(f"min {min(times):.4f}s avg {statistics.mean(times):.4f}s")


def _profile(messages):
    message_types = {
        "@someone": 0,
        "prefix": 0,
        "rendered_emote": 0,
        "unrendered_emote": 0,
        "message_link": 0,
        "sticker": 0,
        "masked_url": 0,
        "persona": 0,
        "phish": 0
    }
    for message in messages:
        for match, *data in get_message_types(message):
            message_types[match] += 1
    return message_types


if __name__ == "__main__":
    import json
    import timeit
    import statistics
    from phish_detection import get_phishing_domains
    with open(r"messages.jsonl") as messages_f:
        messages = [json.loads(l.strip("\n")) for l in messages_f.readlines()]

    asyncio.run(run_profiling(messages))
