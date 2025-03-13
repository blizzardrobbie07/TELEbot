import re
import uuid

class CryptoMock:
    """Mock class for crypto-related operations."""

    @staticmethod
    def verify_address(currency, address):
        """Verify if an address format is valid for the given currency."""
        if currency == 'BTC':
            # Simple check for BTC address format
            return bool(re.match(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$', address))
        elif currency == 'LTC':
            # Simple check for LTC address format
            return bool(re.match(r'^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$', address))
        return False

    @staticmethod
    def get_fee(currency: str) -> float:
        """Get the transaction fee for the given currency."""
        if currency == 'BTC':
            return 0.00002256
        elif currency == 'LTC':
            return 0.0
        return 0.0

    @staticmethod
    def calculate_total(amount: float, currency: str) -> float:
        """Calculate the total amount including fees."""
        fee = CryptoMock.get_fee(currency)
        return amount + fee

    @staticmethod
    def generate_transaction_id():
        """Generate a mock transaction ID."""
        return str(uuid.uuid4())