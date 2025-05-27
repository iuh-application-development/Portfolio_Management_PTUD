import pytest
import time
import threading
import concurrent.futures
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from portfolio.models import Portfolio, StockTransaction, PortfolioSymbol, Assets

@pytest.mark.django_db
class TestLoadPerformance:
    """Test hiệu năng và tải của hệ thống."""

    def setup_method(self):
        """Thiết lập cho mỗi test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='loadtest_user',
            password='testpass123'
        )
        self.client.login(username='loadtest_user', password='testpass123')

    def test_concurrent_user_access(self):
        """Test nhiều user truy cập đồng thời."""
        def simulate_user_session():
            client = Client()
            user = User.objects.create_user(
                username=f'user_{threading.current_thread().ident}',
                password='testpass123'
            )
            client.login(username=user.username, password='testpass123')
            
            # Simulate user activities
            start_time = time.time()
            
            # Truy cập dashboard
            response = client.get(reverse('portfolio:dashboard'))
            assert response.status_code in [200, 302]
            
            # Xem danh sách portfolio
            response = client.get(reverse('portfolio:portfolio_list'))
            assert response.status_code == 200
            
            return time.time() - start_time

        # Test với 10 user đồng thời
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(simulate_user_session) for _ in range(10)]
            response_times = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Kiểm tra thời gian phản hồi trung bình < 5 giây
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 5.0, f"Thời gian phản hồi trung bình quá cao: {avg_response_time}s"

    def test_database_query_performance(self):
        """Test hiệu năng truy vấn database."""
        # Tạo test data
        portfolio = Portfolio.objects.create(user=self.user, name='Performance Test Portfolio')
        
        # Tạo nhiều assets và transactions
        assets = []
        for i in range(100):
            asset = Assets.objects.create(
                user=self.user,
                symbol=f'TEST{i:03d}',
                current_price=50000 + i * 100,
                average_price=50000 + i * 100,
                profit_loss=0
            )
            assets.append(asset)
            
            StockTransaction.objects.create(
                user=self.user,
                portfolio=portfolio,
                symbol=asset.symbol,
                transaction_type='buy',
                quantity=100,
                price=50000 + i * 100,
                total_price=(50000 + i * 100) * 100
            )
        
        # Test thời gian load portfolio detail
        start_time = time.time()
        response = self.client.get(
            reverse('portfolio:portfolio_detail', kwargs={'id': portfolio.id})
        )
        load_time = time.time() - start_time
        
        assert response.status_code == 200
        assert load_time < 2.0, f"Thời gian load portfolio quá chậm: {load_time}s"

    def test_api_response_time(self):
        """Test thời gian phản hồi API."""
        endpoints = [
            'portfolio:dashboard',
            'portfolio:portfolio_list',
            'portfolio:market_overview',
            'portfolio:transaction_history'
        ]
        
        response_times = {}
        
        for endpoint in endpoints:
            start_time = time.time()
            response = self.client.get(reverse(endpoint))
            end_time = time.time()
            
            response_times[endpoint] = end_time - start_time
            assert response.status_code == 200
            assert response_times[endpoint] < 3.0, f"API {endpoint} phản hồi chậm: {response_times[endpoint]}s"

    def test_memory_usage_under_load(self):
        """Test sử dụng memory dưới tải cao."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Tạo nhiều request liên tiếp
        for i in range(50):
            response = self.client.get(reverse('portfolio:dashboard'))
            assert response.status_code in [200, 302]
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Kiểm tra không có memory leak nghiêm trọng (tăng < 50MB)
        assert memory_increase < 50, f"Memory tăng quá nhiều: {memory_increase}MB"

    def test_transaction_processing_speed(self):
        """Test tốc độ xử lý giao dịch."""
        portfolio = Portfolio.objects.create(user=self.user, name='Speed Test Portfolio')
        
        asset = Assets.objects.create(
            user=self.user,
            symbol='SPEEDTEST',
            current_price=50000,
            average_price=50000,
            profit_loss=0
        )
        
        start_time = time.time()
        
        # Tạo 50 giao dịch
        for i in range(50):
            transaction_data = {
                'portfolio': portfolio.id,
                'symbol': asset.symbol,
                'transaction_type': 'buy',
                'quantity': 100,
                'price': 50000 + i * 100,
            }
            
            response = self.client.post(
                reverse('portfolio:add_transaction'),
                transaction_data
            )
            # Chấp nhận cả redirect và success response
            assert response.status_code in [200, 302]
        
        total_time = time.time() - start_time
        avg_time_per_transaction = total_time / 50
        
        assert avg_time_per_transaction < 0.5, f"Xử lý giao dịch quá chậm: {avg_time_per_transaction}s/transaction"

    def test_search_performance(self):
        """Test hiệu năng tìm kiếm."""
        # Tạo nhiều assets để test search
        for i in range(200):
            Assets.objects.create(
                user=self.user,
                symbol=f'SEARCH{i:03d}',
                current_price=50000,
                average_price=50000,
                profit_loss=0
            )
        
        search_queries = ['SEARCH', 'TEST', 'VIC', 'ABC']
        
        for query in search_queries:
            start_time = time.time()
            response = self.client.get(
                reverse('portfolio:stock_search'),
                {'q': query}
            )
            search_time = time.time() - start_time
            
            assert response.status_code == 200
            assert search_time < 1.0, f"Tìm kiếm '{query}' quá chậm: {search_time}s"

    def test_concurrent_portfolio_operations(self):
        """Test các thao tác portfolio đồng thời."""
        def portfolio_operations():
            portfolio = Portfolio.objects.create(
                user=self.user,
                name=f'Concurrent Test {threading.current_thread().ident}'
            )
            
            # Thực hiện các thao tác
            client = Client()
            client.login(username='loadtest_user', password='testpass123')
            
            start_time = time.time()
            
            # View portfolio
            response = client.get(
                reverse('portfolio:portfolio_detail', kwargs={'id': portfolio.id})
            )
            assert response.status_code == 200
            
            # Update portfolio
            update_data = {
                'name': f'Updated {portfolio.name}',
                'description': 'Updated description'
            }
            response = client.post(
                reverse('portfolio:update_portfolio', kwargs={'id': portfolio.id}),
                update_data
            )
            assert response.status_code in [200, 302]
            
            return time.time() - start_time

        # Test với 5 portfolio operations đồng thời
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(portfolio_operations) for _ in range(5)]
            times = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        avg_time = sum(times) / len(times)
        assert avg_time < 3.0, f"Portfolio operations quá chậm: {avg_time}s"

    def test_large_dataset_handling(self):
        """Test xử lý dataset lớn."""
        portfolio = Portfolio.objects.create(user=self.user, name='Large Dataset Test')
        
        # Tạo 500 transactions
        asset = Assets.objects.create(
            user=self.user,
            symbol='LARGE',
            current_price=50000,
            average_price=50000,
            profit_loss=0
        )
        
        start_time = time.time()
        
        transactions = []
        for i in range(500):
            transactions.append(StockTransaction(
                user=self.user,
                portfolio=portfolio,
                symbol=asset.symbol,
                transaction_type='buy' if i % 2 == 0 else 'sell',
                quantity=100,
                price=50000 + i * 10,
                total_price=(50000 + i * 10) * 100
            ))
        
        StockTransaction.objects.bulk_create(transactions)
        
        creation_time = time.time() - start_time
        assert creation_time < 5.0, f"Tạo large dataset quá chậm: {creation_time}s"
        
        # Test load large dataset
        start_time = time.time()
        response = self.client.get(
            reverse('portfolio:portfolio_detail', kwargs={'id': portfolio.id})
        )
        load_time = time.time() - start_time
        
        assert response.status_code == 200
        assert load_time < 3.0, f"Load large dataset quá chậm: {load_time}s"

    def test_stress_test_endpoints(self):
        """Test stress cho các endpoints quan trọng."""
        endpoints = [
            'portfolio:dashboard',
            'portfolio:portfolio_list',
            'portfolio:market_overview'
        ]
        
        def stress_endpoint(endpoint):
            times = []
            for _ in range(20):
                start = time.time()
                response = self.client.get(reverse(endpoint))
                end = time.time()
                
                assert response.status_code in [200, 302]
                times.append(end - start)
            
            return max(times), sum(times) / len(times)
        
        for endpoint in endpoints:
            max_time, avg_time = stress_endpoint(endpoint)
            assert max_time < 5.0, f"Endpoint {endpoint} có response time cao nhất: {max_time}s"
            assert avg_time < 2.0, f"Endpoint {endpoint} có response time trung bình cao: {avg_time}s"

    def test_vnstock_api_performance(self):
        """Test hiệu năng VnStock API calls."""
        from unittest.mock import patch
        
        with patch('portfolio.vnstock_services.stock') as mock_stock:
            # Mock quick response
            mock_stock.quote.history.return_value.iloc = [{'close': 85000}]
            
            start_time = time.time()
            
            # Test multiple API calls
            for _ in range(10):
                response = self.client.get(
                    reverse('portfolio:stock_search'),
                    {'q': 'VIC'}
                )
                assert response.status_code == 200
            
            total_time = time.time() - start_time
            avg_time = total_time / 10
            
            assert avg_time < 1.0, f"VnStock API calls quá chậm: {avg_time}s per call" 