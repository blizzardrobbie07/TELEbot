from models import Transaction, Review, Report, TransactionStatus
import uuid
from datetime import datetime

class Storage:
    """In-memory storage with transaction management."""

    def __init__(self):
        self.transactions = {}
        self.reviews = []
        self.reports = []

    def create_transaction(self, user_id, currency):
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            currency=currency,
            status=TransactionStatus.CREATED,
            created_at=datetime.now()
        )
        self.transactions[user_id] = transaction
        return transaction

    def get_user_transaction(self, user_id):
        return self.transactions.get(user_id)

    def mark_as_funded(self, user_id):
        transaction = self.transactions.get(user_id)
        if transaction:
            transaction.status = TransactionStatus.FUNDED

    def add_review(self, review):
        self.reviews.append(review)

    def add_report(self, report):
        self.reports.append(report)

    def reset_transaction(self, user_id):
        if user_id in self.transactions:
            del self.transactions[user_id]

storage = Storage()