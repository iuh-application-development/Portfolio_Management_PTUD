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
from .vnstock_services import (
    get_historical_data, get_ticker_companyname, get_current_price, get_company_name, get_price_board
)
from .utils import get_ai_response, get_auth0_user_profile, generate_qr_code, check_paid

import uuid
import requests
from decimal import Decimal, InvalidOperation
from urllib.parse import quote_plus, urlencode
import json
import pandas as pd
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
    if list_stock:
        current_price_symbol = get_current_price(list_stock)
        # current_price_symbol = get_current_price(list_stock).set_index('symbol')['ref_price'].to_dict()
        total_assets_value = 0
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
    else:
        total_profit_loss = 0
        total_profit_loss_percentage = 0

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


@login_required
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
        stock.profit_loss = (stock.current_price - stock.average_price) * stock.quantity
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
    return render(request, 'portfolio/stock_transaction.html', context)
    # return render(request, 'portfolio/stock_transaction.html')


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
                # Cập nhật số dư ví
                Wallet.objects.filter(user=user).update(balance=F('balance') - total_buy_price)

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
    return render(request, 'portfolio/stock_transaction.html', context)
    # return render(request, 'portfolio/portfolio_transactions.html')


@login_required
def wallet(request):
    user = request.user
    # user = User.objects.get(pk=1)
    user_wallet = Wallet.objects.get(user=user)
    user_balance = user_wallet.balance
    user_bank_accounts = BankAccount.objects.filter(user=user).order_by('-is_default', '-created_at')[:5]
    context = {
        "user_balance": user_balance,
        "user_bank_accounts": user_bank_accounts,
    }
    
    return render(request, 'portfolio/wallet.html', context)

@login_required
def deposit_money(request):
    user_bank_accounts = BankAccount.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    wallet = Wallet.objects.get(user=request.user)

    # Giá trị mặc định ban đầu khi vào trang (GET request)
    initial_transaction_id = f"DEP{uuid.uuid4().hex[:8].upper()}"
    initial_amount = Decimal('100000')

    context = {
        "user_bank_accounts": user_bank_accounts,
        "current_page": "deposit_money",
        "transaction_id": initial_transaction_id,
        "amount_to_deposit": initial_amount,
        "qr_code_url": generate_qr_code(amount=initial_amount, transaction_id=initial_transaction_id, username=request.user.username)
    }

    if request.method == 'POST':
        # Lấy transaction_id và amount từ POST. Đây là các giá trị mà người dùng đã thấy và có thể đã sử dụng.
        tid_from_form = request.POST.get('transaction_id')
        amount_str_from_form = request.POST.get('amount')

        if not tid_from_form or not amount_str_from_form:
            messages.error(request, "Thiếu thông tin mã giao dịch hoặc số tiền. Vui lòng thử lại.")
            # Render lại với context hiện tại (có thể là giá trị GET ban đầu hoặc giá trị từ lần POST trước đó không thành công)
            # Nếu POST thiếu dữ liệu, context['transaction_id'] và context['amount_to_deposit'] sẽ giữ giá trị từ GET.
            # Hoặc nếu đây là POST thứ N, chúng sẽ là giá trị từ POST thứ N-1 đã được gán vào context.
            context['qr_code_url'] = generate_qr_code(amount=context['amount_to_deposit'], transaction_id=context['transaction_id'], username=request.user.username)
            return render(request, 'portfolio/deposit.html', context)

        try:
            amount_from_form = Decimal(amount_str_from_form)
            if amount_from_form < 50000:
                messages.error(request, "Số tiền nạp tối thiểu là 50,000 VNĐ.")
                # Cập nhật context với giá trị người dùng vừa nhập để hiển thị lại
                context['transaction_id'] = tid_from_form 
                context['amount_to_deposit'] = amount_from_form
                context['qr_code_url'] = generate_qr_code(amount=amount_from_form, transaction_id=tid_from_form, username=request.user.username)
                return render(request, 'portfolio/deposit.html', context)
        except (ValueError, TypeError):
            messages.error(request, "Số tiền không hợp lệ.")
            context['transaction_id'] = tid_from_form 
            context['amount_to_deposit'] = initial_amount # Fallback nếu số tiền nhập lỗi
            context['qr_code_url'] = generate_qr_code(amount=context['amount_to_deposit'], transaction_id=tid_from_form, username=request.user.username)
            return render(request, 'portfolio/deposit.html', context)

        # Cập nhật context với giá trị từ form cho các lần render tiếp theo (nếu có)
        context['transaction_id'] = tid_from_form
        context['amount_to_deposit'] = amount_from_form
        
        if 'confirm_transfer' in request.POST:
            # Người dùng nhấn nút xác nhận cuối cùng
            print(f"[DEBUG] Finalizing deposit. TID from POST: {tid_from_form}, Amount from POST: {amount_from_form}, User: {request.user.username}")

            if BankTransaction.objects.filter(description__startswith=tid_from_form, status='completed', user=request.user).exists():
                messages.info(request, f"Giao dịch với mã {tid_from_form} đã được hệ thống xác nhận trước đó.")
                return redirect('wallet')

            google_apps_script_url = "https://script.google.com/macros/s/AKfycbzKZpHfNxncQvpuVzqGyXTc5Jf2_rLcA8zo99oH2w0QADShVbHa848L3wjVkIVSudsn/exec"
            found_matching_transaction_in_bank = False
            try:
                response = requests.get(google_apps_script_url, timeout=15) # Tăng timeout
                response.raise_for_status()
                bank_transactions_data = response.json()

                if bank_transactions_data.get("error") or not bank_transactions_data.get("data"):
                    messages.error(request, "Dịch vụ ngân hàng không trả về dữ liệu giao dịch hợp lệ hoặc báo lỗi.")
                else:
                    for bank_tran in bank_transactions_data["data"]:
                        description_from_bank = bank_tran.get("Mô tả", "")
                        amount_from_bank_str = str(bank_tran.get("Giá trị", "0"))
                        
                        # Kiểm tra kỹ hơn dữ liệu từ bank
                        if not description_from_bank or not amount_from_bank_str:
                            print(f"[DEBUG] Skipping bank transaction due to missing description or amount: {bank_tran}")
                            continue
                        try:    
                            bank_amount = Decimal(amount_from_bank_str)
                        except ValueError:
                            print(f"[DEBUG] Skipping bank transaction due to invalid amount: {bank_tran}")
                            continue

                        # Logic trích xuất thông tin từ "Mô tả" của ngân hàng: "MãGD SốTiền TênUser ..."
                        # Ví dụ: "DEPXXXXX 100000 username123 ..."
                        desc_parts = str(description_from_bank).strip().split() # Ép kiểu thành chuỗi để tránh lỗi
                        if len(desc_parts) >= 3: # Cần ít nhất Mã GD, Số tiền, Tên User
                            bank_tid_candidate = desc_parts[0]
                            bank_amount_candidate_str = desc_parts[1]
                            bank_username_candidate = desc_parts[2]
                            
                            try:
                                bank_amount_in_desc = Decimal(bank_amount_candidate_str)
                            except (ValueError, InvalidOperation):
                                print(f"[DEBUG] Invalid amount in bank description, skipping: {description_from_bank}")
                                continue

                            print(f"[DEBUG] Comparing: Form TID({tid_from_form}) vs BankTID({bank_tid_candidate}), Form Amount({amount_from_form}) vs BankAmountInDesc({bank_amount_in_desc}), Form User({request.user.username}) vs BankUser({bank_username_candidate})")
                            print(f"[DEBUG] Also checking Form Amount({amount_from_form}) vs BankAmountFromJson({bank_amount})")


                            # Điều kiện khớp:
                            # 1. Mã giao dịch trong mô tả của bank PHẢI khớp với tid_from_form
                            # 2. Số tiền trong mô tả của bank PHẢI khớp với amount_from_form
                            # 3. Tên user trong mô tả của bank PHẢI khớp với request.user.username
                            # 4. Số tiền "Giá trị" từ JSON của bank PHẢI khớp với amount_from_form (kiểm tra chéo)
                            if (bank_tid_candidate == tid_from_form and 
                                bank_amount_in_desc == amount_from_form and 
                                bank_username_candidate == request.user.username and
                                bank_amount == amount_from_form):
                                found_matching_transaction_in_bank = True
                                internal_description = f"{tid_from_form} {int(amount_from_form)} {request.user.username}"
                                try:
                                    with transaction.atomic():
                                        BankTransaction.objects.create(
                                            user=request.user,
                                            type='deposit',
                                            quantity=amount_from_form, 
                                            status='completed',
                                            description=internal_description, # Sử dụng mô tả đã chuẩn hóa
                                            transaction_time=timezone.now(),
                                            completed_at=timezone.now(),
                                            fee=Decimal('0')
                                        )
                                        wallet.balance = F('balance') + amount_from_form # Sử dụng F expression
                                        wallet.save(update_fields=['balance'])
                                        wallet.refresh_from_db() # Đảm bảo đọc giá trị mới nhất
                                    messages.success(request, f"Nạp tiền thành công {amount_from_form:,.0f} VNĐ vào ví của bạn! Số dư mới: {wallet.balance:,.0f} VNĐ.")
                                    return redirect('wallet')
                                except Exception as e:
                                    messages.error(request, f"Lỗi khi xử lý giao dịch nội bộ: {str(e)}")
                                    print(f"[ERROR] Internal transaction processing error: {e}")
                                break # Đã tìm thấy và xử lý, thoát vòng lặp
            except requests.exceptions.RequestException as e:
                messages.error(request, f"Lỗi khi kết nối đến dịch vụ ngân hàng: {str(e)}")
                print(f"[ERROR] Bank service connection error: {e}")
            except ValueError as e: # Lỗi JSONDecodeError hoặc khi convert Decimal
                messages.error(request, f"Lỗi khi đọc dữ liệu từ dịch vụ ngân hàng: {str(e)}")
                print(f"[ERROR] Bank data processing error: {e}")
                # Log a nội dung phản hồi không phải JSON
                if 'response' in locals() and hasattr(response, 'text'):
                    print(f"[DEBUG] Non-JSON response from bank service: {response.text[:500]}") # Log 500 ký tự đầu

            if not found_matching_transaction_in_bank and not messages.get_messages(request): # Chỉ thêm message nếu chưa có lỗi nào khác
                messages.error(request, "Không tìm thấy giao dịch chuyển khoản nào khớp với yêu cầu của bạn trong dữ liệu ngân hàng hoặc giao dịch đã được xử lý. Vui lòng thử lại sau vài phút hoặc kiểm tra lại thông tin chuyển khoản.")
            
            # Nếu không redirect sau khi xác nhận (do lỗi hoặc không tìm thấy), render lại trang với QR hiện tại
            context['qr_code_url'] = generate_qr_code(amount=amount_from_form, transaction_id=tid_from_form, username=request.user.username)
            print(f"[DEBUG] Rendering deposit page after confirm_transfer logic. TID: {tid_from_form}, Amount: {amount_from_form}")
            return render(request, 'portfolio/deposit.html', context)
        else:
            # Không phải 'confirm_transfer', chỉ là cập nhật số tiền/QR
            # Mã QR sẽ được tạo với tid_from_form và amount_from_form
            context['qr_code_url'] = generate_qr_code(amount=amount_from_form, transaction_id=tid_from_form, username=request.user.username)
            print(f"[DEBUG] Rendering deposit page after amount update (not confirm). TID: {tid_from_form}, Amount: {amount_from_form}")
            return render(request, 'portfolio/deposit.html', context)

    # Request method is GET
    print(f"[DEBUG] Rendering deposit page for GET. TID: {context['transaction_id']}, Amount: {context['amount_to_deposit']}")
    return render(request, 'portfolio/deposit.html', context)

# Loại bỏ hàm verify_deposit
# @login_required
# def verify_deposit(request, transaction_id=None):
#     """View to verify deposit transactions"""
#     if request.method != 'POST':
#         messages.success(request, "Xác nhận nạp tiền thành công! Số dư của bạn đã được cập nhật.")
#         return redirect('deposit_money')
#     
#     # Just show success message and redirect
#     return redirect('wallet')

# @login_required
def withdraw_money(request):
    user = request.user
    user_balance = Wallet.objects.get(user=user).balance
    user_bank_accounts = BankAccount.objects.filter(user=user).order_by('-is_default', '-created_at')
    context = {
        "user_balance": user_balance,
        "user_bank_accounts" : user_bank_accounts,
    }
    return render(request, 'portfolio/withdraw.html', context)

@login_required
def wallet_transactions(request):
    user = request.user
    bank_transactions = BankTransaction.objects.filter(user=user).order_by('-transaction_time')
    context = {
        'bank_transactions': bank_transactions,
    }
    return render(request, 'portfolio/wallet_transactions.html', context)


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
        if bank_name == "orther":
            if not other_bank_name:
                errors.append("Vui lòng nhập tên ngân hàng khác")
            else:
                bank_name = other_bank_name
        
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
        redirect_url = request.POST.get('redirect_url', 'deposit_money')
        print(redirect_url)
        return redirect(redirect_url)

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


# ============ API =======
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


from rest_framework.decorators import api_view

# lấy bảng giá cổ phiếu
@api_view(['GET'])
@login_required
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
@login_required
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
    

# lấy dữ liệu lịch sử vẽ biểu đồ giá
@login_required
@api_view(['GET'])
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