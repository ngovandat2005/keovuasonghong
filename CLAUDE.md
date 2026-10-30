# Quy tắc làm việc trong dự án Keo Vữa Sông Hồng (Django)

Trả lời bằng tiếng Việt, ngắn gọn, đi thẳng vào việc.

## 1. Nguyên tắc cốt lõi
- **Chủ dự án bảo gì làm đó.** Không tự ý thay đổi theo ý mình, không tự thêm tính năng, không "tiện tay" sửa thứ khác.
- Chỉ sửa đúng phạm vi được yêu cầu. Thấy lỗi hoặc điểm nên cải thiện ngoài phạm vi thì **báo lại, không tự sửa**.
- Yêu cầu chưa rõ hoặc có nhiều cách hiểu thì **hỏi trước**, không đoán.
- Không đổi thiết kế, màu, font, bố cục, nội dung khi chưa được nói rõ.

## 2. Quy trình bắt buộc cho mỗi yêu cầu
1. **Hiểu**: nhắc lại yêu cầu bằng 1–2 câu nếu có chỗ mơ hồ, rồi hỏi.
2. **Xem**: đọc đúng file liên quan (dùng Grep/Read), không đọc tràn lan.
3. **Đề xuất**: với việc lớn (nhiều file, đổi giao diện, đổi dữ liệu) nêu kế hoạch ngắn và **chờ duyệt** trước khi sửa.
4. **Làm**: sửa nhỏ nhất có thể, giữ phong cách code hiện có.
5. **Kiểm tra**: chạy `python manage.py check`; sửa model thì chạy `python manage.py makemigrations --check`; sửa giao diện thì chạy skill `kiem-tra-mobile` và xem thử ở khổ 375px và máy tính.
5b. **Rà lỗi trước khi commit**: khi được yêu cầu commit, chạy skill `code-review` trên thay đổi và báo kết quả cho chủ dự án trước. Sửa code lớn thì có thể chạy thêm `simplify`; đụng tới đăng nhập, upload, form thì chạy `security-review`. Chỉ báo kết quả, không tự sửa.
6. **Báo cáo**: nêu đã sửa gì, ở file nào, chưa kiểm tra gì. Không nói "xong" khi chưa kiểm tra.

## 3. Git và triển khai
- **Không tự commit, không tự push.** Chỉ làm khi được yêu cầu.
- Trước khi commit, chạy `git status` và cho biết có thay đổi dở dang nào của chủ dự án lẫn vào không.
- Không `git reset --hard`, `push --force`, xóa nhánh, xóa file hay dữ liệu khi chưa được đồng ý.
- Sửa model thì phải kèm file migration, và nhắc chủ dự án chạy `migrate` trên server sau khi `git pull`.
- Không đụng vào `db.sqlite3`, `media/`, `.env`, `venv/`.

## 4. Quy tắc thiết kế (Design System)
Phong cách: tối giản, hiện đại, sạch, chuyên nghiệp, nền trắng, chữ làm trọng tâm, màu thương hiệu dùng có kiểm soát.

- **Font:** Bai Jamjuree. Không dùng font ngoài. (Việc thử font khác chỉ làm khi chủ dự án yêu cầu rõ, và phải dễ đổi lại.)
- **Cỡ chữ:** H1 36px/600/54px/#FF7E2E · H2 24px/600/31px/#808080 · H3 20px/600 · H4 18px/600 · Body 17px/400/27px/#000000.
- **Màu:** Cam #FF7E2E · Nâu #8C5A2B · Xám #808080 · Thành công #6F8A3A · Lỗi #7A0000 · Đen #000000 · Trắng #FFFFFF. Không dùng màu ngoài bảng này.
- **Nút:** nền nâu #8C5A2B, chữ trắng 16px, **không bo góc** (border-radius: 0). Không gradient.
- **Ảnh, banner, khung tài liệu:** không bo góc.
- **Đường kẻ:** 3px, màu #8C5A2B. **Hover:** chữ chuyển sang #FF7E2E.
- Không tự thêm gradient, shadow, hoặc trang trí thừa. Không dùng style mặc định của framework.
- Ba ngôn ngữ: Tiếng Việt, tiếng Trung, tiếng Anh. Chữ dài hơn thì bố cục vẫn phải ổn định.
- Responsive trên máy tính, máy tính bảng, điện thoại. Không để tràn ngang.
- Ảnh đuôi `.png`. Bài viết hoặc sản phẩm mới được đẩy lên đầu danh sách.

## 5. Tiết kiệm token
- Chỉ trả về đoạn code hoặc diff liên quan, không in lại cả file.
- Không giải thích kiến thức cơ bản nếu không được hỏi.
- Không đọc file nhị phân, media, `.sqlite3`, vendor lớn (xem `.agentignore`).
- Gọi công cụ ít và có mục tiêu.
