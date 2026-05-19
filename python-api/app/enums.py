import enum


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
