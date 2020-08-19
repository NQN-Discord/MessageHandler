from typing import List
import re

colon_regex = re.compile(
    r"(?P<rendered_emote><a?:[a-zA-Z0-9_]+:\d+>)|"
    r"(?P<unrendered_emote>:(?:[a-zA-Z0-9_]+-)?[a-zA-Z0-9_]+:(?!\d+>))|"
    r"(?P<message_link>\b(?:https?://(?:[a-z]+\.)?)?discord(?:app)?\.com/channels/\d+/\d+/\d+\b(?!>))|"
    r"(?P<sticker>:[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+:)|"
    r"(?P<masked_url>\[.*\]\(<?https?://[a-zA-Z0-9:.-_]{1,256}\.[a-zA-Z0-9]{1,6}\b[-a-zA-Z0-9@:%_+.~#?&/=]*>?\))"
)


def get_message_types(content, prefix: str = "!") -> List[List[str]]:
    if not content:
        return []
    if content.startswith(prefix):
        return [["prefix", prefix, content.replace(prefix, "", 1)]]
    elif content[:22] in {"<@!559426966151757824>", "<@!561541673750888481>", "<@!734103864785109022>"}:
        return [["prefix", prefix, content[22:].strip(" ")]]
    elif ":" in content:
        return [[m.lastgroup, m.group()] for m in colon_regex.finditer(content)]
    elif content == "@someone":
        return [["@someone"]]
    return []


def run_profiling(messages: List[str]):
    # Messages I care about:
    #  @someone
    #  !prefix
    #  Jump URLs
    #  Masked URLs
    #  Rendered emoji
    #  Unrendered emoji

    #  @someone
    #  !prefix
    #  Any message with a colon for further processing
    for message in messages:
        for match, *data in get_message_types(message):
            message_types[match] += 1
    print(message_types, sum(i for i in message_types.values()), len(messages))


if __name__ == "__main__":

    import json as json
    with open(r"messages.json") as messages_f:
        messages = json.load(messages_f)

    message_types = {
        "@someone": 0,
        "prefix": 0,
        "rendered_emote": 0,
        "unrendered_emote": 0,
        "message_link": 0,
        "sticker": 0,
        "masked_url": 0
    }

    run_profiling(messages)
