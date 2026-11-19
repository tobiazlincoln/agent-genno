"""Simple budget tracker used for the GLM agent experiment."""


class Budget:
    def __init__(self):
        self.transactions = []

    def add_income(self, amount, label="income"):
        if amount < 0:
            raise ValueError("amount must be non-negative")
        self.transactions.append({"type": "income", "amount": amount, "label": label})

    def add_expense(self, amount, label="expense"):
        if amount < 0:
            raise ValueError("amount must be non-negative")
        self.transactions.append({"type": "expense", "amount": amount, "label": label})

    def balance(self):
        total = 0
        for t in self.transactions:
            if t["type"] == "income":
                total += t["amount"]
            else:
                total -= t["amount"]
        return total

    def expenses_by_label(self):
        result = {}
        for t in self.transactions:
            if t["type"] == "expense":
                result[t["label"]] = result.get(t["label"], 0) + t["amount"]
        return result

    def largest_expense(self):
        expenses = [t for t in self.transactions if t["type"] == "expense"]
        if not expenses:
            return None
        return max(expenses, key=lambda t: t["amount"])

    def apply_discount(self, pct):
        """Reduce every expense by pct percent."""
        if not 0 <= pct <= 100:
            raise ValueError("pct must be between 0 and 100")
        for t in self.transactions:
            if t["type"] == "expense":
                t["amount"] = t["amount"] * (100 - pct) / 100

    def summary(self):
        total_income = sum(t["amount"] for t in self.transactions if t["type"] == "income")
        total_expense = sum(t["amount"] for t in self.transactions if t["type"] == "expense")
        return {
            "income": total_income,
            "expense": total_expense,
            "balance": total_income - total_expense,
        }
