Tạo một project đơn giản:

        Đầu vào 1 file lưu trữ câc luật (rules) 1 file chứa thông tin mục đích kiểm tra file chứa thông tin có valid hay invalid với các rules đã liệt kê có thể xem file rules và dummy để hiểu thêm (các rules sau này có thể sẽ phức tạp hơn)

        Yêu cầu: có một file thư viện chứa các hàm helper vd: check empty, check data type (numerical/alphabetical), check date valid,... có thể đề suất thêm
        một file gọi model llm API sẽ nằm trong .env (cung cấp sau) promt cho model đọc rules, và dịch ra các helper cần chạy cũng như đầu vào đầu ra của các helper đó sao cho check được xem là rules có được chấp hành không
        một file oschestra nhận danh sách các rules đã được dịch từ llm, và chạy chúng test xem chúng có hợp lệ không. output ra console kết quả sau khi check valid/invalid nếu invalid thì chỉ ra rules và field chưa chấp hành đúng rules.
    