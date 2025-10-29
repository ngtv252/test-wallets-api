import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import WalletNotFoundError, InsufficientFundsError
from src.wallet.models import Wallet

logger = structlog.get_logger()


class WalletService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def get_wallet(self, wallet_uuid: uuid.UUID) -> Wallet:
        """Получить кошелек по UUID."""
        logger.info("Получение кошелька", wallet_uuid=str(wallet_uuid))
        
        result = await self.db_session.execute(
            select(Wallet).where(Wallet.id == wallet_uuid)
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            logger.warning("Кошелек не найден", wallet_uuid=str(wallet_uuid))
            raise WalletNotFoundError(f"Кошелек {wallet_uuid} не найден")
        
        logger.info("Кошелек найден", wallet_uuid=str(wallet_uuid), balance=wallet.balance)
        return wallet
    
    async def deposit(self, wallet_uuid: uuid.UUID, amount: int) -> Wallet:
        """Пополнить кошелек."""
        logger.info("Пополнение кошелька", wallet_uuid=str(wallet_uuid), amount=amount)
        
        wallet = await self._get_wallet_with_lock(wallet_uuid)
        old_balance = wallet.balance
        
        wallet.balance += amount
        
        await self.db_session.commit()
        await self.db_session.refresh(wallet)
        
        logger.info(
            "Пополнение завершено",
            wallet_uuid=str(wallet_uuid),
            amount=amount,
            old_balance=old_balance,
            new_balance=wallet.balance
        )
        
        return wallet
    
    async def withdraw(self, wallet_uuid: uuid.UUID, amount: int) -> Wallet:
        """Снять с кошелька."""
        logger.info("Снятие с кошелька", wallet_uuid=str(wallet_uuid), amount=amount)
        
        wallet = await self._get_wallet_with_lock(wallet_uuid)
        old_balance = wallet.balance
        
        if wallet.balance < amount:
            logger.error(
                "Недостаточно средств",
                wallet_uuid=str(wallet_uuid),
                requested_amount=amount,
                current_balance=wallet.balance
            )
            raise InsufficientFundsError()
        
        wallet.balance -= amount
        
        await self.db_session.commit()
        await self.db_session.refresh(wallet)
        
        logger.info(
            "Снятие завершено",
            wallet_uuid=str(wallet_uuid),
            amount=amount,
            old_balance=old_balance,
            new_balance=wallet.balance
        )
        
        return wallet
    
    async def _get_wallet_with_lock(self, wallet_uuid: uuid.UUID) -> Wallet:
        """Получить кошелек с блокировкой."""
        result = await self.db_session.execute(
            select(Wallet).where(Wallet.id == wallet_uuid).with_for_update()
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            logger.error("Кошелек не найден", wallet_uuid=str(wallet_uuid))
            raise WalletNotFoundError(f"Кошелек {wallet_uuid} не найден")
        
        return wallet
