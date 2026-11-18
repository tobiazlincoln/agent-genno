import unittest

from budget import Budget


class TestBudget(unittest.TestCase):
    def test_balance(self):
        b = Budget()
        b.add_income(1000)
        b.add_expense(250)
        self.assertEqual(b.balance(), 750)

    def test_largest_expense_returns_the_largest(self):
        b = Budget()
        b.add_expense(10, "coffee")
        b.add_expense(200, "rent")
        b.add_expense(50, "food")
        self.assertEqual(b.largest_expense()["amount"], 200)

    def test_largest_expense_empty(self):
        self.assertIsNone(Budget().largest_expense())

    def test_apply_discount_reduces_expense(self):
        b = Budget()
        b.add_expense(100, "food")
        b.apply_discount(20)
        self.assertEqual(b.expenses_by_label()["food"], 80)

    def test_apply_discount_leaves_income_alone(self):
        b = Budget()
        b.add_income(500)
        b.apply_discount(50)
        self.assertEqual(b.balance(), 500)

    def test_summary(self):
        b = Budget()
        b.add_income(1000, "salary")
        b.add_expense(300, "rent")
        s = b.summary()
        self.assertEqual(s, {"income": 1000, "expense": 300, "balance": 700})


if __name__ == "__main__":
    unittest.main()
