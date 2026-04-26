# Bộ 50 Câu Hỏi Test Text-to-SQL (Dựa trên BusinessDB Schema)

Dưới đây là 50 câu hỏi từ cơ bản đến nâng cao được thiết kế sát với cấu trúc Database của bạn (gồm 4 bảng: `Customers`, `Products`, `Orders`, `MarketingCampaigns`). 
Bạn có thể copy trực tiếp các câu này dán vào giao diện Streamlit để kiểm tra độ thông minh của con AI (Ollama/Qwen).

---

### Mức độ 1: Truy vấn cơ bản (Chỉ cần dùng SELECT, WHERE đơn giản)
1. Liệt kê tất cả các khách hàng trong hệ thống.
2. Tìm danh sách khách hàng ở "Miền Bắc".
3. Khách hàng nào đăng ký tài khoản vào ngày 15/01/2023?
4. Liệt kê tất cả các sản phẩm hiện có.
5. Danh sách các sản phẩm thuộc danh mục "Phụ kiện" là gì?
6. Sản phẩm nào có giá bán trên 10 triệu đồng?
7. Giá của "Laptop Dell XPS" là bao nhiêu?
8. Liệt kê tất cả các đơn hàng đã "Hoàn thành".
9. Có những đơn hàng nào bị "Đã hủy"?
10. Cho biết thông tin chiến dịch marketing có ngân sách lớn hơn 40 triệu.

### Mức độ 2: Hàm tổng hợp (SUM, AVG, COUNT, MIN, MAX)
11. Hệ thống hiện có tổng cộng bao nhiêu khách hàng?
12. Có tất cả bao nhiêu sản phẩm trong cơ sở dữ liệu?
13. Tổng ngân sách của tất cả các chiến dịch marketing là bao nhiêu?
14. Tổng số lượt chuyển đổi (conversions) từ tất cả chiến dịch là bao nhiêu?
15. Trung bình một chiến dịch marketing tiêu tốn bao nhiêu ngân sách?
16. Tổng giá trị của tất cả các đơn hàng là bao nhiêu tiền?
17. Doanh thu của các đơn hàng đã "Hoàn thành" là bao nhiêu?
18. Giá trị trung bình của một đơn hàng là bao nhiêu?
19. Mức giá trung bình của các sản phẩm là bao nhiêu?
20. Đơn hàng có giá trị nhỏ nhất là bao nhiêu tiền?

### Mức độ 3: Gom nhóm dữ liệu (GROUP BY)
21. Mỗi khu vực (Region) có bao nhiêu khách hàng?
22. Có bao nhiêu sản phẩm trong từng danh mục (Category)?
23. Tổng giá trị đơn hàng theo từng trạng thái (Status) là bao nhiêu?
24. Có bao nhiêu đơn hàng theo từng trạng thái?
25. Mức giá trung bình của sản phẩm theo từng danh mục là bao nhiêu?
26. Mỗi khách hàng đã đặt bao nhiêu đơn hàng?
27. Doanh thu tổng cộng mang lại từ từng khu vực là bao nhiêu? *(Lưu ý: AI phải JOIN bảng)*
28. Tính tổng số lượt chuyển đổi theo từng tháng bắt đầu chiến dịch.
29. Khu vực nào mang lại nhiều đơn hàng nhất?
30. Tổng chi tiêu của mỗi khách hàng là bao nhiêu?

### Mức độ 4: Kết hợp nhiều bảng (JOIN)
31. Liệt kê tên khách hàng và tổng giá trị đơn hàng của họ.
32. Khách hàng "Nguyễn Văn A" đã mua tổng cộng bao nhiêu tiền?
33. Tên của những khách hàng có đơn hàng đang ở trạng thái "Đang giao" là gì?
34. Khách hàng ở "Miền Nam" đã chi tổng cộng bao nhiêu tiền?
35. Hiển thị tên khách hàng, ngày đăng ký và trạng thái đơn hàng bị "Đã hủy".
36. Ai là người đã mua đơn hàng có giá trị 26.500.000?
37. Khách hàng ở "Miền Bắc" có bao nhiêu đơn hàng đã hoàn thành?
38. Liệt kê thông tin các đơn hàng (ID, số tiền) kèm theo tên khách hàng tương ứng.
39. Tính giá trị đơn hàng trung bình của khách hàng ở "Miền Trung".
40. Có khách hàng nào chưa từng mua hàng không? *(AI cần dùng LEFT JOIN hoặc NOT IN - mặc dù dữ liệu hiện tại ai cũng có đơn)*

### Mức độ 5: Sắp xếp, Lọc nâng cao & Logical Math (ORDER BY, TOP, DATE, Toán học)
41. Top 3 đơn hàng có giá trị cao nhất là những đơn nào?
42. Sản phẩm nào đắt tiền nhất hệ thống?
43. 2 sản phẩm có giá rẻ nhất là gì?
44. Hiển thị 2 khu vực có số lượng khách hàng đông nhất.
45. Chiến dịch marketing nào mang lại nhiều lượt chuyển đổi (conversions) nhất?
46. Tổng doanh thu trong tháng 3 năm 2024 là bao nhiêu?
47. Có bao nhiêu khách hàng đăng ký trong quý 1 năm 2023 (tháng 1 đến tháng 3)?
48. Tính chi phí trên mỗi lượt chuyển đổi (Budget chia cho Conversions) của từng chiến dịch.
49. Liệt kê các đơn hàng được đặt trong thời gian diễn ra chiến dịch "Khuyến mãi tháng 3" (từ 01/03 đến 31/03).
50. Khách hàng nào có tổng chi tiêu cao hơn mức chi tiêu trung bình của tất cả khách hàng?
