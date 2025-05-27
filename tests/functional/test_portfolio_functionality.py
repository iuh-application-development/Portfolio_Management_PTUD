import pytest
import json
from django.urls import reverse
from django.contrib.auth.models import User
from portfolio.models import Portfolio, StockTransaction, PortfolioSymbol, Assets

@pytest.mark.django_db
class TestPortfolioFunctionality:
    """Test các chức năng chính của Portfolio Management."""

    def test_user_registration(self, client):
        """Test đăng ký user mới."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        response = client.post(reverse('portfolio:register'), data)
        assert response.status_code in [200, 302]
        assert User.objects.filter(username='newuser').exists()

    def test_user_login(self, client, user):
        """Test đăng nhập user."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = client.post(reverse('portfolio:login'), data)
        assert response.status_code in [200, 302]

    def test_create_portfolio(self, authenticated_client, user, sample_portfolio_data):
        """Test tạo portfolio mới."""
        response = authenticated_client.post(
            reverse('portfolio:create_portfolio'), 
            sample_portfolio_data
        )
        assert response.status_code in [200, 302]
        assert Portfolio.objects.filter(name=sample_portfolio_data['name']).exists()

    def test_view_portfolio_list(self, authenticated_client, user):
        """Test xem danh sách portfolio."""
        response = authenticated_client.get(reverse('portfolio:portfolio_list'))
        assert response.status_code == 200
        assert 'portfolios' in response.context or b'portfolio' in response.content.lower()

    def test_portfolio_detail_view(self, authenticated_client, user, sample_portfolio_data):
        """Test xem chi tiết portfolio."""
        # Tạo portfolio trước
        portfolio = Portfolio.objects.create(
            user=user,
            name=sample_portfolio_data['name'],
            description=sample_portfolio_data['description']
        )
        
        response = authenticated_client.get(
            reverse('portfolio:portfolio_detail', kwargs={'id': portfolio.id})
        )
        assert response.status_code == 200

    def test_add_stock_to_portfolio(self, authenticated_client, user, sample_stock_data):
        """Test thêm cổ phiếu vào portfolio."""
        # Tạo portfolio
        portfolio = Portfolio.objects.create(user=user, name='Test Portfolio')
        
        # Tạo asset nếu chưa có
        asset, created = Assets.objects.get_or_create(
            symbol=sample_stock_data['symbol'],
            defaults={
                'user': user,
                'current_price': sample_stock_data['price'],
                'average_price': sample_stock_data['price'],
                'profit_loss': 0
            }
        )
        
        transaction_data = {
            'portfolio': portfolio.id,
            'symbol': asset.symbol,
            'transaction_type': 'buy',
            'quantity': 100,
            'price': sample_stock_data['price'],
        }
        
        response = authenticated_client.post(
            reverse('portfolio:add_transaction'), 
            transaction_data
        )
        assert response.status_code in [200, 302]

    def test_stock_search(self, authenticated_client):
        """Test tìm kiếm cổ phiếu."""
        response = authenticated_client.get(
            reverse('portfolio:stock_search'), 
            {'q': 'VIC'}
        )
        assert response.status_code == 200

    def test_portfolio_performance_calculation(self, authenticated_client, user):
        """Test tính toán hiệu suất portfolio."""
        # Tạo portfolio với transaction
        portfolio = Portfolio.objects.create(user=user, name='Performance Test')
        
        # Tạo stock transaction
        StockTransaction.objects.create(
            user=user,
            portfolio=portfolio,
            symbol='TEST',
            transaction_type='buy',
            quantity=100,
            price=50000,
            total_price=5000000
        )
        
        response = authenticated_client.get(
            reverse('portfolio:portfolio_detail', kwargs={'id': portfolio.id})
        )
        assert response.status_code == 200

    def test_portfolio_delete(self, authenticated_client, user):
        """Test xóa portfolio."""
        portfolio = Portfolio.objects.create(user=user, name='To Delete')
        
        response = authenticated_client.post(
            reverse('portfolio:delete_portfolio', kwargs={'id': portfolio.id})
        )
        assert response.status_code in [200, 302]

    def test_transaction_history(self, authenticated_client, user):
        """Test xem lịch sử giao dịch."""
        response = authenticated_client.get(reverse('portfolio:transaction_history'))
        assert response.status_code == 200

    def test_market_data_access(self, authenticated_client):
        """Test truy cập dữ liệu thị trường."""
        response = authenticated_client.get(reverse('portfolio:market_overview'))
        assert response.status_code == 200

    def test_user_dashboard(self, authenticated_client):
        """Test trang dashboard của user."""
        response = authenticated_client.get(reverse('portfolio:dashboard'))
        assert response.status_code == 200

    def test_unauthorized_access(self, client):
        """Test truy cập khi chưa đăng nhập."""
        response = client.get(reverse('portfolio:dashboard'))
        assert response.status_code in [302, 403]  # Redirect to login hoặc forbidden

    def test_portfolio_update(self, authenticated_client, user):
        """Test cập nhật thông tin portfolio."""
        portfolio = Portfolio.objects.create(user=user, name='Original Name')
        
        update_data = {
            'name': 'Updated Name',
            'description': 'Updated description'
        }
        
        response = authenticated_client.post(
            reverse('portfolio:update_portfolio', kwargs={'id': portfolio.id}),
            update_data
        )
        assert response.status_code in [200, 302]

    def test_stock_price_update(self, authenticated_client, user, sample_stock_data):
        """Test cập nhật giá cổ phiếu."""
        asset = Assets.objects.create(
            user=user,
            symbol=sample_stock_data['symbol'],
            current_price=sample_stock_data['price'],
            average_price=sample_stock_data['price'],
            profit_loss=0
        )
        
        response = authenticated_client.get(
            reverse('portfolio:update_stock_price', kwargs={'symbol': asset.symbol})
        )
        assert response.status_code in [200, 302] 