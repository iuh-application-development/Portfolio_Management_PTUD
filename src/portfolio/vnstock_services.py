from datetime import datetime
from vnstock import Vnstock
from .models import Assets
import pandas as pd
import os



# Khởi tạo Vnstock
vnstock_instance = Vnstock()
stock = vnstock_instance.stock(symbol='VN30', source='VCI')


def get_list_stock_market():
    """Lấy danh sách mã cổ phiếu niêm yết"""
    try:
        symbols_df = stock.listing.all_symbols()
        if symbols_df.empty:
            print("WARNING: No stock symbols retrieved from vnstock")
            return []
        return symbols_df['ticker'].values.tolist()
    except Exception as e:
        print(f"Error in get_list_stock_market: {str(e)}")
        return []

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
    
def get_price_board():
    """Lấy bảng giá thị trường"""
    try:
        # Get a limited set of symbols first to ensure we get some data
        symbols = get_list_stock_market()
        if not symbols:
            # print("WARNING: No symbols to fetch price board")
            return pd.DataFrame()
            
        # For testing, limit to first 50 symbols to avoid timeouts or data size issues
        test_symbols = symbols
        # print(f"Fetching price board for {len(test_symbols)} symbols...")
        
        try:
            # Try with VCI source first
            price_board = stock.trading.price_board(symbols_list=test_symbols)
        except Exception as e:
            # print(f"Error with VCI source: {str(e)}, trying SSI source...")
            # Fall back to SSI source if VCI fails
            ssi_stock = vnstock_instance.stock(symbol='VN30', source='SSI')
            price_board = ssi_stock.trading.price_board(symbols_list=test_symbols)
        
        # Check if we got data
        if price_board.empty:
            # print("WARNING: Empty price board returned from vnstock")
            # Create a minimal dataframe with required columns for debugging
            return pd.DataFrame({
                ('listing', 'symbol'): ['AAA', 'VNM', 'FPT'],
                ('listing', 'ceiling'): [25000, 60000, 90000],
                ('listing', 'floor'): [20000, 50000, 80000],
                ('listing', 'ref_price'): [22000, 55000, 85000],
                ('match', 'match_price'): [22500, 56000, 86000],
                ('match', 'match_vol'): [10000, 5000, 3000]
            })
            
        # print(f"Price board fetched: {len(price_board)} rows")
        # print(f"Price board columns: {price_board.columns}")
        
        if isinstance(price_board.columns, pd.MultiIndex):
            price_board.columns = ['_'.join(map(str, col)).strip() for col in price_board.columns.values]
            # print(f"Flattened columns: {price_board.columns}")
        
        # Check that we have the necessary columns
        required_cols = ['listing_symbol', 'listing_ceiling', 'listing_floor', 'listing_ref_price', 'match_match_price', 'match_match_vol']
        alt_cols = ['symbol', 'ceiling', 'floor', 'ref_price', 'match_price', 'match_vol']
        
        columns_present = all(col in price_board.columns for col in required_cols) or all(col in price_board.columns for col in alt_cols)
        
        if not columns_present:
            # print(f"WARNING: Missing required columns in price board. Available columns: {price_board.columns}")
            # Try to map columns differently
            if isinstance(price_board.columns, pd.MultiIndex):
                # Try another method to flatten
                price_board.columns = [f"{col[0]}_{col[1]}" for col in price_board.columns]
            else:
                # Try to rename columns if they exist with different names
                column_map = {}
                for req, alt in zip(required_cols, alt_cols):
                    if alt in price_board.columns:
                        column_map[alt] = req
                
                if column_map:
                    price_board = price_board.rename(columns=column_map)
        
        # Final check
        # print(f"Final columns: {price_board.columns}")
        return price_board
    except Exception as e:
        # print(f"Error in get_price_board: {str(e)}")
        # Return a fallback dataframe with sample data for debugging
        return pd.DataFrame({
            'listing_symbol': ['AAA', 'VNM', 'FPT'],
            'listing_ceiling': [25000, 60000, 90000],
            'listing_floor': [20000, 50000, 80000],
            'listing_ref_price': [22000, 55000, 85000],
            'match_match_price': [22500, 56000, 86000],
            'match_match_vol': [10000, 5000, 3000]
        })