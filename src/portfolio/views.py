from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError, transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F, Sum, ExpressionWrapper, FloatField
from django.utils import timezone
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.conf import settings
from rest_framework import status


from .models import Portfolio, PortfolioSymbol, Assets, User, Wallet, StockTransaction, BankAccount, BankTransaction
# from .forms import PortfolioForm, AssetForm, TransactionForm, UserRegistrationForm, UserProfileForm
from .vnstock_services import (
    get_price_board, get_historical_data, get_ticker_companyname, get_current_price , sync_vnstock_to_assets,
    get_company_name, get_list_stock_market
)
from .utils import generate_qr_code, check_paid

from vnstock import Vnstock
from decimal import Decimal
from .utils import get_ai_response, get_auth0_user_profile
from urllib.parse import quote_plus, urlencode
import os
import uuid
import json
import pandas as pd
import random
from datetime import datetime, timedelta
# from authlib.integrations.django_client import OAuth  # Comment out this import



# Comment out OAuth setup temporarily
"""
oauth = OAuth()
oauth.register(
    "auth0",
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)
"""

# Auth0 related views - replaced with Django authentication
def login_view(request):
    """Sử dụng Auth0 để xác thực người dùng"""
    from authlib.integrations.django_client import OAuth
    from django.conf import settings
    from urllib.parse import quote_plus, urlencode
    
    # Khởi tạo OAuth client
    oauth = OAuth()
    oauth.register(
        "auth0",
        client_id=settings.AUTH0_CLIENT_ID,
        client_secret=settings.AUTH0_CLIENT_SECRET,
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
    )
    
    # Chuyển hướng đến trang đăng nhập Auth0
    return oauth.auth0.authorize_redirect(
        request, request.build_absolute_uri(reverse("callback"))
    )

def callback(request):
    """Xử lý callback từ Auth0 và đăng nhập người dùng"""
    from authlib.integrations.django_client import OAuth
    from django.conf import settings
    import json
    from .utils import get_auth0_user_profile
    
    # Khởi tạo OAuth client
    oauth = OAuth()
    oauth.register(
        "auth0",
        client_id=settings.AUTH0_CLIENT_ID,
        client_secret=settings.AUTH0_CLIENT_SECRET,
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
    )
    
    # Lấy token từ Auth0
    token = oauth.auth0.authorize_access_token(request)
    userinfo = token.get('userinfo')
    
    # Lấy thêm thông tin từ API Auth0 nếu được
    access_token = token.get('access_token')
    if access_token:
        additional_info = get_auth0_user_profile(access_token)
        if additional_info:
            # Merge additional info vào userinfo
            userinfo.update(additional_info)
    
    if userinfo:
        # Lưu thông tin người dùng vào session
        request.session['userinfo'] = userinfo
        
        # Kiểm tra xem người dùng đã tồn tại trong database chưa
        auth0_user_id = userinfo.get('sub')
        email = userinfo.get('email')
        
        try:
            # Tìm user bằng auth0_user_id
            user = User.objects.get(auth0_user_id=auth0_user_id)
        except User.DoesNotExist:
            try:
                # Tìm user bằng email nếu không tìm thấy qua auth0_user_id
                user = User.objects.get(email=email)
                user.auth0_user_id = auth0_user_id
                user.save()
            except User.DoesNotExist:
                # Tạo user mới nếu chưa tồn tại
                user = User.objects.create_user(
                    username=email.split('@')[0],
                    email=email,
                    auth0_user_id=auth0_user_id,
                    first_name=userinfo.get('given_name', ''),
                    last_name=userinfo.get('family_name', ''),
                    profile_picture_url=userinfo.get('picture', '')
                )
                # Tự động tạo ví điện tử cho người dùng mới
                from .models import Wallet
                Wallet.objects.create(user=user)
        
        # Đăng nhập người dùng
        login(request, user)
        
        # Cập nhật thông tin người dùng từ Auth0 profile
        if 'picture' in userinfo and userinfo['picture']:
            user.profile_picture_url = userinfo['picture']
        if 'given_name' in userinfo and userinfo['given_name']:
            user.first_name = userinfo['given_name']
        if 'family_name' in userinfo and userinfo['family_name']:
            user.last_name = userinfo['family_name']
        for field in user._meta.fields:
            value = getattr(user, field.name)
            if isinstance(value, str) and len(value) > 200:
                print(f"Field {field.name} quá dài: {len(value)} ký tự")

        user.save()

        
        return redirect('dashboard')
    
    return redirect('home')

def logout_view(request):
    """Đăng xuất khỏi Django và Auth0"""
    from django.conf import settings
    from urllib.parse import quote_plus, urlencode
    
    # Đăng xuất khỏi Django
    logout(request)
    
    # Xóa session
    request.session.clear()
    
    # Chuyển hướng đến trang đăng xuất của Auth0
    return redirect(
        f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("home")),
                "client_id": settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        )
    )

def register(request):
    """Chuyển hướng đến trang đăng ký của Auth0"""
    # Sử dụng cùng hàm login_view để chuyển hướng đến Auth0
    return login_view(request)

# User profile view
@login_required
def user_profile(request):
    user = request.user

    if request.method == 'POST':
        # Lấy dữ liệu từ form gửi lên
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        gender = request.POST.get('gender', '').strip()

        # Gán dữ liệu cho user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        user.address = address
        user.gender = gender

        # Xử lý upload ảnh
        if 'profile_picture' in request.FILES and request.FILES['profile_picture']:
            user.profile_picture = request.FILES['profile_picture']
            # Nếu bạn có trường profile_picture_url (ví dụ dùng Auth0), hãy xử lý nếu cần
            if hasattr(user, 'profile_picture_url'):
                user.profile_picture_url = None

        user.save()
        messages.success(request, 'Thông tin cá nhân đã được cập nhật thành công!')
        return redirect('user_profile')
    else:
        # Hiển thị thông tin user hiện tại để render lên template
        pass  # Không cần gì đặc biệt

    # Lấy thông tin user từ Auth0 nếu có
    auth0_userinfo = request.session.get('userinfo', {})

    return render(request, 'portfolio/user_profile.html', {
        'user': user,
        'auth0_userinfo': auth0_userinfo
    })



def home(request):
    return render(request, 'portfolio/home.html')


@login_required
def dashboard(request):
    user = request.user
    # user = User.objects.get(pk=1)
    wallet = Wallet.objects.get(user=user)
    user_balance = wallet.balance

    user_assets = Assets.objects.filter(user=user)
    number_of_symbol = user_assets.count()
    list_stock = list(user_assets.values_list('symbol', flat=True))

    portfolios = Portfolio.objects.filter(user=user)
    number_of_portfolio = portfolios.count()
    # print('='*100)
    # print(portfolios)
    current_price_symbol = None
    if list_stock:
        current_price_symbol = get_current_price(list_stock)
        # current_price_symbol = get_current_price(list_stock).set_index('symbol')['ref_price'].to_dict()
    total_assets_value = user_balance
    total_profit_loss = 0
    for portfolio in portfolios:
        portfolio_symbol = PortfolioSymbol.objects.filter(portfolio=portfolio)
        symbol_quantity_df = pd.DataFrame(portfolio_symbol.values_list('symbol', 'quantity', 'average_price'), columns=['symbol', 'quantity', 'average_price'])
        current_price_df = current_price_symbol[current_price_symbol.symbol.isin(symbol_quantity_df['symbol'])]
        total_df = pd.merge(symbol_quantity_df, current_price_df, on='symbol', how='inner')
        # print(total_df)
        
        portfolio.portfolio_value = sum(total_df['quantity'] * total_df['ref_price'])
        portfolio.profit_loss_percentage = sum((total_df['ref_price'] - total_df['average_price']) / total_df['average_price'] * 100)
        total_assets_value += portfolio.portfolio_value
        total_profit_loss += ((total_df['ref_price'] - total_df['average_price']) * total_df['quantity']).sum()
    total_profit_loss_percentage = round(total_profit_loss / total_assets_value * 100, 2) if total_assets_value != 0 else 0

    recent_transactions = StockTransaction.objects.filter(user=user).order_by('-transaction_time')[:5]
    list_symbol_recent_transactions = list(recent_transactions.values_list('symbol', flat=True))
    list_company_name_recent_transactions_df = get_company_name(list_symbol_recent_transactions)
    for i, transaction in enumerate(recent_transactions):
        transaction.total_value = transaction.quantity * transaction.price
        # print(list_company_name_recent_transactions.isin([transaction.symbol])['organ_name'])
        transaction.company_name = list_company_name_recent_transactions_df[list_company_name_recent_transactions_df.ticker.isin([transaction.symbol])].iloc[0, 1]

    context = {
        "total_assets_value": total_assets_value,
        "total_profit_loss_percentage": total_profit_loss_percentage,
        "user_balance": user_balance,
        "number_of_portfolio": number_of_portfolio,
        "number_of_symbol": number_of_symbol,
        "portfolios": portfolios,
        "recent_transactions": recent_transactions,
    }
    return render(request, 'portfolio/dashboard.html', context)

def portfolio_list(request):
    # user = User.objects.get(pk=1)
    user = request.user
    portfolios = Portfolio.objects.filter(user=user)
    # print('='*100)
    # print(portfolios.values_list('id'))
    for portfolio in portfolios:
        portfolio_symbol_list = PortfolioSymbol.objects.filter(portfolio=portfolio)
        # print(portfolio_symbol_list)
        # print(portfolio.id, portfolio_symbol_list)
        portfolio_value = portfolio_symbol_list.aggregate(total_value=Sum(F('quantity') * F('average_price')))['total_value'] or 0
        portfolio.portfolio_value = portfolio_value
        portfolio.progress = round(portfolio_value / portfolio.target_value * 100) if portfolio.target_value!=0 else 100
    return render(request, 'portfolio/portfolio_list.html', {'portfolios': portfolios})

@login_required
def portfolio_detail(request, pk):
    context = {}
    try:
        portfolio = Portfolio.objects.get(pk=pk)
        user = request.user
        # user = User.objects.get(pk=1)
        # Đảm bảo người dùng hiện tại là chủ sở hữu danh mục
        if request.user.is_authenticated and portfolio.user == request.user:
            pass
        else:
            # Trong môi trường phát triển, có thể bỏ qua xác thực người dùng
            # Trong môi trường sản xuất, bạn nên chuyển hướng nếu không có quyền
            pass

        # Lấy danh sách các mã cổ phiếu trong portfolio
        portfolio_symbols = PortfolioSymbol.objects.filter(portfolio=portfolio)
        symbols_in_portfolio = [ps.symbol for ps in portfolio_symbols]
        
        # Lấy các giao dịch gần nhất của portfolio này dựa trên portfolio_id
        recent_transactions = StockTransaction.objects.filter(
            portfolio=portfolio
        ).order_by('-transaction_time')[:5]  # Lấy 5 giao dịch gần nhất

        # Xử lý thông tin portfolio symbols
        portfolio_symbol_list = PortfolioSymbol.objects.filter(portfolio_id=portfolio.id)
        
        # Chỉ lấy giá hiện tại nếu có cổ phiếu trong danh mục
        if portfolio_symbol_list.exists():
            # Danh sách cổ phiếu có trong tài sản của user
            list_stocks = [ps.symbol for ps in portfolio_symbol_list]
            
            try:
                # Lấy giá hiện tại - Thêm xử lý lỗi
                current_price_stock_df = get_current_price(list_stocks)
                
                # Lấy thông tin công ty - Thêm xử lý lỗi
                try:
                    company_name_df = get_company_name(list_stocks)
                except Exception as e:
                    print(f"Error getting company names: {str(e)}")
                    # Tạo DataFrame trống khi không thể lấy tên công ty
                    import pandas as pd
                    company_name_df = pd.DataFrame({'ticker': list_stocks, 'organ_name': ['Unknown'] * len(list_stocks)})
                
                # Cập nhật thông tin cho từng cổ phiếu trong portfolio
                for stock in portfolio_symbol_list:
                    try:
                        # Kiểm tra xem symbol có trong DataFrame không
                        price_row = current_price_stock_df[current_price_stock_df['symbol'] == stock.symbol]
                        if not price_row.empty:
                            stock.current_price = Decimal(float(price_row.iloc[0, 1]))
                        else:
                            # Nếu không tìm thấy giá hiện tại, sử dụng giá trung bình
                            stock.current_price = stock.average_price
                            print(f"Warning: Could not find current price for {stock.symbol}, using average price")
                            
                        # Tìm tên công ty
                        name_row = company_name_df[company_name_df['ticker'] == stock.symbol]
                        if not name_row.empty:
                            stock.company_name = name_row.iloc[0, 1]
                        else:
                            stock.company_name = "Unknown"
                            
                        # Tính toán các giá trị
                        quantity = stock.quantity
                        avg_buy_price = stock.average_price
                        total_current_price = quantity * stock.current_price
                        total_invest_value = Decimal(quantity * float(avg_buy_price))
                        profit_loss = total_current_price - total_invest_value

                        stock.total_current_price = total_current_price
                        stock.profit_loss = profit_loss
                        stock.save()
                        
                    except Exception as stock_error:
                        print(f"Error processing stock {stock.symbol}: {str(stock_error)}")
                        # Set default values to avoid breaking the template
                        stock.current_price = stock.average_price
                        stock.company_name = "Unknown"
                        stock.total_current_price = stock.quantity * stock.average_price
                        stock.profit_loss = 0
                        stock.save()
                
            except Exception as price_error:
                # Xử lý lỗi khi không thể lấy giá hiện tại
                print(f"Error getting current prices: {str(price_error)}")
                
                # Đặt giá hiện tại bằng giá trung bình cho tất cả cổ phiếu
                for stock in portfolio_symbol_list:
                    stock.current_price = stock.average_price
                    stock.company_name = "Unknown"  # Không có tên công ty
                    stock.total_current_price = stock.quantity * stock.average_price
                    stock.profit_loss = 0
                    stock.save()
        
        # Calculate portfolio totals - Handled even with errors above
        portfolio_value = portfolio_symbol_list.aggregate(total_value=Sum(F('quantity') * F('average_price')))['total_value'] or 0
        total_assets = portfolio_symbol_list.aggregate(
            total=Sum(F('quantity') * F('current_price'))
        )['total'] or 0
        total_buy_price = portfolio_symbol_list.aggregate(total_buy=Sum(F('quantity') * F('average_price')))['total_buy'] or 0
        
        profit_loss = 0
        profit_loss_percentage = 0
        
        if total_buy_price != 0:
            profit_loss = (total_assets - total_buy_price)
            profit_loss_percentage = round((profit_loss / total_buy_price) * 100, 2)
            
        if profit_loss > 0:
            profit_loss = f"+{profit_loss}"
            profit_loss_percentage = f"+{profit_loss_percentage}"
            
        # Xử lý thông tin thêm cho recent_transactions để hiển thị
        for transaction in recent_transactions:
            transaction.transaction_type_display = "Mua" if transaction.transaction_type == "buy" else "Bán"
            
        context = {
            "portfolio": portfolio,
            "portfolio_value": portfolio_value,
            "profit_loss": profit_loss,
            "profit_loss_percentage": profit_loss_percentage,
            "portfolio_symbol_list": portfolio_symbol_list,
            "recent_transactions": recent_transactions,  # Thêm danh sách giao dịch gần nhất
        }
    except Portfolio.DoesNotExist:
        messages.error(request, f"Danh mục không tồn tại!")
        return redirect("portfolio_list")
    except Exception as e:
        messages.error(request, f"Có lỗi xảy ra: {str(e)}")
        return redirect("portfolio_list")
        
    return render(request, 'portfolio/portfolio_detail.html', context)

@login_required
def portfolio_create(request):
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        name = request.POST.get('name').strip()  # Loại bỏ khoảng trắng ở đầu và cuối
        description = request.POST.get('description')
        investment_goal = request.POST.get('investment_goal')
        target_value = request.POST.get('target_value')
        risk_tolerance = request.POST.get('risk_tolerance')

        # Tạo context với dữ liệu form để sử dụng khi render lại form
        form_data = {
            'name': name,
            'description': description,
            'investment_goal': investment_goal,
            'target_value': target_value,
            'risk_tolerance': risk_tolerance
        }
        print("=" * 100)
        print(form_data)

        # Kiểm tra điều kiện bắt buộc
        if (not name):
            messages.error(request, 'Hãy đảm bảo đầy đủ thông tin!')
            return render(request, 'portfolio/portfolio_form.html', context={'form_data': form_data})

        try:
            # Tạo danh mục đầu tư
            with transaction.atomic():
                portfolio = Portfolio.objects.create(
                    name=name,
                    user=request.user,
                    # user=User.objects.get(pk=1),
                    description=description,
                    investment_goal=investment_goal,
                    target_value=Decimal(float(target_value)) if target_value else 0,
                    risk_tolerance=risk_tolerance
                )

                # Thông báo thành công
                messages.success(request, f'Danh mục "{portfolio.name}" đã được tạo thành công!')
                return redirect('portfolio_list')  # Chuyển hướng đến danh sách danh mục đầu tư

        except IntegrityError:
            # Xử lý trường hợp tên danh mục đã tồn tại
            messages.error(request, f'Tên danh mục "{name}" đã tồn tại. Vui lòng chọn tên khác.')
            return render(request, 'portfolio/portfolio_form.html', context={'form_data': form_data})
    return render(request, 'portfolio/portfolio_form.html')

@login_required
def portfolio_update(request, pk):
    try:
        portfolio = get_object_or_404(Portfolio, pk=pk)
        
        # Ensure the user owns this portfolio (commented out for development)
        # if request.user != portfolio.user:
        #     messages.error(request, "Bạn không có quyền chỉnh sửa danh mục này")
        #     return redirect('portfolio_list')
        
        if request.method == 'POST':
            # Lấy dữ liệu từ form
            name = request.POST.get('name').strip()
            description = request.POST.get('description', '')
            investment_goal = request.POST.get('investment_goal', '')
            target_value = request.POST.get('target_value', 0)
            risk_tolerance = request.POST.get('risk_tolerance', 'medium')
            
            # Kiểm tra điều kiện bắt buộc
            if (not name):
                messages.error(request, 'Hãy đảm bảo đầy đủ thông tin!')
                return render(request, 'portfolio/portfolio_form.html', context={
                    'portfolio': portfolio,
                    'form_data': request.POST,
                    'is_update': True
                })
            
            try:
                # Cập nhật danh mục đầu tư
                portfolio.name = name
                portfolio.description = description
                portfolio.investment_goal = investment_goal
                portfolio.target_value = Decimal(target_value) if target_value else Decimal(0)
                portfolio.risk_tolerance = risk_tolerance
                portfolio.save()
                
                # Thông báo thành công
                messages.success(request, f'Danh mục đã được cập nhật thành công!')
                return redirect('portfolio_detail', pk=portfolio.id)
                
            except IntegrityError:
                # Xử lý trường hợp tên danh mục đã tồn tại
                messages.error(request, f'Tên danh mục "{name}" đã tồn tại. Vui lòng chọn tên khác.')
                return render(request, 'portfolio/portfolio_form.html', context={
                    'portfolio': portfolio,
                    'form_data': request.POST,
                    'is_update': True
                })
        
        # GET request - hiển thị form với dữ liệu hiện tại
        return render(request, 'portfolio/portfolio_form.html', {
            'portfolio': portfolio,
            'is_update': True
        })
        
    except Exception as e:
        messages.error(request, f"Có lỗi xảy ra: {str(e)}")
        return redirect('portfolio_list')

@login_required
def portfolio_delete(request, pk):
    """View to handle portfolio deletion"""
    try:
        portfolio = get_object_or_404(Portfolio, pk=pk)
        
        # Ensure the user owns this portfolio (commented out for development)
        if request.user != portfolio.user:
            messages.error(request, "Bạn không có quyền xóa danh mục này")
            return redirect('portfolio_list')
        
        if request.method == 'POST':
            # Check if portfolio has any symbols associated with it
            portfolio_symbols = PortfolioSymbol.objects.filter(portfolio=portfolio)
            
            if portfolio_symbols.exists():
                messages.error(
                    request, 
                    f'Không thể xóa danh mục "{portfolio.name}" vì danh mục đang có cổ phiếu. '
                    f'Vui lòng bán hết cổ phiếu trước khi xóa danh mục.'
                )
                return redirect('portfolio_list')
            
            # Store the name for the success message
            portfolio_name = portfolio.name
            
            # Delete the portfolio
            portfolio.delete()
            
            # Show success message
            messages.success(request, f'Danh mục "{portfolio_name}" đã được xóa thành công!')
            
            # Redirect to portfolio list
            return redirect('portfolio_list')
        
        # If it's a GET request, render a confirmation page
        # This is a fallback - the modal should handle confirmation
        return render(request, 'portfolio/portfolio_confirm_delete.html', {'portfolio': portfolio})
        
    except Exception as e:
        messages.error(request, f"Có lỗi xảy ra khi xóa danh mục: {str(e)}")
        return redirect("portfolio_list")


@login_required
def asset_list(request):
    # user = User.objects.get(pk=1)
    user = request.user

    assets = Assets.objects.filter(user=user)
    # print(assets)
    list_stocks = list(assets.values_list('symbol', flat=True))
    company_name_df = get_company_name(list_stocks)
    for i, stock in enumerate(assets):
        # print(stock.symbol)
        current_price_stock_df = get_current_price(stock.symbol)
        current_price_stock = Decimal(float(current_price_stock_df.iloc[0,1]))
        Assets.objects.filter(user=user, symbol=stock.symbol).update(current_price=current_price_stock)
        stock.company_name = company_name_df.iloc[i, 1]
        # print('='*100)
        # print(stock.company_name)
        stock.total_buy_price_symbol = stock.quantity * stock.current_price
        stock.profit_loss_percentage = (stock.current_price - stock.average_price)/stock.average_price * 100
        # print(stock.current_price)
    total_assets = assets.aggregate(
        total=Sum(F('quantity') * F('current_price'))
    )['total'] or 0
    # print(total_assets)
    total_buy_price = assets.aggregate(total_buy=Sum(F('quantity') * F('average_price')))['total_buy'] or 0
    profit_loss = 0
    if total_buy_price!=0:
        profit_loss = ((total_assets - total_buy_price))
        profit_loss_percentage = round((profit_loss / total_buy_price) * 100, 2)
    else:
        profit_loss_percentage=0
        profit_loss_percentage=0
    number_of_stock = assets.count()

    context = {
        "total_assets": total_assets,
        "profit_loss": profit_loss,
        "profit_loss_percentage": profit_loss_percentage,
        "number_of_stock": number_of_stock,
        "assets" : assets,
    }
    return render(request, 'portfolio/asset_list.html', context)

@login_required
def asset_create(request):
    # if request.method == 'POST':
    #     form = AssetForm(request.POST)
    #     if form.is_valid():
    #         form.save()
    #         messages.success(request, 'Tài sản đã được thêm thành công!')
    #         return redirect('asset_list')
    # else:
    #     form = AssetForm()
    return render(request, 'portfolio/asset_form.html')

@login_required
def asset_detail(request, pk):
#     asset = get_object_or_404(Asset, pk=pk)
    return render(request, 'portfolio/asset_detail.html')

@login_required
def asset_update(request, pk):
#     asset = get_object_or_404(Asset, pk=pk)
#     if request.method == 'POST':
#         form = AssetForm(request.POST, instance=asset)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Tài sản đã được cập nhật!')
#             return redirect('asset_detail', pk=pk)
#     else:
#         form = AssetForm(instance=asset)
#     return render(request, 'portfolio/asset_form.html', {
#         'form': form,
#         'title': 'Chỉnh sửa tài sản'
#     })
    return render(request, 'portfolio/asset_form.html')


@login_required
def transaction_list(request):
    user = request.user
    portfolios = Portfolio.objects.filter(user=user)
    # print(portfolios)
    # bank_transactions = BankTransaction.objects.filter(user=user)
    stock_transactions = StockTransaction.objects.filter(user=user)
    stock_transactions = (
    StockTransaction.objects
        .filter(user=user)
        .annotate(total_value=ExpressionWrapper(F('quantity') * F('price'), output_field=FloatField()))
    )
    # Lọc theo danh mục
    portfolio_id = request.GET.get('portfolio')
    if portfolio_id:
        if portfolio_id == "-1":
            # Lọc theo danh mục không có cổ phiếu
            stock_transactions = stock_transactions.filter(portfolio__isnull=True)
            print(portfolio_id, stock_transactions)
        else:
            stock_transactions = stock_transactions.filter(portfolio_id=portfolio_id)
    
    # Lọc theo loại giao dịch
    transaction_type = request.GET.get('type')
    if transaction_type:
        stock_transactions = stock_transactions.filter(transaction_type=transaction_type)
    
    # Lọc theo ngày
    from_date = request.GET.get('from_date')
    if from_date:
        stock_transactions = stock_transactions.filter(transaction_time__gte=from_date)
    
    to_date = request.GET.get('to_date')
    if to_date:
        stock_transactions = stock_transactions.filter(transaction_time__lte=to_date)
    
    # Phân trang
    paginator = Paginator(stock_transactions.order_by('-transaction_time'), 10)
    page = request.GET.get('page')
    stock_transactions = paginator.get_page(page)
    
    context = {
        'stock_transactions': stock_transactions,
        'portfolios': portfolios,
    }
    return render(request, 'portfolio/transaction_list.html', context)
    # return render(request, 'portfolio/transaction_list.html')

@login_required
def transaction_create(request):
    # if request.method == 'POST':
    #     form = TransactionForm(request.POST)
    #     if form.is_valid():
    #         transaction = form.save(commit=False)
    #         transaction.total_amount = transaction.quantity * transaction.price
    #         transaction.save()
    #         messages.success(request, 'Giao dịch đã được tạo thành công!')
    #         return redirect('transaction_list')
    # else:
    #     form = TransactionForm()
    # return render(request, 'portfolio/transaction_form.html', {
    #     'form': form,
    #     'title': 'Tạo giao dịch mới'
    # })
    return render(request, 'portfolio/transaction_form.html')


@login_required
def buy_stock(request, portfolio_id):
    ticker_company = get_ticker_companyname()
    ticker_company_df = pd.DataFrame(ticker_company)
    ticker_company_js = ticker_company_df.to_json(orient='split')
    portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
    transaction_type = 'buy'
    context = {
        "portfolio": portfolio,
        "transaction_type": transaction_type,
        "ticker_company_js": ticker_company_js,
    }
    # print('='*100)
    # print(ticker_company_df)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # user = User.objects.get(pk=1)       # test user
                user = request.user
                symbol = request.POST.get('symbol')
                quantity = int(request.POST.get('quantity'))
                price = Decimal(request.POST.get('price'))
                notes = request.POST.get('notes')
                total_buy_price = float(quantity) * float(price)
                user_balance = Wallet.objects.get(user=user).balance
                if user_balance < total_buy_price:
                    formatted = f"{float(user_balance):,.0f}".replace(",", ".")
                    messages.error(request, f"Số dư không đủ để thực hiện giao dịch này. Số dư hiện tại: {formatted} VND")
                    return render(request, 'portfolio/transaction_form.html', context)
                
                current_price_symbol = Decimal(float(get_current_price(symbol).iloc[0,1]))
                # print(current_price_symbol, type(current_price_symbol))
                
                # Lấy hoặc tạo portfolio_symbol
                portfolio_symbol, created = PortfolioSymbol.objects.get_or_create(
                    portfolio=portfolio,
                    symbol=symbol,
                    defaults={
                        'quantity': 0,
                        'average_price': 0,
                        'current_price': current_price_symbol,
                        'profit_loss': 0
                    }
                )
                # Tính toán giá trung bình mới
                if created:
                    # Nếu là mã cổ phiếu mới trong danh mục
                    new_average_price = price
                else:
                    # Nếu đã có cổ phiếu này trong danh mục, tính lại giá trung bình
                    total_quantity = portfolio_symbol.quantity + quantity
                    total_cost = (portfolio_symbol.quantity * portfolio_symbol.average_price) + (quantity * price)
                    new_average_price = total_cost / total_quantity if total_quantity > 0 else 0
                # Cập nhật thông tin PortfolioSymbol
                portfolio_symbol.quantity += quantity
                portfolio_symbol.average_price = new_average_price
                # Giả sử giá hiện tại là giá mua mới nhất
                portfolio_symbol.current_price = current_price_symbol
                # Tính lãi/lỗ
                portfolio_symbol.profit_loss = (portfolio_symbol.current_price - portfolio_symbol.average_price) * portfolio_symbol.quantity
                portfolio_symbol.save()
                
                # Lưu giao dịch vào StockTransaction
                stock_transaction = StockTransaction(
                    user=user,
                    portfolio=portfolio,
                    transaction_type='buy',
                    price=price,
                    quantity=quantity,
                    total_price=Decimal(total_buy_price),
                    transaction_time=timezone.now(),  # Add this line to set current time
                    description=notes,
                    symbol=symbol
                    # Removed portfolio_symbol reference as it's no longer in the model
                )
                stock_transaction.save()

                assets, created_assets = Assets.objects.get_or_create(
                    user=user,
                    symbol=symbol,
                    defaults={
                        "quantity": 0,
                        'average_price': 0,
                        'current_price': current_price_symbol,
                        'profit_loss': 0
                    }
                )
                # print(assets)
                if created_assets:
                    # Nếu là mã cổ phiếu mới trong Assets
                    new_average_price = price
                else:
                    total_quantity = assets.quantity + quantity
                    total_cost = (assets.quantity * assets.average_price) + (quantity * price)
                    new_average_price = total_cost / total_quantity if total_quantity > 0 else 0
                assets.quantity += quantity
                assets.average_price = new_average_price
                # Giả sử giá hiện tại là giá mua mới nhất
                assets.current_price = current_price_symbol
                # Tính lãi/lỗ
                assets.profit_loss = (assets.current_price - assets.average_price) * assets.quantity
                assets.save()
                
            messages.success(request, 'Giao dịch mua đã được thực hiện thành công.')
            return redirect('portfolio_detail', pk=portfolio_id)
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra! {e}")
    return render(request, 'portfolio/transaction_form.html', context)

@login_required
def sell_stock(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
    user = request.user
    if portfolio.user != user:
        messages.error(request, "Bạn không có quyền truy cập vào danh mục này.")
        return redirect('portfolio_list')
    
    transaction_type = 'sell'
    
    # Get all stock symbols in this portfolio for the sell form dropdown
    portfolio_symbols = PortfolioSymbol.objects.filter(portfolio=portfolio)
    
    # Check if a specific symbol is requested in the query parameters
    selected_symbol = request.GET.get('symbol', '')
    
    context = {
        "portfolio": portfolio,
        "transaction_type": transaction_type,
        "portfolio_symbols": portfolio_symbols,
        "selected_symbol": selected_symbol
    }
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # user = User.objects.get(pk=1)  # test user
                symbol = request.POST.get('symbol')
                quantity = int(request.POST.get('quantity'))
                price = Decimal(request.POST.get('price'))
                notes = request.POST.get('notes')
                total_sell_price = float(quantity) * float(price)
                
                # Get the portfolio symbol
                portfolio_symbol = get_object_or_404(
                    PortfolioSymbol, 
                    portfolio=portfolio,
                    symbol=symbol
                )
                
                # Check if there are enough shares to sell
                if portfolio_symbol.quantity < quantity:
                    messages.error(request, f'Không đủ cổ phiếu để bán. Số lượng sở hữu: {portfolio_symbol.quantity}')
                    return render(request, 'portfolio/transaction_form.html', context)
                
                # Update the portfolio symbol
                portfolio_symbol.quantity -= quantity
                
                # If all shares are sold, set profit/loss to 0
                if portfolio_symbol.quantity == 0:
                    portfolio_symbol.profit_loss = 0
                else:
                    # Recalculate profit/loss for remaining shares
                    portfolio_symbol.profit_loss = (portfolio_symbol.current_price - portfolio_symbol.average_price) * portfolio_symbol.quantity
                
                # Save the portfolio symbol or delete if all sold
                portfolio_symbol_id = portfolio_symbol.id  # Save ID before potential deletion
                
                if portfolio_symbol.quantity > 0:
                    portfolio_symbol.save()
                    portfolio_symbol_exists = True
                else:
                    # If all shares are sold, delete the portfolio_symbol record
                    portfolio_symbol.delete()
                    portfolio_symbol_exists = False
                
                # Create a transaction record
                stock_transaction = StockTransaction(
                    user=user,
                    portfolio=portfolio if portfolio_symbol_exists else None,
                    transaction_type='sell',
                    price=price,
                    quantity=quantity,
                    total_price=Decimal(total_sell_price),
                    transaction_time=timezone.now(),  # Add this line to set current time
                    description=notes,
                    symbol=symbol
                    # Removed portfolio_symbol reference as it's no longer in the model
                )
                stock_transaction.save()
                
                # Update the Assets model
                try:
                    asset = Assets.objects.get(user=user, symbol=symbol)
                    asset.quantity -= quantity
                    
                    # Check if all assets are sold
                    if asset.quantity <= 0:
                        asset.delete()
                    else:
                        # Recalculate profit/loss for the remaining shares
                        asset.profit_loss = (asset.current_price - asset.average_price) * asset.quantity
                        asset.save()
                except Assets.DoesNotExist:
                    messages.warning(request, f'Không tìm thấy tài sản {symbol} trong cơ sở dữ liệu.')

                Wallet.objects.filter(user=user).update(balance = F('balance') + total_sell_price)
                user_wallet = Wallet.objects.get(user=user)
                user_wallet.refresh_from_db()
                
                messages.success(request, f'Đã bán thành công {quantity} cổ phiếu {symbol} với giá {price:,} VND')
                return redirect('portfolio_detail', pk=portfolio_id)
                
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra khi bán cổ phiếu: {str(e)}")
    
    return render(request, 'portfolio/transaction_form.html', context)

@login_required
def portfolio_transactions(request, portfolio_id):
#     portfolio = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)
#     transactions = Transaction.objects.filter(portfolio=portfolio).order_by('-transaction_date')
#     return render(request, 'portfolio/portfolio_transactions.html', {
#         'portfolio': portfolio,
#         'transactions': transactions
#     })
    return render(request, 'portfolio/portfolio_transactions.html')


# @login_required
def wallet(request):
    user = request.user
    # user = User.objects.get(pk=1)
    user_wallet = Wallet.objects.get(user=user)
    user_balance = user_wallet.balance
    user_bank_accounts = BankAccount.objects.filter(user=user).order_by('-is_default', '-created_at')
    context = {
        "user_balance": user_balance,
        "user_bank_accounts": user_bank_accounts,
    }
    
    return render(request, 'portfolio/wallet.html', context)

@login_required
def deposit_money(request):
    user_bank_accounts = BankAccount.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    context = {
        "user_bank_accounts": user_bank_accounts,
    }
    return render(request, 'portfolio/deposit.html', context)

# @login_required
def verify_deposit(request, transaction_id=None):
    """View to verify deposit transactions"""
    if request.method != 'POST':
        messages.success(request, "Xác nhận nạp tiền thành công! Số dư của bạn đã được cập nhật.")
        return redirect('deposit_money')
    
    # Just show success message and redirect
    return redirect('wallet')

# @login_required
def withdraw_money(request):
    return render(request, 'portfolio/withdraw.html')

# @login_required
def wallet_transactions(request):
    return render(request, 'portfolio/wallet_transactions.html')


@login_required
def bank_account_list(request):
    bank_accounts = BankAccount.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    context = {
        'bank_accounts': bank_accounts,
        'title': 'Danh sách tài khoản ngân hàng'
    }
    return render(request, 'portfolio/bank_account_list.html', context)

@login_required
def bank_account_create(request):
    """View để tạo mới tài khoản ngân hàng"""
    # Lấy danh sách các tài khoản ngân hàng của người dùng
    user = request.user
    bank_accounts = BankAccount.objects.filter(user=user).order_by('-is_default', '-created_at')
    
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        bank_name = request.POST.get('new_bank_name')
        other_bank_name = request.POST.get('new_other_bank_name')
        account_name = request.POST.get('new_account_name')
        account_number = request.POST.get('new_account_number')
        branch = request.POST.get('new_branch')
        is_default = request.POST.get('new_is_default') == 'on'
        
        # Validate dữ liệu
        errors = []
        if not bank_name:
            errors.append("Vui lòng chọn ngân hàng")
        
        # Nếu chọn "Ngân hàng khác" nhưng không nhập tên ngân hàng
        if bank_name == "Ngân hàng khác" and not other_bank_name:
            errors.append("Vui lòng nhập tên ngân hàng khác")
        
        if not account_name:
            errors.append("Vui lòng nhập tên chủ tài khoản")
        
        if not account_number:
            errors.append("Vui lòng nhập số tài khoản")
        elif not account_number.isdigit():
            errors.append("Số tài khoản chỉ được chứa các chữ số")
        
        # Kiểm tra xem số tài khoản đã tồn tại chưa
        if account_number and BankAccount.objects.filter(user=user, account_number=account_number).exists():
            errors.append("Số tài khoản này đã được đăng ký với tài khoản của bạn")
        
        # Nếu có lỗi, hiển thị thông báo lỗi
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Nếu đánh dấu là tài khoản mặc định hoặc đây là tài khoản đầu tiên, đặt tất cả các tài khoản khác là không mặc định
            if is_default or not bank_accounts.exists():
                BankAccount.objects.filter(user=user).update(is_default=False)
                is_default = True  # Đảm bảo tài khoản đầu tiên luôn là mặc định
            
            # Xử lý trường hợp ngân hàng khác
            final_bank_name = bank_name
            if bank_name == "Ngân hàng khác" and other_bank_name:
                final_bank_name = other_bank_name
            
            # Tạo tài khoản mới
            bank_account = BankAccount.objects.create(
                user=user,
                bank_name=final_bank_name,
                account_name=account_name,
                account_number=account_number,
                branch=branch,
                is_default=is_default
            )
            
            messages.success(request, f'Đã thêm tài khoản ngân hàng {final_bank_name} - {account_number}')
            return redirect('bank_account_list')

    return render(request, 'portfolio/bank_account_form.html')

@login_required
def update_bank_account(request, pk):
    """View để cập nhật tài khoản ngân hàng"""
    # Lấy tài khoản ngân hàng cần cập nhật
    bank_account = get_object_or_404(BankAccount, id=pk, user=request.user)
    
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        bank_name = request.POST.get('new_bank_name')
        other_bank_name = request.POST.get('new_other_bank_name')
        account_name = request.POST.get('new_account_name')
        account_number = request.POST.get('new_account_number')
        branch = request.POST.get('new_branch')
        is_default = request.POST.get('new_is_default') == 'on'
        
        # Validate dữ liệu
        errors = []
        if not bank_name:
            errors.append("Vui lòng chọn ngân hàng")
        
        # Nếu chọn "Ngân hàng khác" nhưng không nhập tên ngân hàng
        if bank_name == "Ngân hàng khác" and not other_bank_name:
            errors.append("Vui lòng nhập tên ngân hàng khác")
        
        if not account_name:
            errors.append("Vui lòng nhập tên chủ tài khoản")
        
        if not account_number:
            errors.append("Vui lòng nhập số tài khoản")
        elif not account_number.isdigit():
            errors.append("Số tài khoản chỉ được chứa các chữ số")
        
        # Kiểm tra xem số tài khoản đã tồn tại chưa (trừ tài khoản hiện tại)
        if account_number and BankAccount.objects.filter(user=request.user, account_number=account_number).exclude(id=pk).exists():
            errors.append("Số tài khoản này đã được đăng ký với tài khoản khác của bạn")
        
        # Nếu có lỗi, hiển thị thông báo lỗi
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Nếu đánh dấu là tài khoản mặc định, đặt tất cả các tài khoản khác là không mặc định
            if is_default:
                BankAccount.objects.filter(user=request.user).update(is_default=False)
            
            # Xử lý trường hợp ngân hàng khác
            final_bank_name = bank_name
            if bank_name == "Ngân hàng khác" and other_bank_name:
                final_bank_name = other_bank_name
            
            # Cập nhật tài khoản
            bank_account.bank_name = final_bank_name
            bank_account.account_name = account_name
            bank_account.account_number = account_number
            bank_account.branch = branch
            bank_account.is_default = is_default
            bank_account.save()
            
            messages.success(request, f'Đã cập nhật tài khoản ngân hàng {final_bank_name} - {account_number}')
            return redirect('bank_account_list')
    
    context = {
        'title': 'Cập nhật tài khoản ngân hàng',
        'bank_account': bank_account,
        'bank_accounts': BankAccount.objects.filter(user=request.user),
        'bank_choices': [
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
    }
    
    return render(request, 'portfolio/bank_account_form.html', context)

@login_required
def delete_bank_account(request, pk):
    """View để xóa tài khoản ngân hàng"""
    bank_account = get_object_or_404(BankAccount, id=pk, user=request.user)
    
    if request.method == 'POST':
        # Kiểm tra xem có giao dịch liên quan hay không
        has_related_transactions = BankTransaction.objects.filter(bank_account=bank_account, status='pending').exists()
        
        if has_related_transactions:
            messages.error(request, 'Không thể xóa tài khoản này vì có giao dịch đang xử lý.')
        else:
            # Lưu thông tin để hiển thị thông báo
            bank_name = bank_account.bank_name
            account_number = bank_account.account_number
            
            # Xóa tài khoản
            bank_account.delete()
            
            # Nếu không còn tài khoản nào, hoặc không còn tài khoản mặc định nào
            if bank_account.is_default:
                # Tìm tài khoản cũ nhất và đặt làm mặc định
                oldest_account = BankAccount.objects.filter(user=request.user).order_by('created_at').first()
                if oldest_account:
                    oldest_account.is_default = True
                    oldest_account.save()
            
            messages.success(request, f'Đã xóa tài khoản {bank_name} - {account_number}')
        
        return redirect('bank_account_list')
    
    context = {
        'bank_account': bank_account,
        'title': 'Xóa tài khoản ngân hàng'
    }
    
    return render(request, 'portfolio/bank_account_confirm_delete.html', context)

@login_required
def set_default_bank_account(request, pk):
    """View để đặt tài khoản ngân hàng mặc định"""
    bank_account = get_object_or_404(BankAccount, id=pk, user=request.user)
    
    if request.method == 'POST':
        # Đặt tất cả tài khoản khác thành không mặc định
        BankAccount.objects.filter(user=request.user).update(is_default=False)
        
        # Đặt tài khoản hiện tại thành mặc định
        bank_account.is_default = True
        bank_account.save()
        
        messages.success(request, f'Đã đặt tài khoản {bank_account.bank_name} - {bank_account.account_number} làm tài khoản mặc định')
    
    return redirect('bank_account_list')


# ============ MARKET =======
@login_required
def market(request):
    return render(request, 'portfolio/market.html')

# @api_view(['GET'])
def get_historical_data_api(request, stock_code):
    try:
        data = get_historical_data(stock_code)
        return JsonResponse({'data': data.to_dict('records')})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_stock_historical_data(request, symbol):
    try:
        # Lấy dữ liệu lịch sử từ vnstock service
        historical_data = get_historical_data(symbol)
        
        # Chuyển đổi dữ liệu thành định dạng phù hợp cho biểu đồ
        chart_data = []
        for _, row in historical_data.iterrows():
            chart_data.append({
                'time': row['time'].strftime('%Y-%m-%d') if hasattr(row['time'], 'strftime') else str(row['time']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            })
        
        print(f"Returning data for {symbol}: {len(chart_data)} records") # Debug log
        print(f"Sample data: {chart_data[:1]}") # Debug log để xem mẫu dữ liệu
        return JsonResponse(chart_data, safe=False)
    except Exception as e:
        print(f"Error getting data for {symbol}: {str(e)}") # Debug log
        print(f"Data structure: {historical_data.head()}") if 'historical_data' in locals() else print("No data fetched") # Debug log để xem cấu trúc dữ liệu
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def ai_chat_api(request):
    """
    API endpoint để xử lý các yêu cầu chat với AI
    """
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'Tin nhắn không được để trống'
            }, status=400)
        
        # Gọi API AI để nhận phản hồi
        response = get_ai_response(message)
        
        # Đơn giản hóa định dạng phản hồi và loại bỏ ký tự formatting
        response = response.strip()
        # Loại bỏ các ký tự đánh dấu in đậm và in nghiêng
        response = response.replace('**', '').replace('*', '')
        
        return JsonResponse({
            'success': True,
            'response': response
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dữ liệu JSON không hợp lệ'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# Debug view to directly test asset retrieval 
@login_required
def debug_assets(request):
    """Debug view to directly test asset retrieval"""
    # Get all assets
    all_assets = Asset.objects.all()
    
    # Create a simple context
    context = {
        'assets': all_assets,
        'assets_count': all_assets.count(),
        'portfolios': Portfolio.objects.filter(user=request.user),
    }
    
    # Log to console
    print(f"DEBUG: Found {all_assets.count()} assets in database")
    for asset in all_assets:
        print(f"  - Asset: {asset.id} | {asset.symbol} | {asset.name}")
    
    return render(request, 'portfolio/debug_assets.html', context)

@login_required
def sync_assets(request):
    """View to synchronize assets from VNStock to the database"""
    if request.method == 'POST' or request.method == 'GET':  # Allow both GET and POST
        try:
            result = sync_vnstock_to_assets()
            
            if isinstance(result, dict):
                messages.success(
                    request, 
                    f"Đồng bộ thành công! Đã thêm {result['created']} cổ phiếu mới, cập nhật {result['updated']} cổ phiếu. Bây giờ bạn có thể mua/bán những cổ phiếu này."
                )
            else:
                messages.error(request, "Đồng bộ không thành công, không có cổ phiếu nào được thêm.")
        except Exception as e:
            messages.error(request, f"Lỗi khi đồng bộ dữ liệu: {str(e)}")
    
    # Check if the request came from the market page
    referer = request.META.get('HTTP_REFERER', '')
    if 'market' in referer:
        return redirect('market')
    else:
        return redirect('debug_assets')

@login_required
def update_stock_prices(request):
    """View to update current stock prices"""
    if request.method == 'POST':
        try:
            # Call the function to fetch and update prices
            snapshot_df = fetch_stock_prices_snapshot()
            
            if snapshot_df is not None:
                # Count non-null prices
                non_null_prices = sum(1 for col in snapshot_df.columns if col != 'time' and snapshot_df[col].iloc[0] is not None)
                messages.success(
                    request, 
                    f"Cập nhật giá thành công! Đã cập nhật giá cho {non_null_prices} cổ phiếu."
                )
            else:
                messages.error(request, "Không thể cập nhật giá cổ phiếu.")
        except Exception as e:
            messages.error(request, f"Lỗi khi cập nhật giá: {str(e)}")
    
    return redirect('debug_assets')

@login_required
def get_stock_symbols(request):
    """API view để lấy danh sách mã cổ phiếu phù hợp với từ khóa tìm kiếm"""
    term = request.GET.get('term', '')
    
    # Sử dụng hàm vnstock để lấy danh sách cổ phiếu
    from .vnstock_services import get_all_stock_symbols
    
    try:
        # Lấy toàn bộ danh sách cổ phiếu
        all_symbols = get_all_stock_symbols()
        
        # Lọc theo từ khóa tìm kiếm - ưu tiên mã cổ phiếu khớp với từ khóa
        filtered_symbols = [item['ticker'] for item in all_symbols 
                           if term.upper() in item['ticker'].upper()][:10]
        
        # Nếu không đủ 10 kết quả, tìm thêm trong tên công ty
        if len(filtered_symbols) < 10 and term:
            remaining_slots = 10 - len(filtered_symbols)
            company_matches = [item['ticker'] for item in all_symbols 
                              if item['ticker'] not in filtered_symbols 
                              and term.upper() in item['organ_name'].upper()][:remaining_slots]
            filtered_symbols.extend(company_matches)
        
        return JsonResponse(filtered_symbols, safe=False)
    except Exception as e:
        print(f"Error in get_stock_symbols: {str(e)}")
        
        # Fallback to database search if vnstock fails
        assets = Asset.objects.filter(symbol__istartswith=term)[:10]
        symbols = [asset.symbol for asset in assets]
        
        return JsonResponse(symbols, safe=False)

@login_required
def get_stock_symbols_info(request):
    """API view để lấy thông tin tên công ty cho các mã cổ phiếu"""
    if request.method == 'POST':
        try:
            import json
            symbols_json = request.POST.get('symbols', '[]')
            symbols = json.loads(symbols_json)
            
            # Nếu không có mã cổ phiếu, trả về dict trống
            if not symbols:
                return JsonResponse({}, safe=False)
            
            # Lấy thông tin từ vnstock API
            from .vnstock_services import get_all_stock_symbols
            try:
                all_symbols = get_all_stock_symbols()
                # Tạo dict ánh xạ từ mã đến tên công ty
                symbol_info = {item['ticker']: item['organ_name'] for item in all_symbols 
                              if item['ticker'] in symbols}
                
                # Nếu thiếu symbol nào, bổ sung từ database
                missing_symbols = [symbol for symbol in symbols if symbol not in symbol_info]
                if missing_symbols:
                    assets = Assets.objects.filter(symbol__in=missing_symbols)
                    for asset in assets:
                        symbol_info[asset.symbol] = asset.name
                
                return JsonResponse(symbol_info, safe=False)
            except Exception as e:
                print(f"Error fetching company names from vnstock: {str(e)}")
                # Fallback to database
                assets = Assets.objects.filter(symbol__in=symbols)
                symbol_info = {asset.symbol: asset.name for asset in assets}
                return JsonResponse(symbol_info, safe=False)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def get_stock_price(request, symbol):
    """
    API endpoint để lấy giá cổ phiếu hiện tại và giá gợi ý mua/bán.
    """
    try:
        import random
        from .vnstock_services import get_current_bid_price, get_all_stock_symbols
        
        # Tìm asset hoặc tạo mới nếu chưa có
        asset = Assets.objects.filter(symbol=symbol).first()
        
        # Lấy giá từ vnstock theo hướng dẫn của người dùng
        current_bid = get_current_bid_price(symbol)
        
        if current_bid is not None:
            # Nếu lấy giá thành công từ API, sử dụng giá này
            match_price = float(current_bid)
            
            # Nếu asset chưa tồn tại, tạo mới
            if not asset:
                # Tìm thông tin công ty từ VNStock
                try:
                    print(f"DEBUG: Asset {symbol} not found in database, creating new asset")
                    all_symbols = get_all_stock_symbols()
                    company_info = next((item for item in all_symbols if item['ticker'] == symbol), None)
                    
                    if company_info:
                        company_name = company_info.get('organ_name', f"Công ty {symbol}")
                        # Tạo asset mới
                        asset = Assets(
                            symbol=symbol,
                            name=company_name,
                            type='stock',
                            sector='Unknown',
                            description=f"Auto-created from VNStock on {datetime.now().strftime('%Y-%m-%d')}",
                            current_price=match_price
                        )
                        asset.save()
                        print(f"DEBUG: Created new asset: {asset.id} - {asset.symbol} - {asset.name}")
                    else:
                        # Nếu không tìm thấy thông tin công ty, vẫn tạo Asset với thông tin tối thiểu
                        print(f"DEBUG: Company info for {symbol} not found in VNStock, creating minimal asset")
                        asset = Assets(
                            symbol=symbol,
                            name=f"Cổ phiếu {symbol}",
                            type='stock',
                            sector='Unknown',
                            description=f"Auto-created minimal asset on {datetime.now().strftime('%Y-%m-%d')}",
                            current_price=match_price
                        )
                        asset.save()
                        print(f"DEBUG: Created minimal asset: {asset.id} - {asset.symbol}")
                except Exception as e:
                    print(f"ERROR creating new asset: {str(e)}")
                    # Tạo asset đơn giản nhất có thể nếu có lỗi
                    try:
                        asset = Assets(
                            symbol=symbol,
                            name=f"Cổ phiếu {symbol}",
                            type='stock',
                            sector='Unknown',
                            description="Auto-created as fallback after error",
                            current_price=match_price
                        )
                        asset.save()
                        print(f"DEBUG: Created fallback asset after error: {asset.id} - {asset.symbol}")
                    except Exception as e2:
                        print(f"CRITICAL ERROR creating fallback asset: {str(e2)}")
            elif asset:
                # Cập nhật giá mới cho asset
                asset.current_price = match_price
                asset.save(update_fields=['current_price', 'last_updated'])
                print(f"DEBUG: Updated price for {symbol} to {match_price}")
            
            # Tạo giá trị giả lập cho biến động giá
            change_percent = random.uniform(-2, 2)
            
            # Tính giá mua/bán: giá mua thấp hơn 0.5%, giá bán cao hơn 0.5%
            buy_price = round(match_price * 0.995)
            sell_price = round(match_price * 1.005)
            
            # Chuẩn bị dữ liệu phản hồi
            response_data = {
                'success': True,
                'symbol': symbol,
                'price': match_price,
                'change_percent': change_percent,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'source': 'vnstock',
                'asset_exists': asset is not None,
                'asset_id': asset.id if asset else None,
                'asset_name': asset.name if asset else f"Cổ phiếu {symbol}"
            }
            
            # Trả về phản hồi JSON
            return JsonResponse(response_data)
        else:
            # Không lấy được giá từ API, tìm trong cơ sở dữ liệu
            asset = Assets.objects.filter(symbol=symbol).first()
            if asset:
                match_price = float(asset.current_price)
                change_percent = random.uniform(-2, 2)
                buy_price = round(match_price * 0.995)
                sell_price = round(match_price * 1.005)
                
                response_data = {
                    'success': True,
                    'symbol': symbol,
                    'price': match_price,
                    'change_percent': change_percent,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'source': 'database',
                    'asset_exists': True,
                    'asset_id': asset.id,
                    'asset_name': asset.name
                }
                return JsonResponse(response_data)
            else:
                # Tạo cổ phiếu mới với giá mặc định nếu không thể lấy từ API
                try:
                    default_price = 10000  # Giá mặc định
                    asset = Assets(
                        symbol=symbol,
                        name=f"Cổ phiếu {symbol}",
                        type='stock',
                        sector='Unknown',
                        description=f"Auto-created with default price on {datetime.now().strftime('%Y-%m-%d')}",
                        current_price=default_price
                    )
                    asset.save()
                    print(f"DEBUG: Created new asset with default price: {asset.id} - {asset.symbol}")
                    
                    response_data = {
                        'success': True,
                        'symbol': symbol,
                        'price': default_price,
                        'change_percent': 0,
                        'buy_price': round(default_price * 0.995),
                        'sell_price': round(default_price * 1.005),
                        'source': 'default',
                        'asset_exists': True,
                        'asset_id': asset.id,
                        'asset_name': asset.name
                    }
                    return JsonResponse(response_data)
                except Exception as e:
                    print(f"ERROR creating new asset with default price: {str(e)}")
                    # Không tìm thấy cổ phiếu trong cơ sở dữ liệu và không thể tạo mới
                    return JsonResponse({
                        'success': False,
                        'error': f'Không tìm thấy mã cổ phiếu {symbol} và không thể tạo mới'
                    }, status=404)
    except Exception as e:
        print(f"ERROR in get_stock_price: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Lỗi khi xử lý thông tin cổ phiếu: {str(e)}'
        }, status=500)

@login_required
def create_asset_from_symbol(request):
    """
    API endpoint để tạo mới hoặc cập nhật asset từ mã cổ phiếu
    """
    if request.method == 'POST':
        try:
            symbol = request.POST.get('symbol')
            if not symbol:
                return JsonResponse({'success': False, 'error': 'Thiếu mã cổ phiếu'}, status=400)
            
            from .vnstock_services import get_current_bid_price, get_all_stock_symbols
            
            # Kiểm tra xem asset đã tồn tại chưa
            asset = Assets.objects.filter(symbol=symbol).first()
            
            # Nếu đã tồn tại thì cập nhật giá
            if asset:
                # Lấy giá hiện tại từ API
                current_price = get_current_bid_price(symbol)
                if current_price is not None:
                    asset.current_price = float(current_price)
                    asset.save(update_fields=['current_price', 'last_updated'])
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Đã cập nhật giá cho {symbol}',
                        'asset_id': asset.id,
                        'asset_name': asset.name,
                        'price': float(asset.current_price),
                        'created': False,
                        'updated': True
                    })
                else:
                    return JsonResponse({
                        'success': True,
                        'message': f'Không lấy được giá mới cho {symbol}, giữ nguyên giá cũ',
                        'asset_id': asset.id,
                        'asset_name': asset.name,
                        'price': float(asset.current_price),
                        'created': False,
                        'updated': False
                    })
            
            # Nếu chưa tồn tại, tạo mới
            # Lấy giá hiện tại
            current_price = get_current_bid_price(symbol)
            if current_price is None:
                current_price = 10000  # Giá mặc định nếu không lấy được
            
            # Lấy thông tin công ty
            company_name = f"Cổ phiếu {symbol}"
            try:
                all_symbols = get_all_stock_symbols()
                company_info = next((item for item in all_symbols if item['ticker'] == symbol), None)
                if company_info:
                    company_name = company_info.get('organ_name', company_name)
            except Exception as e:
                print(f"ERROR getting company info for {symbol}: {str(e)}")
            
            # Tạo asset mới
            new_asset = Assets(
                symbol=symbol,
                name=company_name,
                type='stock',
                sector='Unknown',
                description=f"Auto-created via API on {datetime.now().strftime('%Y-%m-%d')}",
                current_price=current_price
            )
            new_asset.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Đã tạo mới cổ phiếu {symbol}',
                'asset_id': new_asset.id,
                'asset_name': new_asset.name,
                'price': float(new_asset.current_price),
                'created': True,
                'updated': False
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Lỗi: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Chỉ hỗ trợ phương thức POST'}, status=405)




# ============ API =======
from rest_framework.decorators import api_view
@api_view(['GET'])
def get_price_board_api(request):
    """
    API endpoint để lấy bảng giá cổ phiếu
    """
    try:
        price_board = get_price_board()
        if price_board.empty:
            raise ValueError("Bảng giá trống")
        
        # Chuyển đổi DataFrame thành JSON
        price_board_json = price_board.to_json(orient='records')
        
        return JsonResponse({'data': json.loads(price_board_json)}, safe=False)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# API lấy giá cổ phiếu hiện tại theo mã
@api_view(['GET'])
def get_current_price_symbol_api(request):
    """
    API endpoint để lấy giá cổ phiếu hiện tại
    """
    try:
        if request.method == 'GET':
            symbol = request.GET.get('symbol')
            # print('='*100)
            # print(symbol)
            price_df = get_current_price(symbol)
            # print(price_df)
            price = float(price_df.iloc[0,1])
            # print(price)
            if price is None:
                raise ValueError("Không tìm thấy giá cổ phiếu")
            return JsonResponse({'symbol': symbol, 'price': price}, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)