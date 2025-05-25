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
    """Lấy mã cổ phiếu và tên công ty"""
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
    """Lấy giá tên công ty
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
    """Lấy giá tham chiếu của cổ phiếu
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

def get_refer_price(stock_code):
    """Lấy giá tham chiếu của cổ phiếu"""
    try:
        data = stock.trading.price_board(symbols_list=[stock_code])
        if data.empty:
            return f'Không tìm thấy mã cổ phiếu {stock_code}!'
        ref_price = int(data[('listing', 'ref_price')].iloc[0])
        return ref_price
    except Exception as e:
        print(f"Error in get_refer_price for {stock_code}: {str(e)}")
        return f'Không tìm thấy mã cổ phiếu {stock_code}!'

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

def get_historical_data(symbol):
    """Lấy giá lịch sử của cổ phiếu"""
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

def sync_vnstock_to_assets():
    """Đồng bộ dữ liệu từ vnstock vào model Asset"""
    try:
        symbols_df = stock.listing.all_symbols()
        if symbols_df.empty:
            print("ERROR: No stock symbols retrieved from vnstock")
            return {'created': 0, 'updated': 0, 'errors': 0, 'total': 0}

        print(f"Found {len(symbols_df)} stocks in VNStock")
        symbols = symbols_df['ticker'].tolist()  # Lấy tất cả mã, không giới hạn 20

        # Lấy bảng giá
        price_board = stock.trading.price_board(symbols_list=symbols)
        if isinstance(price_board.columns, pd.MultiIndex):
            price_board.columns = ['_'.join(map(str, col)).strip() for col in price_board.columns.values]

        created_count = 0
        updated_count = 0
        error_count = 0

        for symbol in symbols:
            try:
                symbol_info = symbols_df[symbols_df['ticker'] == symbol].iloc[0]
                price_row = price_board[price_board['listing_symbol'] == symbol]
                current_price = price_row['match_match_price'].values[0] if not price_row.empty and 'match_match_price' in price_board.columns else 10000

                asset, created = Assets.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        'name': symbol_info['organ_name'],
                        'type': 'stock',
                        'sector': symbol_info.get('industry_name', 'Unknown'),
                        'current_price': current_price,
                        'description': f"Imported from VNStock on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                )
                if created:
                    created_count += 1
                    print(f"Created asset: {symbol} - {symbol_info['organ_name']}")
                else:
                    updated_count += 1
                    print(f"Updated asset: {symbol} - {symbol_info['organ_name']}")
            except Exception as e:
                error_count += 1
                print(f"Error processing {symbol}: {str(e)}")

        return {
            'created': created_count,
            'updated': updated_count,
            'errors': error_count,
            'total': created_count + updated_count
        }
    except Exception as e:
        print(f"Error syncing VNStock data: {str(e)}")
        return {'created': 0, 'updated': 0, 'errors': 1, 'total': 0}

def get_current_bid_price(symbol):
    """Lấy giá mua (bid) hiện tại của một mã cổ phiếu."""
    try:
        print(f"DEBUG: Getting price for symbol {symbol}")
        # Sử dụng Vnstock instance đã có
        price_board = stock.trading.price_board(symbols_list=[symbol])
        
        if isinstance(price_board.columns, pd.MultiIndex):
            # Nếu đầu ra là MultiIndex columns
            try:
                price = price_board[('match', 'match_price')].iloc[0]
                print(f"DEBUG: Found price with ('match', 'match_price'): {price}")
                return price
            except:
                # Thử các tên cột khác nếu không tìm thấy
                for col_pair in [('match', 'price'), ('price', 'price'), ('trade', 'price')]:
                    try:
                        price = price_board[col_pair].iloc[0]
                        print(f"DEBUG: Found price with {col_pair}: {price}")
                        return price
                    except:
                        continue
                # Nếu không tìm được, chuyển đổi columns và thử lại
                price_board.columns = ['_'.join(map(str, col)).strip() for col in price_board.columns.values]
                print(f"DEBUG: Converted columns to: {price_board.columns}")
        
        # Chọn cột giá phù hợp
        for col in ['match_match_price', 'match_price', 'price']:
            if col in price_board.columns:
                price = price_board[col].iloc[0]
                print(f"DEBUG: Found price with {col}: {price}")
                return price
        
        # Nếu không tìm thấy cột giá
        print(f"Warning: Could not find price column for {symbol}. Available columns: {price_board.columns}")
        return None
    except Exception as e:
        print(f"Error in get_current_bid_price for {symbol}: {str(e)}")
        return None

def get_all_stock_symbols():
    """Lấy danh sách mã cổ phiếu và tên công ty dựa theo yêu cầu người dùng"""
    try:
        print("DEBUG: Getting all stock symbols from VNStock")
        # Sử dụng code chính xác từ hướng dẫn
        symbols_data = Vnstock().stock(symbol='VN30', source='VCI').listing.all_symbols().values
        
        # Debug the shape of data
        print(f"DEBUG: Got {len(symbols_data)} symbols, first 3: {symbols_data[:3]}")
        
        # Chuyển đổi thành định dạng dễ sử dụng hơn
        symbols = []
        for item in symbols_data:
            symbols.append({
                'ticker': item[0],
                'organ_name': item[1]
            })
        
        return symbols
    except Exception as e:
        print(f"Error in get_all_stock_symbols: {str(e)}")
        return []

def fetch_stock_prices_snapshot(output_file=None):
    """Lấy snapshot giá cổ phiếu hiện tại"""
    try:
        symbols_df = stock.listing.all_symbols()
        if symbols_df.empty:
            print("ERROR: No stock symbols retrieved")
            return None
        symbols = symbols_df['ticker'].tolist()

        print(f"Fetching prices for {len(symbols)} symbols...")
        price_board = stock.trading.price_board(symbols_list=symbols)
        if isinstance(price_board.columns, pd.MultiIndex):
            price_board.columns = ['_'.join(map(str, col)).strip() for col in price_board.columns.values]

        price_column = None
        for col in ['match_match_price', 'match_price', 'price', 'trading_match_price', 'listing_reference_price']:
            if col in price_board.columns:
                price_column = col
                break
        if not price_column:
            price_cols = [col for col in price_board.columns if 'price' in col.lower()]
            price_column = price_cols[0] if price_cols else None
        if not price_column:
            raise ValueError("Could not find price column in price board data")

        symbol_column = None
        for col in ['listing_symbol', 'symbol', 'ticker']:
            if col in price_board.columns:
                symbol_column = col
                break
        if not symbol_column:
            raise ValueError("Could not find symbol column in price board data")

        snapshot = {'time': datetime.now().isoformat()}
        for symbol in symbols:
            try:
                row = price_board[price_board[symbol_column] == symbol]
                snapshot[symbol] = float(row[price_column].values[0]) if not row.empty and pd.notnull(row[price_column].values[0]) else None
            except Exception as e:
                print(f"Error getting price for {symbol}: {str(e)}")
                snapshot[symbol] = None

        snapshot_df = pd.DataFrame([snapshot])
        update_count = 0
        for symbol, price in snapshot.items():
            if symbol != 'time' and price is not None:
                try:
                    asset = Assets.objects.filter(symbol=symbol).first()
                    if asset:
                        asset.current_price = price
                        asset.save(update_fields=['current_price'])
                        update_count += 1
                except Exception as e:
                    print(f"Error updating asset {symbol}: {str(e)}")

        print(f"Updated prices for {update_count} assets in the database")
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            snapshot_df.to_csv(output_file, mode='a', header=not os.path.exists(output_file), index=False)
            print(f"Saved data to {output_file}")
            return None
        return snapshot_df
    except Exception as e:
        print(f"Error in fetch_stock_prices_snapshot: {str(e)}")
        return None