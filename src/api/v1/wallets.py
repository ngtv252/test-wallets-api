import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.core.enums import OperationType, ErrorMessages
from src.core.exceptions import WalletNotFoundError, InsufficientFundsError
from src.wallet.services import WalletService
from src.wallet.schemas import WalletOperationRequest, WalletResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/wallets", tags=["wallets"])


async def get_wallet_service(db_session: AsyncSession = Depends(get_db_session)) -> WalletService:
    return WalletService(db_session)


@router.post(
    "/{wallet_uuid}/operation",
    response_model=WalletResponse,
    summary="Выполнить операцию с кошельком",
    description="Пополнение или снятие средств с кошелька"
)
async def perform_operation(
    wallet_uuid: uuid.UUID,
    operation: WalletOperationRequest,
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletResponse:
    """Выполнить операцию с кошельком."""
    try:
        match operation.operation_type:
            case OperationType.DEPOSIT:
                wallet = await wallet_service.deposit(wallet_uuid, operation.amount)
            case OperationType.WITHDRAW:
                wallet = await wallet_service.withdraw(wallet_uuid, operation.amount)

        return WalletResponse(
            wallet_uuid=wallet.id,
            balance=wallet.balance
        )
    
    except WalletNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorMessages.WALLET_NOT_FOUND
        )
    except InsufficientFundsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.INSUFFICIENT_FUNDS
        )
    except Exception as e:
        logger.error("Необработанная ошибка", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.INTERNAL_SERVER_ERROR
        )


@router.get(
    "/{wallet_uuid}",
    response_model=WalletResponse,
    summary="Получить баланс кошелька",
    description="Получить текущий баланс кошелька по UUID"
)
async def get_wallet_balance(
    wallet_uuid: uuid.UUID,
    wallet_service: WalletService = Depends(get_wallet_service)
) -> WalletResponse:
    """Получить баланс кошелька."""
    try:
        wallet = await wallet_service.get_wallet(wallet_uuid)
        
        return WalletResponse(
            wallet_uuid=wallet.id,
            balance=wallet.balance
        )
    
    except WalletNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorMessages.WALLET_NOT_FOUND
        )

    except Exception as e:
        logger.error("Ошибка при получении баланса кошелька", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.INTERNAL_SERVER_ERROR
        )