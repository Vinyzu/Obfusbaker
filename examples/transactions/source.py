"""Reserve inventory with a context manager that can roll back a reservation."""


class InsufficientStock(Exception):
    pass


class Reservation:
    def __init__(self, stock, label, events):
        self.stock = stock
        self.label = label
        self.events = events

    def __enter__(self):
        self.snapshot = self.stock.copy()
        return self.stock

    def __exit__(self, error_type, error, traceback):
        if error_type is None:
            self.events.append(f"{self.label}: committed")
            return False
        self.stock.clear()
        self.stock.update(self.snapshot)
        self.events.append(f"{self.label}: rolled back")
        return isinstance(error, InsufficientStock)


def reserve(stock, item, amount):
    remaining = stock[item] - amount
    if remaining < 0:
        raise InsufficientStock(f"{item}: cannot reserve {amount}")
    stock[item] = remaining


if __name__ == "__main__":
    stock = {"cable": 8, "adapter": 3}
    events = []

    with Reservation(stock, "order A", events) as pending:
        reserve(pending, "cable", 2)

    with Reservation(stock, "order B", events) as pending:
        reserve(pending, "adapter", 1)
        reserve(pending, "cable", 12)

    print(sorted(stock.items()))
    print(events)
