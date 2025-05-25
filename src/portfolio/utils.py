import requests
import json
from django.conf import settings
from decimal import Decimal

def get_ai_response(message):
    """
    Gọi API Gemini để nhận phản hồi từ AI
    
    Args:
        message (str): Tin nhắn của người dùng
        
    Returns:
        str: Phản hồi từ AI hoặc thông báo lỗi
    """
    try:
        API_KEY = "AIzaSyB6UifFBfKbGgJmTGdPtyQW-OzaNRithOM"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": f"""Bạn là trợ lý đầu tư tài chính AstroBot, giúp người dùng với các câu hỏi về đầu tư chứng khoán và quản lý danh mục. 
                         Hãy trả lời ngắn gọn, hữu ích và chuyên nghiệp.
                         
                         Sử dụng các định dạng đặc biệt cho câu trả lời đẹp và ấn tượng:
                         
                         1. Tiêu đề và phần quan trọng:
                            - Sử dụng # để tạo tiêu đề chính
                            - Sử dụng ## và ### cho các tiêu đề phụ
                            - Sử dụng **đậm** cho các thuật ngữ quan trọng
                            - Sử dụng *nghiêng* cho các định nghĩa hoặc giải thích
                            - Sử dụng ==từ khóa== để highlight các khái niệm quan trọng
                            - Dùng ký hiệu như [123.456] cho các số liệu tài chính
                         
                         2. Danh sách và cấu trúc:
                            - Sử dụng dấu * hoặc - để tạo danh sách không thứ tự
                            - Sử dụng 1., 2., v.v. để tạo danh sách có thứ tự
                            - Sử dụng > để tạo blockquote cho các thông tin quan trọng
                            
                         3. Cards và thông tin đặc biệt:
                            - Sử dụng [info]...[/info] để tạo khung thông tin
                            - Sử dụng [warning]...[/warning] cho cảnh báo
                            - Sử dụng [success]...[/success] cho các mẹo hữu ích
                         
                         4. Bảng:
                            - Sử dụng định dạng bảng markdown cho dữ liệu có cấu trúc. Ví dụ:
                            
                            | Cột 1 | Cột 2 | Cột 3 |
                            |-------|-------|-------|
                            | Dữ liệu 1 | Dữ liệu 2 | Dữ liệu 3 |
                         
                         Trả lời phải đẹp, có cấu trúc rõ ràng, sử dụng 1-2 emoji phù hợp nếu cần thiết.

                         Người dùng yêu cầu: {message}"""}
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Đã xảy ra lỗi khi kết nối với API: {response.status_code}"
    
    except Exception as e:
        return f"Đã xảy ra lỗi: {str(e)}" 

def generate_qr_code(amount, transaction_id, username=None):
    """
    Tạo QR code VietQR cho giao dịch chuyển khoản ngân hàng
    
    Args:
        amount (float): Số tiền cần chuyển khoản
        transaction_id (str): Mã giao dịch để ghi trong nội dung chuyển khoản
        username (str, optional): Tên người dùng để thêm vào nội dung chuyển khoản
        
    Returns:
        str: URL của hình ảnh QR code
    """
    # Thông tin ngân hàng mặc định (MB Bank)
    BANK_ID = "MB"
    ACCOUNT_NO = "99924999999"
    
    # Tạo nội dung chuyển khoản bao gồm mã giao dịch, số tiền và tên người dùng
    transfer_content = transaction_id
    if amount:
        transfer_content += f" {amount}"
    if username:
        transfer_content += f" {username}"
    
    # Tạo URL QR code từ VietQR
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-compact2.png?amount={amount}&addInfo={transfer_content}"
    
    return qr_url

def check_paid(transaction_id=None, amount=None):
    """
    Kiểm tra thông tin giao dịch nạp tiền từ API
    
    Args:
        transaction_id (str, optional): Mã giao dịch cần kiểm tra
        amount (Decimal, optional): Số tiền cần kiểm tra
        
    Returns:
        dict: Kết quả kiểm tra với các thông tin:
            - success (bool): Thành công hay không
            - message (str): Thông báo kết quả
            - data (dict): Dữ liệu giao dịch nếu tìm thấy
            - match_transaction (bool): Có trùng mã giao dịch không
            - match_amount (bool): Có trùng số tiền không
    """
    result = {
        'success': False,
        'message': '',
        'data': None,
        'match_transaction': False,
        'match_amount': False
    }
    
    try:
        print(f"[DEBUG] Đang kiểm tra giao dịch với mã: {transaction_id}, số tiền: {amount}")
        
        # URL API lấy thông tin giao dịch
        url = "https://script.google.com/macros/s/AKfycbzKZpHfNxncQvpuVzqGyXTc5Jf2_rLcA8zo99oH2w0QADShVbHa848L3wjVkIVSudsn/exec"
        print(f"[DEBUG] Đang truy vấn API với transaction_id: {transaction_id}")
        
        response = requests.get(url)
        response.raise_for_status()  # Nếu lỗi HTTP thì raise exception
        data = response.json()
        transactions = data["data"]
        
        # In thông tin debug
        print(f"[DEBUG] Đã nhận được {len(transactions)} giao dịch từ API")
        for idx, trans in enumerate(transactions):
            desc = trans.get("Mô tả", "")
            code = desc.split()[0] if desc else ""
            print(f"[DEBUG] Giao dịch #{idx+1}: Mã={code}, Mô tả={desc}, Giá trị={trans.get('Giá trị', 'N/A')}")
        
        # Nếu không cung cấp mã giao dịch, trả về giao dịch mới nhất
        if not transaction_id:
            last_transaction = transactions[-1]
            result['data'] = last_transaction
            result['success'] = True
            result['message'] = "Lấy thông tin giao dịch mới nhất thành công"
            return result
        
        # Kiểm tra từng giao dịch để tìm mã giao dịch trùng khớp
        found_transaction = None
        
        for transaction in transactions:
            # Lấy mô tả giao dịch
            description = transaction.get("Mô tả", "")
            
            # Lấy từ đầu tiên trong mô tả (mã giao dịch)
            transaction_code = description.split()[0] if description else ""
            
            # In thông tin debug cho mỗi giao dịch được kiểm tra
            print(f"[DEBUG] Đang so sánh: {transaction_code} với {transaction_id}")
            
            # Kiểm tra nếu mã giao dịch trùng khớp
            if transaction_code == transaction_id:
                found_transaction = transaction
                transaction_amount = Decimal(str(transaction.get("Giá trị", 0)))
                
                result['data'] = found_transaction
                result['match_transaction'] = True
                
                # Kiểm tra số tiền nếu được cung cấp
                if amount is not None:
                    if not isinstance(amount, Decimal):
                        amount = Decimal(str(amount))
                    result['match_amount'] = abs(transaction_amount - amount) < Decimal('1000')  # Cho phép sai số nhỏ
                    
                    if result['match_amount']:
                        result['success'] = True
                        result['message'] = f"Xác nhận nạp tiền thành công với mã giao dịch {transaction_id}, số tiền {transaction_amount:,.0f} VNĐ"
                    else:
                        result['success'] = False
                        result['message'] = f"Mã giao dịch {transaction_id} hợp lệ nhưng số tiền không đúng. Số tiền chuyển: {transaction_amount:,.0f} VNĐ, Số tiền cần nạp: {amount:,.0f} VNĐ"
                else:
                    result['success'] = True
                    result['message'] = f"Tìm thấy giao dịch với mã {transaction_id}"
                
                return result
        
        # Không tìm thấy giao dịch
        if not found_transaction:
            result['success'] = False
            result['message'] = f"Không tìm thấy giao dịch với mã {transaction_id}"
            print(f"[DEBUG] Không tìm thấy giao dịch nào khớp với mã: {transaction_id}")
            
            # Thử tìm giao dịch với nội dung chứa mã giao dịch (trường hợp không phải từ đầu tiên)
            possible_match = None
            for transaction in transactions:
                description = transaction.get("Mô tả", "")
                if transaction_id in description:
                    possible_match = transaction
                    print(f"[DEBUG] Tìm thấy giao dịch có chứa mã: {transaction_id} trong mô tả: {description}")
                    break
                    
            if possible_match:
                result['message'] += f". Tuy nhiên, có một giao dịch chứa mã này trong nội dung: {possible_match.get('Mô tả', '')}"
            
            # Kiểm tra giao dịch mới nhất
            if transactions:
                latest = transactions[-1]
                latest_desc = latest.get("Mô tả", "")
                latest_code = latest_desc.split()[0] if latest_desc else ""
                result['message'] += f". Giao dịch mới nhất có mã: {latest_code}"
            
    except Exception as e:
        result['success'] = False
        result['message'] = f"Lỗi khi kiểm tra giao dịch: {str(e)}"
        print(f"[DEBUG] Exception: {str(e)}")
    
    return result 

# Auth0 Functions
def get_auth0_user_profile(access_token):
    """
    Fetch additional user profile data from Auth0 API using the access token.
    
    Args:
        access_token (str): The access token obtained from Auth0 authentication
        
    Returns:
        dict: User profile data from Auth0
    """
    from django.conf import settings
    
    # Configure the Auth0 API URL
    url = f"https://{settings.AUTH0_DOMAIN}/userinfo"
    
    # Configure the request headers with the access token
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        # Make the request to the Auth0 API
        response = requests.get(url, headers=headers)
        
        # If successful, return the user profile data
        if response.status_code == 200:
            return response.json()
        
        # Log errors for debugging
        print(f"Auth0 API error: {response.status_code} - {response.text}")
        return {}
    
    except Exception as e:
        # Log any exceptions for debugging
        print(f"Error fetching Auth0 user profile: {str(e)}")
        return {} 