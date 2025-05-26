# TÊN ĐỀ TÀI: Hệ Thống Quản Lý Danh Mục Đầu Tư

## 1. THÔNG TIN NHÓM

- Hoa Xuân Hoàn - hoaxuanhoan@gmail.com  
- Đào Tiến Sang - tiensangdao2004@gmail.com  
- Nguyễn Chí Trung - trungtada123@gmail.com  
- Nguyễn Trường Vương - 

## 2. MÔ TẢ ĐỀ TÀI

### 2.1. Mô tả tổng quan

Hệ thống quản lý danh mục đầu tư giúp người dùng theo dõi, mua bán tài sản tài chính và tối ưu hóa hiệu suất đầu tư. Đề tài được xây dựng nhằm hỗ trợ nhà đầu tư cá nhân có thể quản lý dòng tiền, giao dịch và phân tích biến động thị trường ngay trên một nền tảng duy nhất. Hệ thống cho phép tạo ví, nạp tiền, thực hiện giao dịch và xem báo cáo hiệu suất, tư vấn AI,... Ngoài ra còn bổ sung thêm một phần nhỏ của admin cho phép quản lý user ( Quản Lý Rút Tiền, Quản Lý Danh Mục, Block/Unblock User)

### 2.2. Mục tiêu

- Phát triển hệ thống web giúp người dùng đăng ký, quản lý tài khoản cá nhân và danh mục đầu tư.  
- Cung cấp giao diện trực quan, dễ sử dụng để theo dõi biến động thị trường và hiệu suất đầu tư.  
- Hỗ trợ thao tác giao dịch tài sản giả lập (mua/bán) để người dùng luyện tập đầu tư.  

## 3. PHÂN TÍCH THIẾT KẾ

### 3.1. Phân tích yêu cầu

**Chức năng:**

- Đăng ký, đăng nhập, xác thực người dùng  
- Tạo và quản lý ví tiền  
- Nạp tiền vào ví  
- Tạo và quản lý danh mục đầu tư  
- Mua và bán tài sản tài cổ phiếu 
- Theo dõi biến động giá thị trường  
- Xem hiệu suất danh mục  
- Hỗ trợ giải đáp thắc mắc từ AI

**Phi chức năng:**

- Giao diện thân thiện người dùng  ( Lấy Tông Màu Tím (Ceiling Price) làm màu chủ đạo )
- Bảo mật thông tin tài khoản  ( Bằng cách sử dụng bên thứ 3 là Auth0 để xác thực đăng nhập )
- Hiệu năng truy xuất dữ liệu tốt 
- Khả năng mở rộng tính năng sau này 

### 3.2. Đặc tả yêu cầu

Chi tiết trong các module `models.py`, `views.py`, `templates`, với mô hình cơ sở dữ liệu gồm các bảng: `User`, `Portfolio`, `Asset`, `Transaction`, `Wallet`, `BankAccount`.

### 3.3. Thiết kế hệ thống

- **Use Case Diagram**: mô tả người dùng thao tác với hệ thống để đăng ký, tạo ví, giao dịch và xem báo cáo.  
- **Thiết kế CSDL**: Sơ đồ ERD đính kèm:  
  ![alt text](erd.png)  
- **Thiết kế giao diện**: Có trong thư mục `templates/portfolio/` gồm: `home.html`, `dashboard.html`, `login.html`, `register.html`.

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
run.bat
````

**Linux/macOS:**

```bash
chmod +x run.sh
bash run.sh
```

### 5.3. Chạy với Docker

```bash
dos2unix entrypoint.sh
docker-compose up --build
```

**Truy cập hệ thống tại**: [http://localhost:8000](http://localhost:8000)

## 6. KIỂM THỬ

* **Functional Testing**: Kiểm tra khả năng đăng nhập, nạp tiền, giao dịch, tạo portfolio.
* **Performance Testing**: Đánh giá thời gian load trang, truy vấn danh mục khi số lượng tài sản lớn.
* **Unit Tests**: Có sẵn trong `portfolio/tests.py`

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