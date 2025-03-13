from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class TransactionStatus(Enum):
        CREATED = "created"
        BUYER_SET = "buyer_set"
        SELLER_SET = "seller_set"
        FUNDED = "funded"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        CANCELLED = "cancelled"
        REFUNDED = "refunded"

@dataclass
class Transaction:
        id: str
        user_id: int
        currency: str
        status: TransactionStatus
        created_at: datetime
        buyer_id: Optional[int] = None
        seller_id: Optional[int] = None
        buyer_address: Optional[str] = None
        seller_address: Optional[str] = None
        amount: Optional[float] = None
        funded_at: Optional[datetime] = None
@dataclass
class Review:
        transaction_id: str
        user_id: int
        message: str
        created_at: datetime
        rating: Optional[int] = None

@dataclass
class Report:
        user_id: int
        message: str
        created_at: datetime
        resolved: bool = False