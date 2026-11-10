# Tài khoản và phân quyền

**Bản cập nhật giao diện và workflow:** [role-workspaces.md](role-workspaces.md)
là tài liệu quyền hiện tại. Bảng dưới mô tả quyền nền; việc ghi Incident,
phân công, hành động và IOC phải đi qua các endpoint workflow chuyên biệt.

Ứng dụng hỗ trợ 7 vai trò. Tài khoản `admin` hiện có trở thành Admin, giữ mật khẩu cấu hình khi khởi tạo kho tài khoản lần đầu. Sau đó mật khẩu và vai trò được lưu trong `backend/accounts.sqlite3` (đã bỏ qua trong Git). Cần sao lưu file này cùng cấu hình ứng dụng; không xóa file để khởi tạo lại tài khoản.

Admin đăng nhập và tạo tài khoản tại màn hình **Tài khoản và phân quyền**. Có thể chọn vai trò, thay mật khẩu hoặc khóa tài khoản. Ứng dụng không tạo tài khoản mẫu với mật khẩu chung. Không thể tự khóa hoặc tự hạ quyền Admin đang đăng nhập. Tài khoản bị khóa mất quyền ở yêu cầu tiếp theo; đổi vai trò cũng có hiệu lực với phiên hiện có.

| Vai trò | Đọc dữ liệu | Tạo / sửa | Xóa |
|---|---|---|---|
| Admin | Tài khoản, tổ chức, tài sản, nhân viên, nhật ký | Tài khoản, danh mục, liên kết hồ sơ | Danh mục; chặn nhân viên đã tham gia Incident |
| SOC Manager | 14 bảng nghiệp vụ | 14 bảng nghiệp vụ | Bảng có khóa chính đơn |
| L1 | Sự cố, cảnh báo, tài sản, IOC, liên kết cảnh báo–tài sản, lịch sử trạng thái | Sự cố, cảnh báo | Không |
| L2 | Các bảng nghiệp vụ trừ tổ chức, nhân viên và phân công | Sự cố, IOC, liên kết sự cố–IOC, hành động xử lý | Không |
| L3 | Như L2 | Như L2 và kỹ thuật MITRE, liên kết sự cố–MITRE | Không |
| Incident Responder | Sự cố, cảnh báo, tài sản, IOC, liên kết sự cố–tài sản/IOC, hành động và lịch sử | Sự cố, hành động xử lý | Không |
| Threat Hunter | Sự cố, cảnh báo, tài sản, IOC, MITRE và các bảng liên kết liên quan | IOC, MITRE và các liên kết tương ứng với sự cố | Không |

Các quyền được kiểm tra tại backend, bao gồm truy cập API trực tiếp. Menu, thống kê và nút thao tác lấy quyền từ API. Bảng khóa chính ghép vẫn chỉ hỗ trợ đọc và tạo như phiên bản trước. Lịch sử trạng thái chỉ được Manager ghi trực tiếp; chưa có dịch vụ chuyển trạng thái tự ghi lịch sử.

Tài khoản đã liên kết với `MaNV` qua profile. Danh sách L2/Responder được lọc theo người được giao; cập nhật nghiệp vụ của hai vai trò này cũng kiểm tra phân công. Trang “Của tôi” chỉ tra đúng nhân viên của phiên đăng nhập. Quyền đọc hồ sơ liên quan được giữ để tương quan IOC; chưa có cơ chế cô lập dữ liệu giữa các tổ chức.

Mật khẩu được băm bằng scrypt với salt riêng. JWT chỉ mang tên tài khoản, quyền được đọc lại từ kho tài khoản cho mỗi yêu cầu. Đổi mật khẩu không thu hồi JWT đã cấp; khóa tài khoản sẽ ngăn truy cập ngay.

Kiểm tra từ thư mục `backend`: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`.
