# 🇰🇷 HangulMate - Trợ lý học tiếng Hàn thông minh

![HangulMate Logo](https://placehold.co/600x300/e2f4ff/0078ff?text=HangulMate&font=montserrat)

## 📝 Giới thiệu

**HangulMate** là ứng dụng web hỗ trợ người Việt học tiếng Hàn một cách hiệu quả. Ứng dụng cung cấp các tính năng như phân tích ngữ pháp, tra cứu từ vựng, phát âm, ghi nhớ từ vựng (mnemonics) và nhiều công cụ học tập khác.

### Tính năng chính

- 📚 **Phân tích ngữ pháp**: Phân tích cấu trúc câu tiếng Hàn, giải thích quy tắc ngữ pháp
- 🔍 **Tra cứu từ vựng**: Hiển thị nghĩa, phiên âm và loại từ
- 🗣️ **Phát âm**: Nghe cách phát âm chính xác của từ và câu tiếng Hàn
- 🧠 **Ghi nhớ từ vựng**: Hệ thống ghi nhớ (mnemonics) giúp nhớ từ vựng dễ dàng
- 🌐 **Nhận diện văn bản từ hình ảnh**: Upload ảnh chứa văn bản tiếng Hàn để phân tích
- 📖 **Tạo bài học ngữ pháp**: Cung cấp bài học chi tiết về các chủ đề ngữ pháp
- 💬 **Phản hồi giao tiếp**: Trả lời các câu hỏi về ngôn ngữ và văn hóa Hàn Quốc

## 🚀 Cài đặt

### Yêu cầu hệ thống

- Python 3.8+ 
- pip (trình quản lý gói Python)
- virtualenv (khuyến nghị)

### Các bước cài đặt

1. **Clone repository**
   ```bash
   git clone https://github.com/yourusername/hanquocsarang.git
   cd hanquocsarang
   ```

2. **Tạo và kích hoạt môi trường ảo**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Cài đặt các thư viện phụ thuộc**
   ```bash
   pip install -r requirements.txt
   ```

4. **Cấu hình biến môi trường**
   - Tạo file `.env` trong thư mục gốc và thêm các thông tin sau:
     ```
     XAI_API_KEY=your_api_key_here
     SECRET_KEY=your_secret_key_here
     ```

5. **Chạy ứng dụng**
   ```bash
   python app.py
   ```

6. **Truy cập ứng dụng**
   - Mở trình duyệt và truy cập `http://127.0.0.1:5000`

## 📖 Hướng dẫn sử dụng

### 1. Phân tích văn bản tiếng Hàn

1. Nhập văn bản tiếng Hàn vào ô nhập liệu
2. Nhấn nút "Phân tích"
3. Xem kết quả phân tích bao gồm:
   - Từ vựng
   - Ngữ pháp
   - Dịch thuật
   - Ví dụ
   - Phát âm
   - Ghi chú văn hóa (nếu có)

### 2. Upload ảnh văn bản tiếng Hàn

1. Nhấp vào nút "Tải ảnh chứa văn bản tiếng Hàn"
2. Chọn ảnh chứa văn bản tiếng Hàn (JPG, PNG)
3. Nhấn nút "Phân tích"
4. Xem kết quả phân tích từ văn bản được trích xuất từ ảnh

### 3. Sử dụng tính năng Mnemonics

1. Nhập "ghi nhớ từ '[từ_tiếng_hàn]'" vào ô nhập liệu
   - Ví dụ: `ghi nhớ từ '안녕'` hoặc `mnemonics '학교'`
2. Nhấn nút "Phân tích"
3. Xem các phương pháp ghi nhớ, ví dụ và từ liên quan

### 4. Học ngữ pháp

1. Nhập câu hỏi về ngữ pháp vào ô nhập liệu
   - Ví dụ: `phân biệt 은/는 và 이/가` hoặc `cách sử dụng 으로/로`
2. Nhấn nút "Phân tích"
3. Xem bài học ngữ pháp chi tiết, bao gồm:
   - Định nghĩa
   - Cách dùng
   - So sánh (nếu có)
   - Lỗi thường gặp
   - Ví dụ
   - Bài tập

### 5. Phát âm

- Nhấn nút phát âm (biểu tượng loa) bên cạnh các từ/câu tiếng Hàn để nghe cách phát âm
- Sử dụng thanh điều chỉnh tốc độ phát âm ở góc dưới bên phải màn hình

## 🧩 Cấu trúc dự án

```
hanquocsarang/
├── app.py               # File chính của ứng dụng Flask
├── requirements.txt     # Danh sách thư viện phụ thuộc
├── .env                 # File cấu hình (không đưa lên git)
├── .gitignore           # Danh sách file/thư mục bỏ qua trong git
├── static/              # Thư mục chứa các file tĩnh
│   ├── css/             # Stylesheet
│   ├── js/              # JavaScript
│   └── images/          # Hình ảnh
└── templates/           # Thư mục chứa template HTML
    └── index.html       # File HTML chính của ứng dụng
```

## 🔧 Công nghệ sử dụng

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **CSS Framework**: Tailwind CSS
- **Icon**: Font Awesome
- **API**: X.AI API (Grok), Web Speech API
- **NLP**: Xử lý ngôn ngữ tự nhiên cho tiếng Hàn

## 📝 Câu trả lời kỳ vọng

Khi sử dụng HangulMate, bạn có thể kỳ vọng nhận được các loại phản hồi sau:

### 1. Phân tích từ vựng

```json
{
  "vocabulary": [
    {
      "hangul": "안녕하세요",
      "roman": "annyeonghaseyo",
      "meaning": "Xin chào",
      "pos": "Thán từ"
    },
    {
      "hangul": "감사합니다",
      "roman": "gamsahamnida",
      "meaning": "Cảm ơn",
      "pos": "Thán từ"
    }
  ]
}
```

### 2. Phân tích ngữ pháp

```json
{
  "grammar": "Câu này sử dụng cấu trúc '-아/어요' là dạng kết thúc câu thể hiện sự lịch sự ở mức độ trung bình, thường dùng trong giao tiếp hàng ngày.",
  "grammar_formula": {
    "formula": "Động từ + 아/어요",
    "explanation": "Đuôi 아/어요 được thêm vào sau động từ để biểu thị sự lịch sự trong hội thoại hàng ngày"
  }
}
```

### 3. Dịch thuật

```json
{
  "translation": {
    "original": "안녕하세요, 만나서 반갑습니다",
    "literal": "Xin chào, gặp được bạn tôi vui",
    "natural": "Xin chào, rất vui được gặp bạn"
  }
}
```

### 4. Mnemonics (Phương pháp ghi nhớ)

```json
{
  "word": "학교",
  "pronunciation": "hakgyo",
  "meaning": "Trường học",
  "mnemonics": [
    {
      "title": "Phân tích âm tiết",
      "description": "Học (학) + Giao (교) = Nơi giao lưu để học tập"
    },
    {
      "title": "Liên tưởng hình ảnh",
      "description": "Hãy tưởng tượng 'học' như 'học sinh' và 'gyo' như 'giáo viên' - Trường học là nơi học sinh gặp giáo viên"
    }
  ],
  "examples": [
    {
      "korean": "학교에 가요",
      "vietnamese": "Tôi đi đến trường"
    }
  ],
  "related_words": [
    {
      "word": "학생",
      "meaning": "Học sinh"
    },
    {
      "word": "교실",
      "meaning": "Lớp học"
    }
  ]
}
```

### 5. Bài học ngữ pháp

```json
{
  "topic": "Phân biệt 은/는 và 이/가",
  "definition": "은/는 và 이/가 đều là trợ từ chủ ngữ trong tiếng Hàn, nhưng có những khác biệt quan trọng về ngữ cảnh sử dụng và hàm ý.",
  "usage": "은/는 dùng để nhấn mạnh chủ đề (topic marker), trong khi 이/가 dùng để xác định chủ ngữ (subject marker).",
  "comparison": "은/는 thường dùng khi muốn đối lập hoặc so sánh, còn 이/가 thường dùng khi giới thiệu thông tin mới.",
  "common_mistakes": "Người học thường nhầm lẫn khi nào dùng 은/는 và khi nào dùng 이/가. Lỗi phổ biến là sử dụng 은/는 cho tất cả các chủ ngữ.",
  "examples": [
    "저는 한국 사람이에요 (Tôi là người Hàn Quốc) - Dùng 는 vì đang nói về chủ đề 'tôi'",
    "누가 왔어요? (Ai đã đến?) - Dùng 가 vì đang hỏi về một chủ ngữ chưa xác định"
  ],
  "exercise": "Hãy hoàn thành các câu sau bằng 은/는 hoặc 이/가 phù hợp:\n1. 저___ 학생이에요.\n2. 이것___ 뭐예요?\n3. 누구___ 한국어를 공부해요?"
}
```

## 🔄 Cập nhật và bảo trì

### Khắc phục sự cố

1. **Lỗi kết nối API**:
   - Kiểm tra API key trong file `.env`
   - Đảm bảo kết nối internet ổn định

2. **Lỗi phát âm không hoạt động**:
   - Đảm bảo trình duyệt hỗ trợ Web Speech API
   - Kiểm tra quyền truy cập microphone nếu sử dụng tính năng ghi âm

3. **Lỗi CSS/Layout**:
   - Xóa cache trình duyệt
   - Đảm bảo Tailwind CSS đã được nạp đúng cách

## 👥 Đóng góp

Chúng tôi luôn hoan nghênh đóng góp để cải thiện HangulMate! Nếu bạn muốn đóng góp:

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`)
4. Push lên branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📄 Giấy phép

Phân phối theo giấy phép MIT. Xem `LICENSE` để biết thêm thông tin.

## 📞 Liên hệ

Email: your.email@example.com

---

Made with ❤️ by [Your Name]
"# Korean-AI-Helper" 
