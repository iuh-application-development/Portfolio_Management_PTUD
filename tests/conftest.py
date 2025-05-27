import os
import sys
import django
import pytest

# Thêm src vào Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Cấu hình Django settings TRƯỚC khi import bất kỳ Django model nào
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Cấu hình Django
django.setup()

# BÂY GIỜ mới import các Django components
from django.test import Client
from portfolio.models import User  # Sử dụng custom User model
from django.conf import settings

@pytest.fixture(scope='session')
def django_db_setup():
    """Thiết lập database cho test session."""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }

@pytest.fixture
def client():
    """Tạo Django test client."""
    return Client()

@pytest.fixture
def user():
    """Tạo user test."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def authenticated_client(client, user):
    """Tạo client đã đăng nhập."""
    client.login(username='testuser', password='testpass123')
    return client

@pytest.fixture
def sample_stock_data():
    """Dữ liệu cổ phiếu mẫu cho test."""
    return {
        'symbol': 'VIC',
        'price': 85000,
        'change': 1000,
        'percent_change': 1.18,
        'volume': 1234567,
        'market_cap': 400000000000
    }

@pytest.fixture
def sample_portfolio_data():
    """Dữ liệu portfolio mẫu cho test."""
    return {
        'name': 'Test Portfolio',
        'description': 'Portfolio dùng để test',
        'initial_cash': 1000000000
    } 