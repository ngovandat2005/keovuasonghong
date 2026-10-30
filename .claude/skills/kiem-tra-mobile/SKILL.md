---
name: kiem-tra-mobile
description: Kiểm tra giao diện điện thoại của website (tràn ngang, phần tử vượt khung) bằng Chrome thật ở khổ 320/375px. Dùng khi sửa CSS/template giao diện hoặc khi được yêu cầu rà soát mobile.
---

Chỉ kiểm tra và báo cáo, không tự sửa nếu chủ dự án chưa duyệt.

## Các bước
1. Chạy server tạm: `python manage.py runserver 127.0.0.1:8123 --noreload` (chạy nền). Sau khi sửa template phải khởi động lại vì `--noreload` giữ cache template.
2. Cài công cụ vào thư mục tạm, không cài vào dự án:
   `python -m venv <scratchpad>/pw && <scratchpad>/pw/Scripts/pip install playwright`
3. Chạy: `<scratchpad>/pw/Scripts/python .claude/skills/kiem-tra-mobile/audit.py 320 http://127.0.0.1:8123`
   (tham số: độ rộng màn hình, địa chỉ gốc). Script tự lấy danh sách trang từ `/sitemap.xml`. Dùng Chrome cài sẵn trên máy.
4. Trang nào báo `OVERFLOW` thì tìm phần tử rộng quá khung, báo lại cho chủ dự án kèm đề xuất sửa.
5. Chụp ảnh vài trang chính ở 375px để xem bằng mắt: trang chủ, giới thiệu, sản phẩm, chi tiết sản phẩm, tin tức, đại lý.
6. Tắt server tạm khi xong.

## Lỗi hay gặp ở dự án này
- Lưới `grid-template-columns: 1fr` trong media query bị nội dung đẩy rộng. Dùng `minmax(0, 1fr)`.
- Bảng trong nội dung soạn từ admin cần `overflow-x: auto` bọc ngoài.
- Git Bash đổi đường dẫn bắt đầu bằng `/` thành đường dẫn Windows. Đặt `MSYS_NO_PATHCONV=1` khi truyền URL.
