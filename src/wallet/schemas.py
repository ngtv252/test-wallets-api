import uuid

from pydantic import BaseModel, Field, ConfigDict

from src.core.enums import OperationType


class WalletOperationRequest(BaseModel):
    operation_type: OperationType = Field(description="Тип операции")
    amount: int = Field(ge=1, description="Сумма операции")


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    wallet_uuid: uuid.UUID
    balance: int = Field(description="Текущий баланс")
