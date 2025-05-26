from django.contrib import admin  # Nhập các ứng dụng của Django
from django.urls import path, include  # Nhập các hàm để định tuyến URL
from django.conf import settings  # Nhập các cài đặt của dự án
from django.conf.urls.static import static  # Nhập hàm để phục vụ các file tĩnh và media

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Định tuyến URL cho trang quản trị Django mặc định
    path('', include('portfolio.urls')),  # Định tuyến URL cho ứng dụng portfolio
]

if settings.DEBUG:  # Kiểm tra xem có đang ở chế độ debug không
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Phục vụ các file media trong chế độ debug
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # Phục vụ các file tĩnh trong chế độ debug