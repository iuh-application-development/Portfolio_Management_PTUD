
document.addEventListener('DOMContentLoaded', function() {
    // Xử lý hiển thị trường nhập tên ngân hàng khác
    const bankNameSelect = document.getElementById('new_bank_name');
    const otherBankGroup = document.getElementById('otherBankGroup');
    
    if (bankNameSelect && otherBankGroup) {
        // Kiểm tra giá trị ban đầu
        if (bankNameSelect.value === 'other') {
            otherBankGroup.classList.remove('d-none');
        } else {
            otherBankGroup.classList.add('d-none');
        }
        
        // Thêm event listener cho sự kiện thay đổi
        bankNameSelect.addEventListener('change', function() {
            if (this.value === 'other') {
                otherBankGroup.classList.remove('d-none');
                document.getElementById('new_other_bank_name').focus();
            } else {
                otherBankGroup.classList.add('d-none');
            }
        });
    }
    
    // Validate form trước khi submit
    const bankAccountForm = document.getElementById('bankAccountForm');
    if (bankAccountForm) {
        bankAccountForm.addEventListener('submit', function(event) {
            const bankName = document.getElementById('new_bank_name').value;
            const accountName = document.getElementById('new_account_name').value;
            const accountNumber = document.getElementById('new_account_number').value;
            
            let isValid = true;
            let errorMessage = '';
            
            // Validate ngân hàng
            if (!bankName) {
                isValid = false;
                errorMessage = 'Vui lòng chọn ngân hàng';
                document.getElementById('new_bank_name').focus();
            } 
            // Validate tên ngân hàng khác nếu chọn "Ngân hàng khác"
            else if (bankName === 'other') {
                const otherBankName = document.getElementById('new_other_bank_name').value.trim();
                if (!otherBankName) {
                    isValid = false;
                    errorMessage = 'Vui lòng nhập tên ngân hàng khác';
                    document.getElementById('new_other_bank_name').focus();
                }
            }
            
            // Validate tên chủ tài khoản
            if (isValid && !accountName.trim()) {
                isValid = false;
                errorMessage = 'Vui lòng nhập tên chủ tài khoản';
                document.getElementById('new_account_name').focus();
            }
            
            // Validate số tài khoản
            if (isValid && !accountNumber.trim()) {
                isValid = false;
                errorMessage = 'Vui lòng nhập số tài khoản';
                document.getElementById('new_account_number').focus();
            }
            
            // Hiển thị thông báo lỗi nếu có
            if (!isValid) {
                event.preventDefault();
                
                // Tạo thông báo lỗi
                showError(errorMessage);
            }
        });
    }
    
    // Hàm hiển thị thông báo lỗi
    function showError(message) {
        // Xóa thông báo lỗi cũ nếu có
        removeExistingAlerts();
        
        // Tạo thông báo lỗi mới
        const alertEl = document.createElement('div');
        alertEl.className = 'alert alert-danger alert-dismissible fade show rounded-4 mb-3';
        alertEl.innerHTML = `
            <div class="d-flex">
                <div class="me-3">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div>
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        // Thêm thông báo vào đầu form
        const formContainer = document.querySelector('.card-body');
        formContainer.insertBefore(alertEl, formContainer.firstChild);
    }
    
    // Hàm xóa các thông báo hiện tại
    function removeExistingAlerts() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => alert.remove());
    }

    // Xử lý auto-format số tài khoản (tùy chọn, để dễ đọc)
    const accountNumberInput = document.getElementById('new_account_number');
    if (accountNumberInput) {
        accountNumberInput.addEventListener('input', function(e) {
            // Chỉ giữ lại số, loại bỏ các ký tự khác
            let value = this.value.replace(/\D/g, '');
            this.value = value;
        });
    }
});