import enum


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class DebtDirection(str, enum.Enum):
    OWED_BY_ME = "owed_by_me"  # Долг — я должен
    OWED_TO_ME = "owed_to_me"  # Займ — мне должны


class DebtStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
