from enum import StrEnum


class OperationType(StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class ErrorMessages(StrEnum):
    WALLET_NOT_FOUND = "Wallet not found"
    INSUFFICIENT_FUNDS = "Insufficient funds"
    INTERNAL_SERVER_ERROR = "Internal server error"
    INVALID_REQUEST_DATA = "Invalid request data"
