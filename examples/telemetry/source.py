"""Summarize synthetic readings with repeated attribute and literal access."""

from dataclasses import dataclass


@dataclass(slots=True)
class Reading:
    value: int
    label: str


def summarize(rounds=200_000):
    cache = (
        Reading(19, "outdoor sensor"),
        Reading(37, "indoor sensor"),
        Reading(82, "outdoor sensor"),
        Reading(51, "indoor sensor"),
    )
    minimum, checksum = 1000, 0
    current = Reading(0, "")
    for index in range(rounds):
        reading = cache[index & 3]
        current.value = reading.value
        if reading.label == "outdoor sensor":
            minimum = min(minimum, current.value)
        checksum += current.value * 7 % 257
    return minimum, checksum


if __name__ == "__main__":
    print("Temperature readings", summarize())
