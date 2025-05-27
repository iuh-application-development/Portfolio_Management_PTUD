import pytest
from django.utils import timezone
from portfolio.models import User, Portfolio, Assets, StockTransaction

@pytest.mark.django_db
class TestBasicFunctionality:
    """Test các chức năng cơ bản."""

    def test_create_user(self):
        """Test tạo user mới."""
        user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )
        assert user.username == 'newuser'
        assert user.email == 'newuser@example.com'

    def test_create_portfolio(self, user):
        """Test tạo portfolio mới."""
        portfolio = Portfolio.objects.create(
            user=user,
            name='Test Portfolio',
            description='Test Description'
        )
        assert portfolio.name == 'Test Portfolio'
        assert portfolio.user == user

    def test_create_asset(self, user):
        """Test tạo asset mới."""
        asset = Assets.objects.create(
            user=user,
            symbol='VIC',
            current_price=85000,
            average_price=85000,
            profit_loss=0
        )
        assert asset.symbol == 'VIC'
        assert asset.current_price == 85000

    def test_create_transaction(self, user):
        """Test tạo giao dịch mới."""
        portfolio = Portfolio.objects.create(
            user=user,
            name='Transaction Test Portfolio'
        )

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

        assert transaction.symbol == 'VIC'
        assert transaction.quantity == 100
        assert transaction.total_price == 8500000 