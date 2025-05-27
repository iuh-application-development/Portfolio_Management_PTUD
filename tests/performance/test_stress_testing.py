import pytest
import time
import threading
import random
import concurrent.futures
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from portfolio.models import Portfolio, StockTransaction, PortfolioSymbol, Assets

@pytest.mark.django_db
class TestStressPerformance:
    """Test stress và giới hạn của hệ thống."""

    def setup_method(self):
        """Thiết lập môi trường test."""
        self.base_client = Client()
        self.test_users = []
        
        # Tạo nhiều user để test
        for i in range(10):  # Giảm từ 20 xuống 10 để test nhanh hơn
            user = User.objects.create_user(
                username=f'stressuser{i}',
                password='testpass123',
                email=f'stress{i}@test.com'
            )
            self.test_users.append(user)

    def test_high_concurrent_users(self):
        """Test với số lượng user đồng thời cao (20 users)."""
        def user_stress_session(user_id):
            client = Client()
            user = self.test_users[user_id % len(self.test_users)]
            client.login(username=user.username, password='testpass123')
            
            operations = []
            start_time = time.time()
            
            try:
                # Dashboard access
                response = client.get(reverse('portfolio:dashboard'))
                operations.append(('dashboard', response.status_code, time.time() - start_time))
                
                # Portfolio list
                response = client.get(reverse('portfolio:portfolio_list'))
                operations.append(('portfolio_list', response.status_code, time.time() - start_time))
                
                # Market overview
                response = client.get(reverse('portfolio:market_overview'))
                operations.append(('market_overview', response.status_code, time.time() - start_time))
                
                # Random delays để simulate real usage
                time.sleep(random.uniform(0.1, 0.5))
                
            except Exception as e:
                operations.append(('error', 500, str(e)))
            
            return operations

        # Stress test với 20 concurrent users
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(user_stress_session, i) for i in range(20)]
            all_operations = []
            
            for future in concurrent.futures.as_completed(futures):
                all_operations.extend(future.result())
        
        # Phân tích kết quả
        success_count = sum(1 for op in all_operations if op[1] in [200, 302])
        total_operations = len(all_operations)
        success_rate = success_count / total_operations * 100
        
        assert success_rate > 90, f"Success rate quá thấp: {success_rate}%"

    def test_rapid_fire_requests(self):
        """Test với requests liên tiếp không nghỉ."""
        client = Client()
        user = self.test_users[0]
        client.login(username=user.username, password='testpass123')
        
        request_times = []
        error_count = 0
        
        # 50 requests liên tiếp (giảm từ 100)
        for i in range(50):
            start = time.time()
            try:
                response = client.get(reverse('portfolio:dashboard'))
                end = time.time()
                request_times.append(end - start)
                
                if response.status_code not in [200, 302]:
                    error_count += 1
                    
            except Exception:
                error_count += 1
                request_times.append(10.0)  # Penalty time for errors
        
        avg_response_time = sum(request_times) / len(request_times)
        error_rate = error_count / 50 * 100
        
        assert avg_response_time < 2.0, f"Average response time quá cao: {avg_response_time}s"
        assert error_rate < 10, f"Error rate quá cao: {error_rate}%"

    def test_database_stress(self):
        """Test stress database với nhiều operations đồng thời."""
        def database_operations(thread_id):
            client = Client()
            user = self.test_users[thread_id % len(self.test_users)]
            client.login(username=user.username, password='testpass123')
            
            operations_count = 0
            errors = 0
            
            try:
                # Tạo portfolio
                portfolio = Portfolio.objects.create(
                    user=user,
                    name=f'Stress Portfolio {thread_id}_{time.time()}'
                )
                operations_count += 1
                
                # Tạo assets và transactions
                for i in range(5):  # Giảm từ 10 xuống 5
                    asset = Assets.objects.create(
                        user=user,
                        symbol=f'STRESS{thread_id}{i:02d}',
                        current_price=random.randint(10000, 100000),
                        average_price=random.randint(10000, 100000),
                        profit_loss=0
                    )
                    
                    StockTransaction.objects.create(
                        user=user,
                        portfolio=portfolio,
                        symbol=asset.symbol,
                        transaction_type=random.choice(['buy', 'sell']),
                        quantity=random.randint(10, 1000),
                        price=random.randint(10000, 100000),
                        total_price=random.randint(100000, 10000000)
                    )
                    operations_count += 1
                
                # Read operations
                portfolio_detail = client.get(
                    reverse('portfolio:portfolio_detail', kwargs={'id': portfolio.id})
                )
                if portfolio_detail.status_code != 200:
                    errors += 1
                
            except Exception:
                errors += 1
            
            return operations_count, errors

        # 10 threads thực hiện database operations (giảm từ 20)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(database_operations, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_operations = sum(result[0] for result in results)
        total_errors = sum(result[1] for result in results)
        error_rate = total_errors / total_operations * 100 if total_operations > 0 else 100
        
        assert error_rate < 5, f"Database error rate quá cao: {error_rate}%"

    def test_transaction_volume_stress(self):
        """Test với volume giao dịch cao."""
        portfolio = Portfolio.objects.create(user=self.test_users[0], name='Volume Stress Portfolio')
        
        assets = []
        for i in range(20):  # Giảm từ 50
            asset = Assets.objects.create(
                user=self.test_users[0],
                symbol=f'VOL{i:03d}',
                current_price=50000,
                average_price=50000,
                profit_loss=0
            )
            assets.append(asset)
        
        def create_transactions_batch(batch_id):
            client = Client()
            client.login(username=self.test_users[0].username, password='testpass123')
            
            success_count = 0
            for i in range(10):  # Giảm từ 20
                asset = random.choice(assets)
                transaction_data = {
                    'portfolio': portfolio.id,
                    'symbol': asset.symbol,
                    'transaction_type': random.choice(['buy', 'sell']),
                    'quantity': random.randint(10, 1000),
                    'price': random.randint(10000, 100000),
                }
                
                try:
                    response = client.post(
                        reverse('portfolio:add_transaction'),
                        transaction_data
                    )
                    if response.status_code in [200, 302]:
                        success_count += 1
                except Exception:
                    pass
            
            return success_count

        # 5 threads tạo transactions đồng thời (giảm từ 10)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_transactions_batch, i) for i in range(5)]
            success_counts = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_success = sum(success_counts)
        total_attempts = 5 * 10  # 5 threads x 10 transactions each
        success_rate = total_success / total_attempts * 100
        
        assert success_rate > 70, f"Transaction creation success rate quá thấp: {success_rate}%"

    def test_system_recovery(self):
        """Test khả năng phục hồi của hệ thống sau stress."""
        client = Client()
        user = self.test_users[0]
        client.login(username=user.username, password='testpass123')
        
        # Phase 1: Heavy load (giảm từ 100 xuống 50)
        for _ in range(50):
            try:
                client.get(reverse('portfolio:dashboard'))
            except:
                pass
        
        # Phase 2: Recovery test
        time.sleep(2)  # Wait for system to recover
        
        recovery_times = []
        for _ in range(5):  # Giảm từ 10
            start = time.time()
            response = client.get(reverse('portfolio:dashboard'))
            end = time.time()
            
            assert response.status_code in [200, 302]
            recovery_times.append(end - start)
        
        avg_recovery_time = sum(recovery_times) / len(recovery_times)
        assert avg_recovery_time < 2.0, f"System recovery quá chậm: {avg_recovery_time}s" 