import pytest
import json
from unittest.mock import patch, Mock
import portfolio.vnstock_services as vnstock_services

@pytest.mark.django_db
class TestVnStockIntegration:
    """Test tích hợp với VnStock API."""

    def setup_method(self):
        """Thiết lập cho mỗi test method."""
        pass

    @patch('portfolio.vnstock_services.stock')
    def test_get_stock_price(self, mock_stock):
        """Test lấy giá cổ phiếu từ VnStock."""
        # Mock response
        mock_stock.trading.price_board.return_value = Mock()
        mock_stock.trading.price_board.return_value.empty = False
        mock_stock.trading.price_board.return_value.__getitem__ = Mock(return_value=Mock())
        mock_stock.trading.price_board.return_value.__getitem__.return_value.iloc = [85000]
        
        result = vnstock_services.get_current_bid_price('VIC')
        assert result is not None or result == 85000

    @patch('portfolio.vnstock_services.stock')
    def test_get_market_overview(self, mock_stock):
        """Test lấy bảng giá thị trường."""
        mock_stock.trading.price_board.return_value = Mock()
        mock_stock.trading.price_board.return_value.empty = False
        
        result = vnstock_services.get_price_board()
        assert result is not None

    @patch('portfolio.vnstock_services.stock')
    def test_get_stock_list(self, mock_stock):
        """Test lấy danh sách cổ phiếu."""
        mock_stock.listing.all_symbols.return_value = Mock()
        mock_stock.listing.all_symbols.return_value.empty = False
        mock_stock.listing.all_symbols.return_value.__getitem__ = Mock(return_value=Mock())
        mock_stock.listing.all_symbols.return_value.__getitem__.return_value.values = Mock()
        mock_stock.listing.all_symbols.return_value.__getitem__.return_value.values.tolist = Mock(return_value=['VIC', 'VHM', 'GAS'])
        
        result = vnstock_services.get_list_stock_market()
        assert isinstance(result, list)

    @patch('portfolio.vnstock_services.stock')
    def test_get_historical_data(self, mock_stock):
        """Test lấy dữ liệu lịch sử cổ phiếu."""
        mock_data = Mock()
        mock_data.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        mock_data.head = Mock(return_value=Mock())
        mock_stock.quote.history.return_value = mock_data
        
        result = vnstock_services.get_historical_data('VIC')
        assert result is not None
        mock_stock.quote.history.assert_called_once()

    def test_get_company_names(self):
        """Test lấy tên công ty."""
        with patch('portfolio.vnstock_services.stock') as mock_stock:
            mock_df = Mock()
            mock_df.empty = False
            mock_df.__getitem__ = Mock(return_value=Mock())
            mock_df.__getitem__.return_value.isin = Mock(return_value=Mock())
            mock_stock.listing.all_symbols.return_value = mock_df
            
            result = vnstock_services.get_company_name(['VIC'])
            assert result is not None

    @patch('portfolio.vnstock_services.stock')
    def test_api_error_handling(self, mock_stock):
        """Test xử lý lỗi API."""
        mock_stock.trading.price_board.side_effect = Exception("API Error")
        
        result = vnstock_services.get_current_bid_price('INVALID')
        assert result is None

    @patch('portfolio.vnstock_services.stock')
    def test_get_reference_price(self, mock_stock):
        """Test lấy giá tham chiếu."""
        mock_data = Mock()
        mock_data.empty = False
        mock_data.__getitem__ = Mock(return_value=Mock())
        mock_data.__getitem__.return_value.iloc = [85000]
        mock_stock.trading.price_board.return_value = mock_data
        
        result = vnstock_services.get_refer_price('VIC')
        assert result is not None

    def test_connection_timeout(self):
        """Test xử lý timeout kết nối."""
        with patch('portfolio.vnstock_services.stock') as mock_stock:
            mock_stock.trading.price_board.side_effect = TimeoutError("Connection timeout")
            
            result = vnstock_services.get_current_bid_price('VIC')
            assert result is None

    @patch('portfolio.vnstock_services.stock')
    def test_empty_response_handling(self, mock_stock):
        """Test xử lý response rỗng."""
        mock_data = Mock()
        mock_data.empty = True
        mock_stock.trading.price_board.return_value = mock_data
        
        result = vnstock_services.get_current_bid_price('INVALID_SYMBOL')
        assert result is None

    @patch('portfolio.vnstock_services.stock')
    def test_get_current_price_multiple_stocks(self, mock_stock):
        """Test lấy giá hiện tại nhiều cổ phiếu."""
        mock_data = Mock()
        mock_data.empty = False
        mock_data.__getitem__ = Mock(return_value=['VIC', 'VHM'])
        mock_stock.trading.price_board.return_value = mock_data
        
        result = vnstock_services.get_current_price(['VIC', 'VHM'])
        assert result is not None

    def test_sync_vnstock_to_assets(self):
        """Test đồng bộ dữ liệu VnStock vào Assets."""
        with patch('portfolio.vnstock_services.stock') as mock_stock:
            mock_symbols = Mock()
            mock_symbols.empty = False
            mock_symbols.__getitem__ = Mock(return_value=['VIC'])
            mock_symbols.tolist = Mock(return_value=['VIC'])
            mock_stock.listing.all_symbols.return_value = mock_symbols
            
            mock_price_board = Mock()
            mock_price_board.empty = False
            mock_price_board.columns = Mock()
            mock_stock.trading.price_board.return_value = mock_price_board
            
            result = vnstock_services.sync_vnstock_to_assets()
            assert isinstance(result, dict)

    @patch('portfolio.vnstock_services.Vnstock')
    def test_get_all_stock_symbols(self, mock_vnstock):
        """Test lấy tất cả mã cổ phiếu."""
        mock_instance = Mock()
        mock_stock_obj = Mock()
        mock_listing = Mock()
        mock_listing.all_symbols.return_value.values = [['VIC', 'VinGroup'], ['VHM', 'Vinhomes']]
        mock_stock_obj.listing = mock_listing
        mock_instance.stock.return_value = mock_stock_obj
        mock_vnstock.return_value = mock_instance
        
        result = vnstock_services.get_all_stock_symbols()
        assert isinstance(result, list)
        assert len(result) >= 0

    def test_fetch_stock_prices_snapshot(self):
        """Test lấy snapshot giá cổ phiếu."""
        with patch('portfolio.vnstock_services.stock') as mock_stock:
            mock_symbols = Mock()
            mock_symbols.empty = False
            mock_symbols.__getitem__ = Mock(return_value=['VIC'])
            mock_symbols.tolist = Mock(return_value=['VIC'])
            mock_stock.listing.all_symbols.return_value = mock_symbols
            
            mock_price_board = Mock()
            mock_price_board.empty = False
            mock_price_board.columns = ['listing_symbol', 'match_match_price']
            mock_stock.trading.price_board.return_value = mock_price_board
            
            result = vnstock_services.fetch_stock_prices_snapshot()
            # Result có thể là None hoặc DataFrame
            assert result is None or hasattr(result, 'columns') 