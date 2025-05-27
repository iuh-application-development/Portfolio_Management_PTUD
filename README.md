# TÊN ĐỀ TÀI: Hệ Thống Quản Lý Danh Mục Đầu Tư

## 1. THÔNG TIN NHÓM

- Hoa Xuân Hoàn - hoaxuanhoan@gmail.com  
- Đào Tiến Sang - tiensangdao2004@gmail.com  
- Nguyễn Chí Trung - trungtada123@gmail.com  
- Nguyễn Trường Vương - tiger.data105@gmail.com

**Link Video:** [https://youtu.be/ThxjXBCELSM](https://youtu.be/ThxjXBCELSM)
**Link Web Demo:** [https://portfolio-management-ca62a2efb4f8.herokuapp.com/](https://portfolio-management-ca62a2efb4f8.herokuapp.com/)

### 1.1. Phân chia công việc

Mỗi thành viên đảm nhận cả 3 yếu tố (Backend + Frontend + Testing) cho một module chức năng cụ thể:

#### **Module 1: Authentication & Market Data**
**Thành viên phụ trách**: _[Đào Tiến Sang]_

**Backend responsibilities**:
- Model: User (AbstractUser), Auth0 integration
- Views: Login, logout, callback, profile management
- APIs: `/login/`, `/logout/`, `/callback/`, `/api/user-profile/`
- Auth0 configuration và social login setup
- Session management và security
- Market data APIs: `/api/market-data/`, `/api/stock-price/<symbol>/`
- VNStock API integration cho market data realtime
- Market data synchronization và caching

**Frontend responsibilities**:
- Trang đăng nhập (`img_readme/login.jpg`)
- Trang cá nhân (`img_readme/trangcanhan.jpg`) 
- Upload avatar và form validation
- Auth0 social login buttons
- Responsive design cho authentication flows
- Trang thị trường (`img_readme/trangthitruong.jpg`)
- Biểu đồ thị trường (`img_readme/chart_trangthitruong.jpg`)
- Search và filter mã cổ phiếu

**Testing**:
- Unit tests cho authentication flow
- Integration tests với Auth0
- Market data API testing

---

#### **Module 2: Wallet, Banking & AI Chat**
**Thành viên phụ trách**: _[Nguyễn Chí Trung]_

**Backend responsibilities**:
- Models: Wallet, BankAccount, BankTransaction
- Views: Wallet management, deposit, withdraw
- APIs: `/api/wallet-data/`, `/wallet/deposit/`, `/wallet/withdraw/`
- Casso API integration cho payment processing
- Google Apps Script webhook setup
- Transaction validation và approval workflow
- AI Chat API: `/api/ai-chat/`
- Google AI Studio (Gemini) integration
- AI conversation management và context handling

**Frontend responsibilities**:
- Trang ví điện tử (`img_readme/vidientu.jpg`)
- Giao diện nạp tiền (`img_readme/naptienvidientu.jpg`)
- Giao diện rút tiền (`img_readme/ruttienvidientu.jpg`)
- QR code generation và bank selection
- Realtime balance updates
- AstroBot AI chat (`img_readme/astrobot.jpg`)
- Chat interface với animations và typing indicators
- AI conversation flow và suggested questions

**Testing**:
- Unit tests cho wallet operations
- Banking APIs integration tests
- AI chatbot conversation testing

---

#### **Module 3: Portfolio & Trading System**
**Thành viên phụ trách**: _[Hoa Xuân Hoàn]_

**Backend responsibilities**:
- Models: Portfolio, PortfolioSymbol, StockTransaction, Assets
- Views: Portfolio CRUD, buy/sell stocks, transaction history
- APIs: `/portfolios/`, `/portfolios/<id>/buy/`, `/portfolios/<id>/sell/`
- VNStock API integration cho stock data
- P&L calculation logic
- Trading validation (balance, quantity checks)

**Frontend responsibilities**:
- Danh sách danh mục (`img_readme/danhmuc.jpg`)
- Tạo danh mục (`img_readme/taodanhmuc.jpg`, `img_readme/danhmucsaukhitao.jpg`)
- Chi tiết danh mục (`img_readme/chitietdanhmuc.jpg`)
- Mua cổ phiếu (`img_readme/muacophieu.jpg`)
- Bán cổ phiếu (`img_readme/bancophieu.jpg`)
- Danh sách tài sản (`img_readme/danhsachtaisan.jpg`)
- Lịch sử giao dịch (`img_readme/lichsugiaodich.jpg`)

**Testing**:
- Unit tests cho trading logic
- Integration tests với VNStock API
- Performance testing cho large portfolios

---

#### **Module 4: Admin System**
**Thành viên phụ trách**: _[Nguyễn Trường Vương]_

**Backend responsibilities**:
- Models: Admin-related models
- Views: Admin dashboard, user management, transaction approval
- APIs: `/api/admin-stats/`, `/admin/users/`, `/admin/transactions/`
- Admin user management và block/unblock functionality
- Transaction approval workflow cho withdrawals
- Admin dashboard metrics và statistics
- System monitoring và reporting

**Frontend responsibilities**:
- Dashboard chính (`img_readme/dashboard.jpg`)
- Trang chủ Admin (`img_readme/trangchu_admin.jpg`)
- Dashboard Admin (`img_readme/dashboard_admin.jpg`)
- Quản lý User (`img_readme/quanlyuser.jpg`, `img_readme/chitietuser.jpg`)
- Quản lý Giao dịch (`img_readme/quanlygiaodich.jpg`)
- Admin charts và statistics visualization
- User activity monitoring interface

**Testing**:
- Unit tests cho admin functions
- Admin workflow testing
- Security testing cho admin privileges

### 1.2. Chung cho tất cả thành viên

**🔄 Shared Responsibilities**:
- **Docker & Deployment**: Mỗi người đảm bảo module của mình chạy được trong Docker
- **Database Design**: Collaborate trong việc thiết kế ERD và relationships
- **Code Review**: Peer review code của nhau trước khi merge
- **Integration Testing**: Test integration giữa các modules
- **Documentation**: Mỗi người viết docs cho module của mình

**🛠️ Công cụ chung**:
- **Version Control**: Git với feature branches cho từng module
- **Project Management**: GitHub Issues được assign theo module
- **Communication**: Daily standups để sync progress
- **IDE**: VSCode/Cursor với shared settings
- **Testing**: Sử dụng chung Django Test Framework

**📋 Timeline & Milestones**:
- **Week 1-2**: Database design và backend models
- **Week 3-4**: Backend APIs và business logic  
- **Week 5-6**: Frontend implementation
- **Week 7**: Integration testing giữa modules
- **Week 8**: Documentation, deployment và final testing

### 1.3. Cross-module Integration Points

**🔗 Dependencies giữa các modules**:
- **Module 1 → All**: Authentication required cho tất cả features + Market data cho portfolio pricing
- **Module 2 → Module 3**: Wallet balance check khi trading
- **Module 3 → Module 1**: Portfolio cần market data để tính P&L
- **Module 4 → All**: Admin oversight cho tất cả modules

**🎯 Integration Meetings**:
- Weekly sync để đảm bảo APIs compatible
- Shared database schema review sessions
- Cross-module testing collaboration

## 2. MÔ TẢ ĐỀ TÀI

### 2.1. Mô tả tổng quan

Hệ thống quản lý danh mục đầu tư giúp người dùng theo dõi, mua bán tài sản tài chính và tối ưu hóa hiệu suất đầu tư. Đề tài được xây dựng nhằm hỗ trợ nhà đầu tư cá nhân có thể quản lý dòng tiền, giao dịch và phân tích biến động thị trường ngay trên một nền tảng duy nhất. Hệ thống cho phép tạo ví, nạp tiền, thực hiện giao dịch và xem báo cáo hiệu suất, tư vấn AI,... Ngoài ra còn bổ sung thêm một phần nhỏ của admin cho phép quản lý user ( Quản Lý Rút Tiền, Quản Lý Danh Mục, Block/Unblock User)

### 2.2. Mục tiêu

- Phát triển hệ thống web giúp người dùng đăng ký, quản lý tài khoản cá nhân và danh mục đầu tư.  
- Cung cấp giao diện trực quan, dễ sử dụng để theo dõi biến động thị trường và hiệu suất đầu tư.  
- Hỗ trợ thao tác giao dịch tài sản giả lập (mua/bán) để người dùng luyện tập đầu tư ( Hướng phát triển là giao dịch thực )  

## 3. PHÂN TÍCH THIẾT KẾ

### 3.1. Phân tích yêu cầu

**Chức năng:**

**User:**

- Đăng ký, đăng nhập, và xác thực người dùng
- Tạo và quản lý ví tiền của mình
- Nạp tiền vào ví để sử dụng
- Tạo và quản lý danh mục đầu tư cá nhân
- Thực hiện các giao dịch mua và bán tài sản, bao gồm cổ phiếu
- Theo dõi biến động giá trên thị trường tài chính
- Xem xét hiệu suất của danh mục đầu tư
- Nhận hỗ trợ giải đáp thắc mắc từ trí tuệ nhân tạo (AI)

**Admin:**

- Quản lý người dùng trên hệ thống
- Quản lý danh mục, tài sản, và các giao dịch rút tiền
- Thực hiện các chức năng Block/Unlock tài khoản (khi người dùng có biểu hiện khả nghi, mất tài khoản, v.v.)

**Phi chức năng:**

- Giao diện thân thiện người dùng  ( Lấy Tông Màu Tím (Ceiling Price) làm màu chủ đạo )
- Bảo mật thông tin tài khoản  ( Bằng cách sử dụng bên thứ 3 là Auth0 để xác thực đăng nhập )
- Hiệu năng truy xuất dữ liệu tốt 
- Khả năng mở rộng tính năng sau này 

### 3.2. Đặc tả yêu cầu

#### 3.2.1. Yêu cầu chức năng chi tiết

**A. Hệ thống xác thực và quản lý người dùng**

1. **Đăng ký và đăng nhập**
   - Đăng ký tài khoản mới với username, email, password
   - Đăng nhập bằng tài khoản local hoặc Auth0 (Google, Facebook, v.v.)
   - Tự động tạo ví điện tử với số dư khởi tạo 500,000,000 VNĐ khi đăng ký
   - Logout an toàn và xóa session

2. **Quản lý hồ sơ cá nhân**
   - Cập nhật thông tin: họ tên, email, số điện thoại, địa chỉ, giới tính
   - Upload và quản lý ảnh đại diện
   - Tích hợp với Auth0 để lấy avatar từ social media
   - Lưu trữ Auth0 User ID để đồng bộ dữ liệu

**B. Hệ thống ví điện tử và giao dịch ngân hàng**

1. **Quản lý ví tiền**
   - Hiển thị số dư ví hiện tại
   - Lịch sử giao dịch nạp/rút tiền
   - Theo dõi realtime số dư ví

2. **Quản lý tài khoản ngân hàng**
   - Thêm/sửa/xóa tài khoản ngân hàng
   - Hỗ trợ 10+ ngân hàng phổ biến tại Việt Nam
   - Đặt tài khoản ngân hàng mặc định
   - Validation số tài khoản và thông tin ngân hàng

3. **Nạp tiền**
   - Nạp tiền vào ví qua chuyển khoản ngân hàng
   - Tích hợp Google Apps Script và Casso API để xử lý tự động
   - Xác nhận giao dịch realtime

4. **Rút tiền**
   - Rút tiền từ ví về tài khoản ngân hàng
   - Validation số dư khả dụng
   - Quy trình phê duyệt từ admin
   - Tính phí giao dịch và ghi nhận

**C. Hệ thống quản lý danh mục đầu tư**

1. **Tạo và quản lý danh mục**
   - Tạo nhiều danh mục đầu tư khác nhau
   - Đặt tên, mô tả, mục tiêu đầu tư
   - Thiết lập giá trị mục tiêu và mức độ rủi ro (thấp/trung bình/cao)
   - Theo dõi tiến độ đạt mục tiêu

2. **Quản lý tài sản trong danh mục**
   - Thêm/bớt mã cổ phiếu vào danh mục
   - Theo dõi số lượng cổ phiếu sở hữu
   - Tính toán giá trung bình và lãi/lỗ cho từng mã
   - Cập nhật giá realtime từ VNStock API

**D. Hệ thống giao dịch chứng khoán**

1. **Giao dịch mua/bán**
   - Mua cổ phiếu với giá thị trường hiện tại
   - Bán cổ phiếu đã sở hữu
   - Validation số dư ví và số lượng cổ phiếu
   - Ghi nhận giao dịch với timestamp chính xác

2. **Lịch sử giao dịch**
   - Xem lịch sử mua/bán theo danh mục
   - Filter theo loại giao dịch, thời gian
   - Tính toán tổng giá trị giao dịch

3. **Quản lý tài sản cá nhân**
   - Danh sách tổng hợp tất cả tài sản sở hữu
   - Sync tự động với dữ liệu VNStock
   - Cập nhật giá realtime cho tất cả mã đang sở hữu

**E. Hệ thống thông tin thị trường**

1. **Dữ liệu thị trường realtime**
   - Hiển thị bảng giá chứng khoán realtime
   - Thông tin giá sàn, trần, tham chiếu
   - Volume giao dịch và biến động giá

2. **Dữ liệu lịch sử**
   - Biểu đồ giá lịch sử của từng mã cổ phiếu
   - Hỗ trợ nhiều khung thời gian
   - Export dữ liệu lịch sử

3. **Tìm kiếm và lọc**
   - Tìm kiếm mã cổ phiếu theo ký hiệu hoặc tên công ty
   - Lọc theo ngành, sàn giao dịch
   - Danh sách mã cổ phiếu phổ biến

**F. Dashboard và báo cáo**

1. **Dashboard tổng quan**
   - Thống kê tổng quan tài sản
   - Biểu đồ phân bố danh mục
   - Top cổ phiếu lãi/lỗ nhất
   - Cập nhật dữ liệu realtime

2. **Báo cáo hiệu suất**
   - Tính toán P&L (Profit & Loss) cho từng danh mục
   - Phần trăm lãi/lỗ so với vốn ban đầu
   - Tracking tiến độ đạt mục tiêu đầu tư

**G. Hệ thống AI Chat Support**

1. **Chatbot tư vấn tài chính**
   - Tích hợp Google AI Studio (Gemini)
   - Trả lời câu hỏi về đầu tư, phân tích thị trường
   - Gợi ý câu hỏi thông minh
   - Lưu trữ lịch sử chat trong session

2. **Tương tác realtime**
   - Chat interface hiện đại với animation
   - Typing indicator khi AI đang xử lý
   - Responsive design cho mobile

**H. Hệ thống quản trị (Admin)**

1. **Quản lý người dùng**
   - Danh sách tất cả người dùng đã đăng ký
   - Xem chi tiết thông tin và hoạt động của user
   - Block/Unblock tài khoản người dùng
   - Thống kê người dùng hoạt động

2. **Quản lý giao dịch rút tiền**
   - Danh sách yêu cầu rút tiền chờ duyệt
   - Phê duyệt/từ chối yêu cầu rút tiền
   - Theo dõi lịch sử giao dịch ngân hàng
   - Quản lý phí giao dịch

3. **Dashboard admin**
   - Thống kê tổng quan hệ thống
   - Số lượng user, giao dịch, tổng giá trị
   - Biểu đồ hoạt động theo thời gian
   - Monitoring realtime

#### 3.2.2. Yêu cầu phi chức năng chi tiết

**A. Hiệu năng**
- Thời gian tải trang < 3 giây
- API response time < 500ms cho các thao tác cơ bản
- Cập nhật dữ liệu realtime với độ trễ < 2 giây
- Hỗ trợ đồng thời 100+ users online

**B. Bảo mật**
- Xác thực OAuth 2.0 với Auth0
- Mã hóa password bằng Django's PBKDF2
- HTTPS cho all endpoints
- Session management an toàn
- Input validation và sanitization
- Protection against SQL injection, XSS

**C. Khả năng mở rộng**
- Kiến trúc modular với Django apps
- Database indexing cho performance
- Caching strategy với Redis (future)
- Horizontal scaling ready với Docker
- API-first design cho mobile integration

**D. Trải nghiệm người dùng**
- Responsive design cho all devices (desktop, tablet, mobile)
- Modern UI với Bootstrap 5 và custom CSS
- Loading animations và transitions mượt mà
- Notification system realtime
- Multilingual support (Vietnamese)

**E. Tính khả dụng**
- Uptime 99.5%+
- Graceful error handling
- Backup và recovery procedures
- Health monitoring với logging
- Failover mechanisms

#### 3.2.3. Ràng buộc kỹ thuật

**A. Công nghệ sử dụng**
- Backend: Django 4.x + Python 3.11+
- Database: PostgreSQL 15+
- Frontend: HTML5, CSS3, JavaScript ES6+
- Deployment: Docker + Docker Compose
- External APIs: VNStock, Auth0, Google AI Studio

**B. Tích hợp bên thứ ba**
- **VNStock API**: Dữ liệu chứng khoán realtime
- **Auth0**: Xác thực và authorization
- **Google AI Studio**: AI chatbot
- **Casso API**: Payment processing
- **Google Apps Script**: Webhook handling

**C. Data Models**

Hệ thống sử dụng 8 models chính:

1. **User** (AbstractUser): Thông tin người dùng + Auth0 integration
2. **Wallet**: Ví điện tử với balance tracking
3. **BankAccount**: Thông tin tài khoản ngân hàng
4. **BankTransaction**: Giao dịch nạp/rút tiền
5. **Portfolio**: Danh mục đầu tư với mục tiêu và risk tolerance  
6. **PortfolioSymbol**: Mã cổ phiếu trong danh mục với số lượng và giá
7. **StockTransaction**: Lịch sử giao dịch mua/bán
8. **Assets**: Master data các mã cổ phiếu và giá hiện tại

**D. API Endpoints**

Hệ thống cung cấp 15+ REST APIs:
- Authentication: `/login/`, `/logout/`, `/callback/`
- Wallet: `/api/wallet-data/`, `/wallet/deposit/`, `/wallet/withdraw/`
- Trading: `/portfolios/<id>/buy/`, `/portfolios/<id>/sell/`
- Market Data: `/api/market-data/`, `/api/stock-price/<symbol>/`
- AI Chat: `/api/ai-chat/`
- Admin: `/api/admin-stats/`, `/admin/transactions/<id>/action/`

### 3.3. Thiết kế hệ thống

- **Use Case Diagram**: Hệ thống có 2 actor chính (User và Admin) với các use case được phân chia rõ ràng theo chức năng. Sơ đồ Use Case mô tả đầy đủ các tương tác giữa người dùng và hệ thống để thực hiện các nghiệp vụ đầu tư và quản lý.

#### 3.3.1. Use Case Diagram Chi Tiết

**A. Actors (Tác nhân)**

1. **User (Người dùng)**: Nhà đầu tư cá nhân sử dụng hệ thống
2. **Admin (Quản trị viên)**: Người quản lý hệ thống
3. **VNStock API**: Hệ thống bên ngoài cung cấp dữ liệu chứng khoán
4. **Auth0 System**: Hệ thống xác thực bên thứ ba
5. **Banking System**: Hệ thống ngân hàng (Casso API + Google Apps Script)

**B. Use Cases theo từng Actor**

**🔵 USER USE CASES:**

**Sơ Đồ Tổng Quan Cho User**
![Use Case Diagram -For User](img_readme/Use_Case_Diagram.jpg)


**Sơ Đồ Tổng Quan Cho Admin**
![Use Case Diagram - For Admin](img_readme/admin_flow.jpg)

**UC1. Quản lý tài khoản và xác thực**
```
UC1.1. Đăng ký tài khoản
  - Precondition: Chưa có tài khoản
  - Main Flow: Nhập thông tin → Xác thực email → Tạo tài khoản thành công
  - Postcondition: Tài khoản được tạo, ví điện tử khởi tạo 500M VNĐ

UC1.2. Đăng nhập hệ thống
  - Precondition: Có tài khoản hợp lệ
  - Main Flow: Nhập credentials → Xác thực → Truy cập dashboard
  - Alternative Flow: Đăng nhập bằng Auth0 (Google/Facebook)
  - Postcondition: Session được tạo, truy cập được hệ thống

UC1.3. Quản lý hồ sơ cá nhân
  - Precondition: Đã đăng nhập
  - Main Flow: Xem/Sửa thông tin cá nhân → Lưu thay đổi
  - Includes: Upload avatar, cập nhật thông tin liên lạc
  - Postcondition: Thông tin được cập nhật
```

**UC2. Quản lý ví điện tử**
```
UC2.1. Xem số dư ví
  - Precondition: Đã đăng nhập
  - Main Flow: Truy cập trang ví → Hiển thị số dư realtime
  - Postcondition: Hiển thị số dư và lịch sử giao dịch

UC2.2. Nạp tiền vào ví
  - Precondition: Đã đăng nhập, có tài khoản ngân hàng
  - Main Flow: Chọn số tiền → Chuyển khoản → Xác nhận giao dịch
  - Extends: Thêm tài khoản ngân hàng mới
  - External Actor: Banking System (Casso API)
  - Postcondition: Số dư ví được cập nhật

UC2.3. Rút tiền từ ví
  - Precondition: Đã đăng nhập, có số dư đủ
  - Main Flow: Nhập số tiền → Chọn tài khoản ngân hàng → Gửi yêu cầu
  - Business Rule: Cần admin phê duyệt
  - Postcondition: Yêu cầu rút tiền được tạo
```

**UC3. Quản lý danh mục đầu tư**
```
UC3.1. Tạo danh mục đầu tư
  - Precondition: Đã đăng nhập
  - Main Flow: Nhập tên/mô tả → Thiết lập mục tiêu → Chọn mức rủi ro → Tạo
  - Business Rule: Tên danh mục unique per user
  - Postcondition: Danh mục mới được tạo

UC3.2. Xem danh sách danh mục
  - Precondition: Đã đăng nhập
  - Main Flow: Truy cập trang danh mục → Hiển thị list + performance
  - Postcondition: Hiển thị tất cả danh mục và thống kê

UC3.3. Xem chi tiết danh mục
  - Precondition: Có danh mục tồn tại
  - Main Flow: Click vào danh mục → Hiển thị chi tiết tài sản
  - Includes: Xem P&L, biểu đồ phân bố, lịch sử giao dịch
  - Postcondition: Hiển thị thông tin chi tiết danh mục

UC3.4. Cập nhật/Xóa danh mục
  - Precondition: Là chủ sở hữu danh mục
  - Main Flow: Sửa thông tin hoặc xóa danh mục
  - Business Rule: Không xóa được nếu có tài sản
  - Postcondition: Danh mục được cập nhật/xóa
```

**UC4. Giao dịch chứng khoán**
```
UC4.1. Mua cổ phiếu
  - Precondition: Đã đăng nhập, có số dư đủ
  - Main Flow: Chọn mã CP → Nhập số lượng → Xác nhận mua
  - External Actor: VNStock API (lấy giá realtime)
  - Business Rule: Kiểm tra số dư, validate mã CP
  - Postcondition: Giao dịch được ghi nhận, cập nhật portfolio

UC4.2. Bán cổ phiếu
  - Precondition: Đã đăng nhập, có CP trong portfolio
  - Main Flow: Chọn CP sở hữu → Nhập số lượng → Xác nhận bán
  - Business Rule: Số lượng bán <= số lượng sở hữu
  - Postcondition: Giao dịch được ghi nhận, cập nhật số dư

UC4.3. Xem lịch sử giao dịch
  - Precondition: Đã đăng nhập
  - Main Flow: Truy cập lịch sử → Filter/Search → Xem chi tiết
  - Includes: Filter theo thời gian, loại giao dịch, danh mục
  - Postcondition: Hiển thị lịch sử giao dịch
```

**UC5. Theo dõi thị trường**
```
UC5.1. Xem bảng giá chứng khoán
  - Precondition: Đã đăng nhập
  - Main Flow: Truy cập trang thị trường → Hiển thị bảng giá realtime
  - External Actor: VNStock API
  - Postcondition: Hiển thị giá realtime tất cả mã CP

UC5.2. Xem biểu đồ giá lịch sử
  - Precondition: Đã đăng nhập
  - Main Flow: Chọn mã CP → Xem chart → Chọn khung thời gian
  - External Actor: VNStock API
  - Postcondition: Hiển thị biểu đồ interactive

UC5.3. Tìm kiếm mã cổ phiếu
  - Precondition: Đã đăng nhập
  - Main Flow: Nhập từ khóa → Tìm kiếm → Hiển thị kết quả
  - Includes: Tìm theo mã CP hoặc tên công ty
  - Postcondition: Hiển thị danh sách mã CP phù hợp
```

**UC6. AI Chat Support**
```
UC6.1. Chat với AI Bot
  - Precondition: Đã đăng nhập
  - Main Flow: Mở chat → Nhập câu hỏi → Nhận phản hồi từ AI
  - External Actor: Google AI Studio (Gemini)
  - Includes: Câu hỏi gợi ý, lưu lịch sử chat
  - Postcondition: Nhận được tư vấn từ AI
```

**🔴 ADMIN USE CASES:**

**UC7. Quản lý người dùng**
```
UC7.1. Xem danh sách người dùng
  - Precondition: Đã đăng nhập với quyền admin
  - Main Flow: Truy cập admin panel → Xem list users
  - Postcondition: Hiển thị tất cả users và thông tin

UC7.2. Xem chi tiết người dùng
  - Precondition: Có quyền admin
  - Main Flow: Click vào user → Xem thông tin chi tiết
  - Includes: Portfolio, giao dịch, hoạt động
  - Postcondition: Hiển thị thông tin đầy đủ user

UC7.3. Block/Unblock người dùng
  - Precondition: Có quyền admin
  - Main Flow: Chọn user → Block/Unblock → Xác nhận
  - Business Rule: User bị block không thể đăng nhập
  - Postcondition: Trạng thái user được cập nhật
```

**UC8. Quản lý giao dịch rút tiền**
```
UC8.1. Xem yêu cầu rút tiền
  - Precondition: Có quyền admin
  - Main Flow: Truy cập trang quản lý → Xem list pending withdrawals
  - Postcondition: Hiển thị tất cả yêu cầu chờ duyệt

UC8.2. Phê duyệt/Từ chối rút tiền
  - Precondition: Có yêu cầu rút tiền pending
  - Main Flow: Xem chi tiết → Quyết định approve/reject → Xác nhận
  - Business Rule: Cập nhật số dư nếu approve
  - Postcondition: Yêu cầu được xử lý, user nhận thông báo
```

**UC9. Dashboard và thống kê**
```
UC9.1. Xem dashboard admin
  - Precondition: Có quyền admin
  - Main Flow: Truy cập admin dashboard → Xem metrics realtime
  - Includes: Số lượng users, giao dịch, tổng giá trị
  - Postcondition: Hiển thị thống kê tổng quan hệ thống
```

**C. Quan hệ giữa các Use Cases**

**Include Relationships:**
- UC1.3 includes "Upload Avatar"
- UC3.3 includes "Tính toán P&L", "Hiển thị biểu đồ"
- UC4.1, UC4.2 include "Validate số dư/số lượng"
- UC7.2 includes "Xem portfolio user", "Xem lịch sử giao dịch"

**Extend Relationships:**
- UC2.2 extends "Thêm tài khoản ngân hàng"
- UC5.1 extends "Export dữ liệu"
- UC6.1 extends "Lưu câu hỏi thường gặp"

**Generalization:**
- "Quản lý giao dịch" generalizes UC4.1, UC4.2
- "Xem thông tin thị trường" generalizes UC5.1, UC5.2
- "Quản lý admin" generalizes UC7, UC8, UC9

**D. Business Rules và Constraints**

1. **Bảo mật**: Tất cả use cases yêu cầu authentication
2. **Dữ liệu realtime**: Giá CP cập nhật từ VNStock API
3. **Validation**: Số dư, số lượng CP phải được validate
4. **Workflow**: Rút tiền cần approval từ admin
5. **Unique constraints**: Tên danh mục unique per user
6. **Auto-calculation**: P&L được tính tự động

- **Thiết kế CSDL**: Sơ đồ ERD đính kèm:  
  ![alt text](img_readme/erd.png)  

- **Thiết kế giao diện**: Hệ thống có giao diện hiện đại, responsive và thân thiện người dùng với màu sắc chủ đạo tím (ceiling price) tạo cảm giác chuyên nghiệp và tin cậy.

#### 3.3.2. Giao diện người dùng (User Interface)

**A. Trang chủ và xác thực**

1. **Trang chủ**
   ![Trang chủ](img_readme/trangchu.jpg)
   - Landing page với thiết kế hiện đại, thu hút
   - Giới thiệu các tính năng chính của hệ thống
   - Call-to-action rõ ràng để người dùng đăng ký/đăng nhập

2. **Trang đăng nhập**
   ![Đăng nhập](img_readme/login.jpg)
   - Form đăng nhập đơn giản, dễ sử dụng
   - Tích hợp Auth0 cho đăng nhập social media
   - Thiết kế responsive cho mọi thiết bị

3. **Trang cá nhân**
   ![Trang cá nhân](img_readme/trangcanhan.jpg)
   - Quản lý thông tin cá nhân và avatar
   - Upload ảnh đại diện và cập nhật thông tin
   - Giao diện trực quan với validation realtime

**B. Dashboard và tổng quan**

4. **Dashboard chính**
   ![Dashboard](img_readme/dashboard.jpg)
   - Tổng quan tài sản và danh mục đầu tư
   - Biểu đồ và thống kê realtime
   - Widget hiển thị P&L và hiệu suất

**C. Quản lý danh mục đầu tư**

5. **Danh sách danh mục**
   ![Danh mục](img_readme/danhmuc.jpg)
   - Hiển thị tất cả danh mục đầu tư của người dùng
   - Thông tin tổng quan về hiệu suất từng danh mục

6. **Tạo danh mục mới**
   ![Tạo danh mục](img_readme/taodanhmuc.jpg)
   - Form tạo danh mục với validation
   - Thiết lập mục tiêu và mức độ rủi ro

7. **Danh mục sau khi tạo**
   ![Danh mục sau tạo](img_readme/danhmucsaukhitao.jpg)
   - Hiển thị danh mục vừa được tạo
   - Giao diện clean và organized

8. **Chi tiết danh mục**
   ![Chi tiết danh mục](img_readme/chitietdanhmuc.jpg)
   - Xem chi tiết tài sản trong danh mục
   - Tracking P&L và hiệu suất từng mã

**D. Giao dịch chứng khoán**

9. **Mua cổ phiếu**
   ![Mua cổ phiếu](img_readme/muacophieu.jpg)
   - Interface mua cổ phiếu với validation realtime
   - Hiển thị giá hiện tại và số dư khả dụng

10. **Bán cổ phiếu**
    ![Bán cổ phiếu](img_readme/bancophieu.jpg)
    - Giao diện bán cổ phiếu với danh sách tài sản sở hữu
    - Validation số lượng và tính toán P&L

11. **Danh sách tài sản**
    ![Danh sách tài sản](img_readme/danhsachtaisan.jpg)
    - Tổng hợp tất cả tài sản đang sở hữu
    - Cập nhật giá realtime và P&L

12. **Lịch sử giao dịch**
    ![Lịch sử giao dịch](img_readme/lichsugiaodich.jpg)
    - Theo dõi lịch sử mua/bán chi tiết
    - Filter và search theo nhiều tiêu chí

**E. Ví điện tử và giao dịch ngân hàng**

13. **Ví điện tử**
    ![Ví điện tử](img_readme/vidientu.jpg)
    - Hiển thị số dư và các tính năng ví
    - Quick actions cho nạp/rút tiền

14. **Nạp tiền**
    ![Nạp tiền](img_readme/naptienvidientu.jpg)
    - Giao diện nạp tiền với QR code
    - Tích hợp với hệ thống ngân hàng

15. **Rút tiền**
    ![Rút tiền](img_readme/ruttienvidientu.jpg)
    - Form rút tiền với validation
    - Quản lý tài khoản ngân hàng

**F. Thông tin thị trường**

16. **Trang thị trường**
    ![Trang thị trường](img_readme/trangthitruong.jpg)
    - Bảng giá chứng khoán realtime
    - Search và filter mã cổ phiếu

17. **Biểu đồ thị trường**
    ![Chart thị trường](img_readme/chart_trangthitruong.jpg)
    - Biểu đồ giá lịch sử interactive
    - Nhiều khung thời gian và indicators

**G. AI Chat Support**

18. **AstroBot AI**
    ![AstroBot](img_readme/astrobot.jpg)
    - Chatbot AI tư vấn tài chính
    - Giao diện chat hiện đại với animations

#### 3.3.3. Giao diện quản trị (Admin Interface)

**A. Dashboard Admin**

19. **Trang chủ Admin**
    ![Trang chủ Admin](img_readme/trangchu_admin.jpg)
    - Landing page cho admin với menu navigation
    - Thiết kế professional và easy-to-use

20. **Dashboard Admin**
    ![Dashboard Admin](img_readme/dashboard_admin.jpg)
    - Thống kê tổng quan hệ thống
    - Charts và metrics realtime

**B. Quản lý người dùng**

21. **Quản lý User**
    ![Quản lý User](img_readme/quanlyuser.jpg)
    - Danh sách tất cả người dùng
    - Actions: View, Block/Unblock users

22. **Chi tiết User**
    ![Chi tiết User](img_readme/chitietuser.jpg)
    - Thông tin chi tiết và hoạt động của user
    - Lịch sử giao dịch và portfolio

**C. Quản lý giao dịch**

23. **Quản lý Giao dịch**
    ![Quản lý Giao dịch](img_readme/quanlygiaodich.jpg)
    - Danh sách yêu cầu rút tiền chờ duyệt
    - Approve/Reject transactions

#### 3.3.4. Đặc điểm thiết kế

**A. Design System**
- **Color Palette**: Tím chủ đạo (#7e57c2) - biểu tượng ceiling price
- **Typography**: Montserrat (headings) + Open Sans (body text)
- **Components**: Bootstrap 5 + Custom CSS
- **Icons**: Font Awesome 6 + Custom SVG

**B. Responsive Design**
- Mobile-first approach
- Breakpoints: 576px, 768px, 992px, 1200px
- Flexible grid system và components

**C. User Experience**
- Loading animations và micro-interactions
- Toast notifications realtime
- Smooth transitions và hover effects
- Accessibility compliance (WCAG 2.1)

**D. Performance Optimization**
- Lazy loading cho images và charts
- CSS/JS minification
- Optimized asset delivery
- Progressive enhancement

## 4. CÔNG CỤ VÀ CÔNG NGHỆ SỬ DỤNG

- **Ngôn ngữ lập trình**: Python
- **Framework**: Django  
- **Cơ sở dữ liệu**: PostgreSQL  
- **Front-end**: HTML, CSS, JavaScript  
- **IDE**: VSCode, Cursor 
- **Công cụ triển khai**: Docker, Docker Compose  

## 5. TRIỂN KHAI

### 5.1. Cài đặt yêu cầu

- Python 3.8+
- PostgreSQL
- Docker (nếu dùng Docker)

### 5.2. Cài đặt Local

**Windows:**

```bash
.\run.bat

```

**Linux/macOS:**

```bash
chmod +x run.sh
bash run.sh

```

### 5.3. Chạy với Docker ( Bật Git Bash và chạy lần lượt 2 lệnh sau)

```bash
dos2unix entrypoint.sh
docker-compose up --build
```

**Truy cập hệ thống tại**: [http://localhost:8000](http://localhost:8000)

## 6. KIỂM THỬ

* **Functional Testing**: Kiểm tra khả năng đăng nhập, nạp tiền, giao dịch, tạo portfolio.
* **Performance Testing**: Đánh giá thời gian load trang, truy vấn danh mục khi số lượng tài sản lớn.
* **Unit Tests**: Có sẵn trong `/tests/`  ( Chức năng test hiện chưa hoàn thiện )

## 7. KẾT QUẢ

### 7.1. Kết quả đạt được

* Hoàn thiện hệ thống backend và frontend đầy đủ tính năng.
* Tích hợp thành công Auth0, PostgreSQL, Docker và các API như Google AI Studio, Vnstock, Google Apps Script & Casso.
* Thực hiện thành công các nghiệp vụ tài chính giả lập như mua bán, nạp tiền, xem hiệu suất.

### 7.2. Kết quả chưa đạt được

* Chưa có tính năng để kết nối dữ liệu mua bán trên thị trường thật.
* Chưa tích hợp xác thực OTP/email cho tài khoản.

### 7.3. Hướng phát triển

* Kết nối với các công ty hỗ trợ giao dịch với sàn như DNSE.
* Thêm chức năng phân tích biểu đồ, phân tích kỹ thuật cho người dùng ( Airflow -> Kafka -> Spark -> Postgres (Pipeline Xử lý, thu thập thông tính để kết xuất thành data hữu ích phục vụ cho việc vẽ biểu đồ, xác định điểm mua/bán, Chat Read Data,...)).
* Phát triển phiên bản mobile với React Native hoặc Flutter.

## 8. TÀI LIỆU THAM KHẢO

* [https://vnstocks.com/docs/tai-lieu/huong-dan-nhanh](https://vnstocks.com/docs/tai-lieu/huong-dan-nhanh)
* [https://auth0.com/](https://auth0.com/)
* [https://aistudio.google.com/](https://aistudio.google.com/)
* [https://www.docker.com/](https://www.docker.com/)
* [https://docs.djangoproject.com/](https://docs.djangoproject.com/)
* Tài liệu môn Phát triển ứng dụng web
