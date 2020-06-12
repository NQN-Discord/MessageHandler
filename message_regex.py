from typing import List


def run_profiling(messages: List):
    # Messages I care about:
    #
    print(len(messages))


if __name__ == "__main__":
    import json
    messages = []
    with open("messages.json") as messages_f:
        all = messages_f.read()
        i = 1
        while all:
            print("Loading part", i)
            i += 1

            data, end = json.JSONDecoder().raw_decode(all)
            messages.extend(data)
            all = all[end:]
    run_profiling(messages)
