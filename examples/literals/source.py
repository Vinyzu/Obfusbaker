"""Report the contents of mixed text and binary records."""


def format_record(width, precision, /, *, enabled=True):
    label = """Café #literal
鐘 • 東京 🌱 \u099e \u06f8a"""
    escapes = r"C:\reports\new\test.txt"
    marker = b"\x00\x8b\xfe"
    distance = 3.125
    offset = 2j
    match (enabled, "ready"):
        case (True, "ready"):
            return f"{label!r}: {distance:{width}.{precision}f}", escapes, marker, offset
        case _:
            return f"Inactive {distance=}"


if __name__ == "__main__":
    print(format_record(7, 2))
    print(format_record(7, 2, enabled=False))
