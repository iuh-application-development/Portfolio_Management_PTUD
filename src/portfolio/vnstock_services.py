from datetime import datetime
from vnstock import Vnstock
from .models import Assets
import pandas as pd
import os



# Khởi tạo Vnstock
vnstock_instance = Vnstock()
stock = vnstock_instance.stock(symbol='VN30', source='VCI')


def get_ticker_companyname():
    """Lấy mã cổ phiếu và tên công ty
        return :
            DataFrame: 'ticker', 'organ_name'
    """
    try:
        symbols_df = stock.listing.all_symbols()
        if symbols_df.empty:
            print("WARNING: No stock data in get_ticker_companyname")
            return []
        return [
            {"ticker": row[0], "organ_name": row[1]}
            for row in symbols_df.itertuples(index=False, name=None)
        ]
    except Exception as e:
        print(f"Error in get_ticker_companyname: {str(e)}")
        return []
    
def get_company_name(stock_codes):
    """Lấy giá tên công ty theo mã
        Param :
            stock_codes: là một list hoặc một chuỗi
        return :
            DataFrame: 'ticker', 'organ_name'
    """
    try:
        if not isinstance(stock_codes, list):
            stock_codes = list(stock_codes)
        symbols_df = stock.listing.all_symbols()
        company_names = symbols_df[symbols_df['ticker'].isin(stock_codes)]
        return company_names
    except Exception as e:
        print(f"Error in get company name.")
        return f'Lỗi lấy dữ liệu!'

def get_current_price(stock_code):
    """Lấy giá hiện tại
        Param :
            stock_code: là một list hoặc một chuỗi
        return :
            DataFrame: 'ticker', 'price'
    """
    try:
        if not isinstance(stock_code, list):
            stock_code = stock_code.split()
        data_board = stock.trading.price_board(symbols_list=stock_code)
        data = data_board[[('listing', 'symbol'), 
                        ('listing', 'ref_price'), 
                        ('match', 'match_price')]]
        if data.empty:
            return f'Không tìm thấy giá!'
        data.columns = ['symbol', 'ref_price', 'match_price']
        data.loc[data['match_price'] != 0, 'ref_price'] = data['match_price']
        data_price = data[['symbol', 'ref_price', 'match_price']]
        return data_price
    except Exception as e:
        print(f"Error in get current price.")
        return f'Lỗi! '

def get_historical_data(symbol):
    """Lấy giá lịch sử của cổ phiếu
    Args:
        symbol (str): Mã cổ phiếu cần lấy dữ liệu lịch sử.
    Returns:
        DataFrame: 'time', 'open', 'high', 'low', 'close', 'volume'.
    """
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        data = stock.quote.history(symbol=symbol, start='2000-01-01', end=today)
        if 'time' not in data.columns and data.index.name != 'time':
            data = data.reset_index().rename(columns={'index': 'time'})
        print(f"Data columns for {symbol}: {data.columns}")
        print(f"Sample data:\n{data.head()}")
        return data
    except Exception as e:
        print(f"Error in get_historical_data for {symbol}: {str(e)}")
        raise Exception(f"Không thể lấy dữ liệu lịch sử cho mã {symbol}: {str(e)}")
    
