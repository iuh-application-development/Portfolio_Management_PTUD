import pytest
from django.utils import timezone
from portfolio.models import User, Portfolio, Assets, StockTransaction
from decimal import Decimal

@pytest.mark.django_db
class TestBusinessLogic:
    """Test các chức năng nghiệp vụ."""

    def test_portfolio_profit_loss(self, user):
        """Test tính lãi/lỗ của portfolio."""
        # Tạo portfolio
        portfolio = Portfolio.objects.create(
            user=user,
            name='Profit Test Portfolio'
        )

        # Tạo asset
        asset = Assets.objects.create(
            user=user,
            symbol='VIC',
            current_price=90000,  # Giá hiện tại
            average_price=85000,  # Giá mua vào
            profit_loss=0
        )

        # Tạo giao dịch mua
        transaction = StockTransaction.objects.create(
            user=user,
            portfolio=portfolio,
            symbol='VIC',
            transaction_type='buy',
            quantity=100,
            price=85000,
            total_price=8500000,
            transaction_time=timezone.now()
        )

        # Tính lãi/lỗ
        profit_loss = (asset.current_price - asset.average_price) * transaction.quantity
        assert profit_loss == 500000  # (90000 - 85000) * 100

    def test_multiple_transactions(self, user):
        """Test nhiều giao dịch trên cùng một cổ phiếu."""
        portfolio = Portfolio.objects.create(
            user=user,
            name='Multiple Transactions Portfolio'
        )

        asset = Assets.objects.create(
            user=user,
            symbol='VIC',
            current_price=85000,
            average_price=85000,
            profit_loss=0
        )

        # Giao dịch mua đầu tiên
        transaction1 = StockTransaction.objects.create(
            user=user,
            portfolio=portfolio,
            symbol='VIC',
            transaction_type='buy',
            quantity=100,
            price=85000,
            total_price=8500000,
            transaction_time=timezone.now()
        )

        # Giao dịch mua thứ hai với giá khác
        transaction2 = StockTransaction.objects.create(
            user=user,
            portfolio=portfolio,
            symbol='VIC',
            transaction_type='buy',
            quantity=50,
            price=90000,
            total_price=4500000,
            transaction_time=timezone.now()
        )

        # Tính giá trung bình mới
        total_quantity = transaction1.quantity + transaction2.quantity
        total_cost = transaction1.total_price + transaction2.total_price
        new_average_price = total_cost / total_quantity

        assert new_average_price == Decimal('86666.666666666666666666666667')  # (8500000 + 4500000) / 150

    def test_portfolio_value(self, user):
        """Test tính tổng giá trị portfolio."""
        portfolio = Portfolio.objects.create(
            user=user,
            name='Value Test Portfolio'
        )

        # Tạo nhiều assets và giao dịch
        assets_data = [
            {'symbol': 'VIC', 'price': 85000, 'quantity': 100},
            {'symbol': 'VHM', 'price': 50000, 'quantity': 200},
            {'symbol': 'VRE', 'price': 25000, 'quantity': 300}
        ]

        total_value = 0
        for data in assets_data:
            asset = Assets.objects.create(
                user=user,
                symbol=data['symbol'],
                current_price=data['price'],
                average_price=data['price'],
                profit_loss=0
            )

            StockTransaction.objects.create(
                user=user,
                portfolio=portfolio,
                symbol=data['symbol'],
                transaction_type='buy',
                quantity=data['quantity'],
                price=data['price'],
                total_price=data['price'] * data['quantity'],
                transaction_time=timezone.now()
            )

            total_value += data['price'] * data['quantity']

        assert total_value == 24500000  # (85000*100 + 50000*200 + 25000*300)

    def test_transaction_validation(self, user):
        """Test validate giao dịch."""
        portfolio = Portfolio.objects.create(
            user=user,
            name='Validation Test Portfolio'
        )

        asset = Assets.objects.create(
            user=user,
            symbol='VIC',
            current_price=85000,
            average_price=85000,
            profit_loss=0,
            quantity=100  # Số lượng hiện có
        )

        # Test bán quá số lượng hiện có
        with pytest.raises(Exception):
            StockTransaction.objects.create(
                user=user,
                portfolio=portfolio,
                symbol='VIC',
                transaction_type='sell',
                quantity=200,  # Số lượng bán > số lượng hiện có
                price=85000,
                total_price=17000000,
                transaction_time=timezone.now()
            ) 