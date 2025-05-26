from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Portfolio, Assets, BankTransaction, BankAccount, StockTransaction, Wallet
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'gender', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên của bạn'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập họ của bạn'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập email của bạn'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập số điện thoại của bạn'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Nhập địa chỉ của bạn'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'profilePictureInput'
            }),
        }

# ===== Forms cho ví điện tử =====
BANK_CHOICES = [
    ('Vietcombank', 'Vietcombank'),
    ('Techcombank', 'Techcombank'),
    ('BIDV', 'BIDV'),
    ('Vietinbank', 'Vietinbank'),
    ('MB Bank', 'MB Bank'),
    ('TPBank', 'TPBank'),
    ('ACB', 'ACB'),
    ('Sacombank', 'Sacombank'),
    ('VPBank', 'VPBank'),
    ('Ngân hàng khác', 'Ngân hàng khác')
]

class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['bank_name', 'account_name', 'account_number', 'branch', 'is_default']
        widgets = {
            'bank_name': forms.Select(choices=BANK_CHOICES, attrs={
                'class': 'form-select',
                'id': 'bankName'
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên chủ tài khoản'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập số tài khoản'
            }),
            'branch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập chi nhánh (không bắt buộc)'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        if not account_number.isdigit():
            raise forms.ValidationError("Số tài khoản chỉ được chứa các chữ số")
        return account_number

class WithdrawForm(forms.Form):
    amount = forms.DecimalField(
        label="Số tiền muốn rút",
        min_value=100000,
        max_digits=15,
        decimal_places=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Nhập số tiền muốn rút',
            'min': '100000',
            'step': '50000'
        })
    )
    
    bank_account = forms.ModelChoiceField(
        label="Tài khoản ngân hàng",
        queryset=BankAccount.objects.none(),
        required=False,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    description = forms.CharField(
        label="Ghi chú",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'withdrawNote',
            'rows': 3,
            'placeholder': 'Nhập ghi chú của bạn (nếu có)'
        })
    )
    
    agree_terms = forms.BooleanField(
        label="Tôi đồng ý với điều khoản rút tiền",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'agreeTerms'
        })
    )
    
    # Các trường cho tài khoản ngân hàng mới
    new_bank_name = forms.ChoiceField(
        label="Ngân hàng",
        choices=BANK_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'bankName'
        })
    )
    
    new_other_bank_name = forms.CharField(
        label="Tên ngân hàng khác",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'otherBankName',
            'placeholder': 'Nhập tên ngân hàng'
        })
    )
    
    new_account_name = forms.CharField(
        label="Chủ tài khoản",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'accountName',
            'placeholder': 'Nhập tên chủ tài khoản'
        })
    )
    
    new_account_number = forms.CharField(
        label="Số tài khoản",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'accountNumber',
            'placeholder': 'Nhập số tài khoản'
        })
    )
    
    new_branch = forms.CharField(
        label="Chi nhánh",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'branch',
            'placeholder': 'Nhập chi nhánh (không bắt buộc)'
        })
    )
    
    new_is_default = forms.BooleanField(
        label="Đặt làm tài khoản mặc định",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'defaultAccount'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank_account'].queryset = BankAccount.objects.filter(user=user).order_by('-is_default')
        self.user = user
        
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        user_wallet = Wallet.objects.get(user=self.user)
        
        if amount > user_wallet.balance:
            raise forms.ValidationError("Số tiền rút không được vượt quá số dư khả dụng")
        
        return amount
        
    def clean(self):
        cleaned_data = super().clean()
        bank_account = cleaned_data.get('bank_account')
        
        # Nếu không có tài khoản ngân hàng nào được chọn
        if not bank_account:
            # Kiểm tra xem đã nhập đủ thông tin tài khoản mới chưa
            new_bank_name = cleaned_data.get('new_bank_name')
            new_account_name = cleaned_data.get('new_account_name')
            new_account_number = cleaned_data.get('new_account_number')
            
            if not (new_bank_name and new_account_name and new_account_number):
                if BankAccount.objects.filter(user=self.user).exists():
                    self.add_error('bank_account', 'Vui lòng chọn tài khoản ngân hàng')
                else:
                    self.add_error(None, 'Vui lòng thêm thông tin tài khoản ngân hàng')
        
        return cleaned_data