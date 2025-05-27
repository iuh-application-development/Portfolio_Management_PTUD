# 🧪 Portfolio Management - Test Suite

Bộ test toàn diện cho hệ thống Portfolio Management System.

## 📁 Cấu trúc Test

```
tests/
├── conftest.py                     # Cấu hình chung cho pytest
├── pytest.ini                     # Cấu hình pytest
├── requirements_test.txt           # Dependencies cho testing
├── run_tests.py                   # Script chạy test
├── README.md                      # Hướng dẫn này
├── functional/                    # Tests chức năng
│   ├── test_portfolio_functionality.py
│   └── test_vnstock_integration.py
└── performance/                   # Tests hiệu năng
    ├── test_load_testing.py
    └── test_stress_testing.py
```

## 🚀 Cài đặt và Thiết lập

### 1. Cài đặt Dependencies

```bash
# Từ thư mục gốc dự án
cd Portfolio_Management_PTUD

# Kích hoạt virtual environment
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows

# Cài đặt test dependencies
pip install -r tests/requirements_test.txt
```

### 2. Thiết lập môi trường test

```bash
python tests/run_tests.py setup
```

## 🧪 Chạy Tests

### Script chính (Khuyến nghị)

```bash
# Chạy tất cả tests
python tests/run_tests.py all

# Chạy functional tests
python tests/run_tests.py functional

# Chạy performance tests  
python tests/run_tests.py performance

# Chạy quick tests (loại trừ performance)
python tests/run_tests.py quick

# Chạy stress tests
python tests/run_tests.py stress

# Chạy load tests
python tests/run_tests.py load

# Tạo coverage report
python tests/run_tests.py coverage

# Dọn dẹp test artifacts
python tests/run_tests.py clean
```

### Pytest trực tiếp

```bash
# Chạy tất cả tests với coverage
pytest tests/ --cov=src/portfolio --cov-report=html

# Chỉ functional tests
pytest tests/functional/ -v

# Chỉ performance tests
pytest tests/performance/ -v -s

# Chạy test cụ thể
pytest tests/functional/test_portfolio_functionality.py::TestPortfolioFunctionality::test_create_portfolio -v

# Chạy với markers
pytest -m "not performance" -v  # Loại trừ performance tests
pytest -m "functional" -v       # Chỉ functional tests
```

## 📊 Coverage Report

Sau khi chạy tests với coverage:

```bash
# HTML report sẽ được tạo tại
open tests/coverage_html/index.html
```

## 📝 Loại Tests

### 1. Functional Tests (`tests/functional/`)

**test_portfolio_functionality.py:**
- ✅ Đăng ký và đăng nhập user
- ✅ Tạo, xem, cập nhật, xóa portfolio
- ✅ Thêm cổ phiếu vào portfolio
- ✅ Xem lịch sử giao dịch
- ✅ Tính toán hiệu suất portfolio
- ✅ Tìm kiếm cổ phiếu
- ✅ Kiểm tra authorization

**test_vnstock_integration.py:**
- ✅ Tích hợp VnStock API
- ✅ Lấy giá cổ phiếu real-time
- ✅ Tìm kiếm cổ phiếu
- ✅ Xử lý lỗi API
- ✅ Validate dữ liệu
- ✅ Cache performance

### 2. Performance Tests (`tests/performance/`)

**test_load_testing.py:**
- ⚡ Concurrent user access (10 users)
- ⚡ Database query performance
- ⚡ API response time
- ⚡ Memory usage under load
- ⚡ Transaction processing speed
- ⚡ Search performance
- ⚡ Large dataset handling

**test_stress_testing.py:**
- 💪 High concurrent users (50+ users)
- 💪 Rapid fire requests
- 💪 Database stress testing
- 💪 Memory stress testing
- 💪 API endpoint limits
- 💪 Transaction volume stress
- 💪 System recovery testing

## 🎯 Test Criteria

### Functional Tests
- ✅ Tất cả chức năng hoạt động đúng
- ✅ Error handling phù hợp
- ✅ Data validation chính xác
- ✅ Authorization security

### Performance Tests
- ⚡ Response time < 2 giây cho most operations
- ⚡ Concurrent users: 10+ users đồng thời
- ⚡ Memory usage ổn định (không memory leak)
- ⚡ Database queries optimized

### Stress Tests
- 💪 Success rate > 95% under high load
- 💪 System recovery < 1 giây after stress
- 💪 Error rate < 5% under normal load
- 💪 Memory increase < 200MB under stress

## 🔧 Customization

### Thêm Test Mới

1. Tạo file test trong thư mục phù hợp:
```python
# tests/functional/test_new_feature.py
import pytest
from django.test import Client

@pytest.mark.django_db
class TestNewFeature:
    def test_new_functionality(self, authenticated_client):
        # Your test here
        pass
```

2. Update markers nếu cần trong `pytest.ini`

### Thay đổi Performance Thresholds

Trong files test, thay đổi các giá trị assert:
```python
# Ví dụ: thay đổi từ 2 giây thành 3 giây
assert response_time < 3.0, f"Response time quá chậm: {response_time}s"
```

## 🐛 Troubleshooting

### Lỗi Import
```bash
# Đảm bảo PYTHONPATH đúng
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Database Issues
```bash
# Reset test database
python src/manage.py migrate --settings=config.settings
```

### VnStock API Issues
- Check internet connection
- Verify VnStock service status
- Tests sử dụng mocking nên không phụ thuộc API thật

### Memory Issues
```bash
# Giảm số concurrent users trong performance tests
# Hoặc chạy tests từng phần
python tests/run_tests.py functional
python tests/run_tests.py performance
```

## 📈 Metrics và Monitoring

### Key Metrics
- **Test Coverage:** > 90%
- **Functional Tests:** 100% pass rate
- **Performance Tests:** Response time < 2s
- **Stress Tests:** > 95% success rate under load

### Continuous Integration
Để tích hợp với CI/CD:

```yaml
# .github/workflows/tests.yml
- name: Run Tests
  run: |
    python tests/run_tests.py all
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./tests/coverage_html/coverage.xml
```

## 🤝 Contributing

Khi thêm features mới:
1. ✅ Viết functional tests cho feature
2. ✅ Thêm performance tests nếu cần
3. ✅ Đảm bảo coverage > 90%
4. ✅ Chạy full test suite trước commit

---

**📞 Liên hệ:** Nếu có vấn đề với test suite, vui lòng tạo issue hoặc liên hệ team development. 