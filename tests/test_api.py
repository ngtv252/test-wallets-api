import uuid
import pytest
import asyncio
from httpx import AsyncClient

from src.core.enums import OperationType, ErrorMessages
from src.wallet.models import Wallet
from tests.conftest import BACKEND, DatabaseBackend


class TestWalletAPI:
    """Тесты API кошельков."""
    
    @pytest.mark.asyncio
    async def test_deposit_success(self, client: AsyncClient, wallet: Wallet):
        """Тест успешного пополнения."""
        response = await client.post(
            f"/api/v1/wallets/{wallet.id}/operation",
            json={
                "operation_type": OperationType.DEPOSIT,
                "amount": 500
            }
        )
        assert response.status_code == 200
        assert response.json() == {
            "wallet_uuid": str(wallet.id),
            "balance": 1500
        }

    @pytest.mark.asyncio
    async def test_deposit_invalid_wallet(self, client: AsyncClient):
        """Тест пополнения несуществующего кошелька."""
        fake_uuid = uuid.uuid4()
        response = await client.post(
            f"/api/v1/wallets/{fake_uuid}/operation",
            json={
                "operation_type": OperationType.DEPOSIT,
                "amount": 500
            }
        )

        assert response.status_code == 404
        assert response.json()["detail"] == ErrorMessages.WALLET_NOT_FOUND

    @pytest.mark.asyncio
    async def test_withdraw_success(self, client: AsyncClient, wallet: Wallet):
        """Тест успешного снятия."""
        response = await client.post(
            f"/api/v1/wallets/{wallet.id}/operation",
            json={
                "operation_type": OperationType.WITHDRAW,
                "amount": 300
            }
        )
        
        assert response.status_code == 200
        assert response.json() == {
            "wallet_uuid": str(wallet.id),
            "balance": 700
        }

    @pytest.mark.asyncio
    async def test_withdraw_insufficient_funds(self, client: AsyncClient, wallet: Wallet):
        """Тест снятия при недостатке средств."""
        response = await client.post(
            f"/api/v1/wallets/{wallet.id}/operation",
            json={
                "operation_type": OperationType.WITHDRAW,
                "amount": 1500
            }
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == ErrorMessages.INSUFFICIENT_FUNDS

    @pytest.mark.asyncio
    async def test_withdraw_invalid_wallet(self, client: AsyncClient):
        """Тест снятия с несуществующего кошелька."""
        fake_uuid = uuid.uuid4()
        response = await client.post(
            f"/api/v1/wallets/{fake_uuid}/operation",
            json={
                "operation_type": OperationType.WITHDRAW,
                "amount": 100
            }
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == ErrorMessages.WALLET_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_wallet_balance_success(self, client: AsyncClient, wallet: Wallet):
        """Тест получения баланса."""
        response = await client.get(f"/api/v1/wallets/{wallet.id}")
        
        assert response.status_code == 200
        assert response.json() == {
            "wallet_uuid": str(wallet.id),
            "balance": 1000
        }

    @pytest.mark.asyncio
    async def test_get_wallet_balance_not_found(self, client: AsyncClient):
        """Тест получения баланса несуществующего кошелька."""
        fake_uuid = uuid.uuid4()
        response = await client.get(f"/api/v1/wallets/{fake_uuid}")
        
        assert response.status_code == 404
        assert response.json()["detail"] == ErrorMessages.WALLET_NOT_FOUND

    @pytest.mark.asyncio
    async def test_invalid_operation_type(self, client: AsyncClient, wallet: Wallet):
        """Тест неверного типа операции."""
        response = await client.post(
            f"/api/v1/wallets/{wallet.id}/operation",
            json={
                "operation_type": "INVALID",
                "amount": 100
            }
        )
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_invalid_amount(self, client: AsyncClient, wallet: Wallet):
        """Тест неверной суммы."""
        response = await client.post(
            f"/api/v1/wallets/{wallet.id}/operation",
            json={  
                "operation_type": OperationType.DEPOSIT,
                "amount": -100
            }
        )
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_zero_amount(self, client: AsyncClient, wallet: Wallet):
        """Тест нулевой суммы."""
        response = await client.post(
            f"/api/v1/wallets/{wallet.id}/operation",
            json={
                "operation_type": OperationType.DEPOSIT,
                "amount": 0
            }
        )
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_withdraw_equals_balance(self, client: AsyncClient, wallet: Wallet):
        """Снятие всей суммы: баланс должен стать 0."""
        response = await client.post(
            f"/api/v1/wallets/{wallet.id}/operation",
            json={
                "operation_type": OperationType.WITHDRAW,
                "amount": 1000
            }
        )
        assert response.status_code == 200
        assert response.json() == {
            "wallet_uuid": str(wallet.id),
            "balance": 0
        }

    @pytest.mark.asyncio
    async def test_invalid_uuid_in_path_get(self, client: AsyncClient):
        """Некорректный UUID в path должен дать 422."""
        response = await client.get("/api/v1/wallets/not-a-uuid")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_uuid_in_path_post(self, client: AsyncClient):
        """Некорректный UUID в path для операции должен дать 422."""
        response = await client.post(
            "/api/v1/wallets/not-a-uuid/operation",
            json={
                "operation_type": OperationType.DEPOSIT,
                "amount": 100
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_operation_type(self, client: AsyncClient, wallet: Wallet):
        """Отсутствует поле operation_type: 422."""
        response = await client.post(
            f"/api/v1/wallets/{wallet.id}/operation",
            json={
                "amount": 100
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_amount(self, client: AsyncClient, wallet: Wallet):
        """Отсутствует поле amount: 422."""
        response = await client.post(
            f"/api/v1/wallets/{wallet.id}/operation",
            json={
                "operation_type": OperationType.DEPOSIT
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_amount_as_string_is_accepted(self, client: AsyncClient, wallet: Wallet):
        """Строковое число для amount по умолчанию парсится Pydantic: 200."""
        response = await client.post(
            f"/api/v1/wallets/{wallet.id}/operation",
            json={
                "operation_type": OperationType.DEPOSIT,
                "amount": "100"
            }
        )
        assert response.status_code == 200


@pytest.mark.skipif(
    BACKEND is DatabaseBackend.SQLITE,
    reason="Concurrency tests require PostgreSQL row-level locks",
)
class TestWalletConcurrency:
    """Тесты конкурентности и потокобезопасности."""

    @pytest.mark.asyncio
    async def test_concurrent_deposits(self, client: AsyncClient, empty_wallet: Wallet):
        """Тест конкурентных пополнений."""
        async def deposit():
            response = await client.post(
                f"/api/v1/wallets/{empty_wallet.id}/operation",
                json={
                    "operation_type": OperationType.DEPOSIT,
                    "amount": 100
                }
            )
            return response.status_code == 200
        
        # Запускаем 10 конкурентных пополнений
        results = await asyncio.gather(*[deposit() for _ in range(10)])
        
        # Все операции должны быть успешными
        assert all(results)
        
        # Проверяем финальный баланс
        response = await client.get(f"/api/v1/wallets/{empty_wallet.id}")
        assert response.status_code == 200
        assert response.json()["balance"] == 1000  # 0 + 10*100

    @pytest.mark.asyncio
    async def test_concurrent_withdraws(self, client: AsyncClient, wallet: Wallet):
        """Тест конкурентных снятий."""
        async def withdraw():
            response = await client.post(
                f"/api/v1/wallets/{wallet.id}/operation",
                json={
                    "operation_type": OperationType.WITHDRAW,
                    "amount": 50
                }
            )
            return response.status_code == 200
        
        # Запускаем 10 конкурентных снятий
        results = await asyncio.gather(*[withdraw() for _ in range(10)])
        
        # Все операции должны быть успешными
        assert all(results)
        
        # Проверяем финальный баланс
        response = await client.get(f"/api/v1/wallets/{wallet.id}")
        assert response.status_code == 200
        assert response.json()["balance"] == 500  # 1000 - 10*50

    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self, client: AsyncClient, wallet: Wallet):
        """Тест смешанных конкурентных операций."""
        async def deposit():
            response = await client.post(
                f"/api/v1/wallets/{wallet.id}/operation",
                json={
                    "operation_type": OperationType.DEPOSIT,
                    "amount": 200
                }
            )
            return response.status_code == 200
        
        async def withdraw():
            response = await client.post(
                f"/api/v1/wallets/{wallet.id}/operation",
                json={
                    "operation_type": OperationType.WITHDRAW,
                    "amount": 100
                }
            )
            return response.status_code == 200
        
        # Запускаем смешанные операции
        deposit_tasks = [deposit() for _ in range(5)]
        withdraw_tasks = [withdraw() for _ in range(5)]
        
        deposit_results = await asyncio.gather(*deposit_tasks)
        withdraw_results = await asyncio.gather(*withdraw_tasks)
        
        # Все операции должны быть успешными
        assert all(deposit_results)
        assert all(withdraw_results)
        
        # Проверяем финальный баланс
        response = await client.get(f"/api/v1/wallets/{wallet.id}")
        assert response.status_code == 200
        assert response.json()["balance"] == 1500  # 1000 + 5*200 - 5*100

    @pytest.mark.asyncio
    async def test_high_concurrency(self, client: AsyncClient, empty_wallet: Wallet):
        """Тест высокой конкурентности."""
        total_operations = 100
        concurrency_limit = 20
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def operation():
            async with semaphore:
                response = await client.post(
                    f"/api/v1/wallets/{empty_wallet.id}/operation",
                    json={
                        "operation_type": OperationType.DEPOSIT,
                        "amount": 1
                    }
                )
                return response.status_code == 200

        results = await asyncio.gather(*(operation() for _ in range(total_operations)))
        assert all(results)

        response = await client.get(f"/api/v1/wallets/{empty_wallet.id}")
        assert response.status_code == 200
        assert response.json()["balance"] == total_operations  # 0 + 100*1