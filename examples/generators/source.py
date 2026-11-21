"""Group readings into batches and accept a new batch size while streaming."""


def batches(readings, size, events):
    batch = []
    total = 0
    try:
        for reading in readings:
            batch.append(reading)
            total += reading
            if len(batch) == size:
                requested_size = yield tuple(batch)
                batch.clear()
                if requested_size is not None:
                    size = requested_size
        if batch:
            yield tuple(batch)
        return total
    finally:
        events.append("stream closed")


def summarize(readings, events):
    total = yield from batches(readings, 2, events)
    events.append(f"total reading: {total}")


if __name__ == "__main__":
    events = []
    readings = (3, 7, 11, 13, 17, 19)
    stream = summarize(readings, events)
    print(next(stream))
    print(stream.send(3))
    print(list(stream))

    interrupted = summarize(readings, events)
    next(interrupted)
    interrupted.close()
    print(events)
