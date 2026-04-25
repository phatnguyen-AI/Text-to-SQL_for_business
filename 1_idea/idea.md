# ĐỀ XUẤT DỰ ÁN: GIẢI PHÁP TRUY VẤN DỮ LIỆU TỰ ĐỘNG CHO BUSINESS (TEXT-TO-SQL)

## 1. Tóm tắt dự án (Executive Summary)
Đề xuất phát triển một trợ lý dữ liệu thông minh, cho phép các phòng ban (Business/Operations/Marketing) tự động truy xuất dữ liệu từ cơ sở dữ liệu nội bộ bằng **ngôn ngữ tự nhiên** mà không cần viết code hay phụ thuộc vào Data Team. Giải pháp nhằm giải phóng nguồn lực và tăng tốc độ ra quyết định cho doanh nghiệp.

## 2. Thực trạng & Điểm nghẽn hiện tại (Pain Points)
- **Tốn thời gian chờ đợi:** Hiện tại, các bộ phận Business mất từ **30 đến 120 phút** (có khi vài ngày) để yêu cầu và nhận được một dữ liệu/báo cáo ad-hoc.
- **Tắc nghẽn tại Data Team (Bottleneck):** Đội ngũ Data đang bị quá tải bởi các yêu cầu truy xuất dữ liệu vụn vặt, lặp đi lặp lại, không còn thời gian tập trung vào phân tích chuyên sâu mang lại giá trị cốt lõi.

### Đánh giá Hiệu quả Đầu tư (Estimated Business Impact - ROI)
- Trung bình mỗi query mất **~60 phút**.
- Khối lượng: **~20 query/ngày** (từ các team Business).
→ Thời gian tiêu tốn: **20 giờ/ngày** → **~400 giờ/tháng**.
- Nếu tính chi phí 1 giờ nhân sự = 100k VNĐ:
Tiết kiệm **~40 triệu VNĐ/tháng** chi phí vận hành ẩn, đồng thời giải phóng hoàn toàn thời gian của Data Team.

## 3. Kiến trúc Giải pháp & Use-case
### 3.1 Tình huống sử dụng điển hình (Typical Use Cases)
Biến các câu hỏi nghiệp vụ hàng ngày thành số liệu ngay lập tức:
- *"Doanh thu tháng 3 theo miền là bao nhiêu?"*
- *"Top 5 khách hàng theo giá trị đơn hàng trong quý này?"*
- *"Tỷ lệ chuyển đổi của chiến dịch marketing X ngày hôm qua?"*

### 3.2 Kiến trúc Hệ thống (System Overview)
Kiến trúc được thiết kế tối ưu và bảo mật:
🏗️ `User` → `API` → `LLM (Query Planner)` → `SQL Generator` → `Validator (Security)` → `Database (Read-only)` → `Result + Explanation`

## 4. Quản trị Rủi ro & Chiến lược Đảm bảo (Risk & Reliability)
1. **Bảo mật & An toàn dữ liệu (Security):** 
   - Hệ thống chỉ được cấp quyền **Đọc (Read-only)**, tuyệt đối không thay đổi/xóa dữ liệu.
   - Áp dụng phân quyền (RBAC - Role-Based Access Control) chặt chẽ.
2. **Chiến lược Độ tin cậy (Reliability Strategy - Chống Hallucination):** 
   - Nếu *confidence thấp* → Yêu cầu user xác nhận lại.
   - Nếu *query thất bại (fail)* → Hệ thống auto-debug và tự động retry.
   - Nếu *câu hỏi mơ hồ (ambiguous)* → Hệ thống sẽ hỏi lại để làm rõ ngữ cảnh.
3. **Giới hạn & Khắc phục (Known Limitations & Mitigation):**
   - *Rủi ro:* Query phức tạp (multi-join) có thể sai sót; Business dùng từ lóng mơ hồ; Schema thay đổi liên tục.
   - *Khắc phục:* Áp dụng cơ chế **Schema Retrieval** (chỉ trích xuất schema cần thiết), **Glossary Mapping** (từ điển chuẩn hóa thuật ngữ Business thành DB), và **Logging** để liên tục cải tiến.

## 5. Tiêu chí Thành công & Chiến lược Triển khai
### 5.1 Tiêu chí Thành công Giai đoạn 1 (Phase 1 Success Criteria)
Đo lường hiệu quả rõ ràng qua các chỉ số:
- **Độ chính xác (Accuracy):** ≥ 75%
- **Độ trễ (Latency):** < 2s
- **Chi phí (Cost/query):** < $0.005
- **Độ hài lòng người dùng (User satisfaction):** ≥ 80%

### 5.2 Chiến lược Áp dụng (Adoption Strategy)
Công cụ tốt cần được sử dụng rộng rãi, do đó cần:
- Giao diện người dùng (UI) **đơn giản**, mô phỏng ứng dụng Chat quen thuộc.
- Tổ chức các buổi **training ngắn** tập trung cho Business team.
- **Demo trực quan** các use-case thường gặp sát với nghiệp vụ hàng ngày.

### 5.3 Đề xuất Bước tiếp theo (Next Steps)
- **Phase 1 (Proof of Concept - PoC):** Triển khai thử nghiệm 2-4 tuần trên dữ liệu Sale/Marketing để kiểm chứng các Tiêu chí Thành công.
- **Phase 2:** Đánh giá thực tế và Demo trực tiếp cho Ban Giám đốc để phê duyệt triển khai toàn công ty.