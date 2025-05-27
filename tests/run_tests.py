#!/usr/bin/env python
"""
Script chạy test cho Portfolio Management System.
Hỗ trợ các loại test khác nhau: functional, performance, unit, integration.
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

# Thêm src vào Python path
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / 'src'
sys.path.insert(0, str(SRC_PATH))

def run_command(command, cwd=None):
    """Chạy command và hiển thị output."""
    print(f"🔄 Đang chạy: {command}")
    print("-" * 60)
    
    start_time = time.time()
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd or PROJECT_ROOT,
        capture_output=False
    )
    end_time = time.time()
    
    print(f"⏱️  Thời gian thực hiện: {end_time - start_time:.2f} giây")
    print("-" * 60)
    return result.returncode

def run_functional_tests():
    """Chạy functional tests."""
    print("🧪 CHẠY FUNCTIONAL TESTS")
    return run_command("pytest tests/functional/ -v --tb=short")

def run_performance_tests():
    """Chạy performance tests."""
    print("⚡ CHẠY PERFORMANCE TESTS")
    return run_command("pytest tests/performance/ -v --tb=short -s")

def run_all_tests():
    """Chạy tất cả tests."""
    print("🔄 CHẠY TẤT CẢ TESTS")
    return run_command("pytest tests/ -v --cov=src/portfolio --cov-report=html --cov-report=term")

def run_quick_tests():
    """Chạy quick tests (loại trừ performance tests)."""
    print("⚡ CHẠY QUICK TESTS")
    return run_command("pytest tests/functional/ -v --tb=short -x")

def run_coverage_report():
    """Tạo coverage report."""
    print("📊 TẠO COVERAGE REPORT")
    return run_command("pytest tests/ --cov=src/portfolio --cov-report=html --cov-report=term-missing")

def run_stress_tests():
    """Chạy stress tests."""
    print("💪 CHẠY STRESS TESTS")
    return run_command("pytest tests/performance/test_stress_testing.py -v -s")

def run_load_tests():
    """Chạy load tests."""
    print("🔄 CHẠY LOAD TESTS")
    return run_command("pytest tests/performance/test_load_testing.py -v -s")

def setup_test_environment():
    """Thiết lập môi trường test."""
    print("🔧 THIẾT LẬP MÔI TRƯỜNG TEST")
    
    # Cài đặt test dependencies
    if not os.path.exists(PROJECT_ROOT / 'venv'):
        print("❌ Virtual environment không tồn tại!")
        print("Vui lòng tạo virtual environment trước.")
        return False
    
    # Install test requirements
    install_cmd = "pip install -r tests/requirements_test.txt"
    return run_command(install_cmd) == 0

def clean_test_artifacts():
    """Dọn dẹp các file test artifacts."""
    print("🧹 DỌN DẸP TEST ARTIFACTS")
    
    artifacts = [
        ".coverage",
        "tests/coverage_html",
        ".pytest_cache",
        "**/__pycache__",
        "**/*.pyc"
    ]
    
    for pattern in artifacts:
        if pattern.startswith("**"):
            run_command(f"find . -name '{pattern.replace('**/', '')}' -delete")
        else:
            if os.path.exists(pattern):
                if os.path.isdir(pattern):
                    run_command(f"rm -rf {pattern}")
                else:
                    run_command(f"rm -f {pattern}")

def main():
    parser = argparse.ArgumentParser(description="Portfolio Management Test Runner")
    parser.add_argument(
        'test_type',
        choices=['functional', 'performance', 'all', 'quick', 'coverage', 'stress', 'load', 'setup', 'clean'],
        help='Loại test cần chạy'
    )
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Chạy tests song song'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Hiển thị output chi tiết'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧪 PORTFOLIO MANAGEMENT TEST RUNNER")
    print("=" * 60)
    
    # Thay đổi working directory
    os.chdir(PROJECT_ROOT)
    
    start_time = time.time()
    
    if args.test_type == 'setup':
        success = setup_test_environment()
    elif args.test_type == 'clean':
        clean_test_artifacts()
        success = True
    elif args.test_type == 'functional':
        success = run_functional_tests() == 0
    elif args.test_type == 'performance':
        success = run_performance_tests() == 0
    elif args.test_type == 'all':
        success = run_all_tests() == 0
    elif args.test_type == 'quick':
        success = run_quick_tests() == 0
    elif args.test_type == 'coverage':
        success = run_coverage_report() == 0
    elif args.test_type == 'stress':
        success = run_stress_tests() == 0
    elif args.test_type == 'load':
        success = run_load_tests() == 0
    else:
        print(f"❌ Loại test không hợp lệ: {args.test_type}")
        success = False
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print("=" * 60)
    if success:
        print("✅ TESTS HOÀN THÀNH THÀNH CÔNG!")
    else:
        print("❌ TESTS THẤT BẠI!")
    
    print(f"⏱️  Tổng thời gian: {total_time:.2f} giây")
    print("=" * 60)
    
    # Coverage report location
    if args.test_type in ['all', 'coverage']:
        print(f"📊 Coverage report: {PROJECT_ROOT}/tests/coverage_html/index.html")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main()) 