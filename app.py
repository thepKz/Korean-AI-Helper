from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from flask_cors import CORS
import json
import time
import base64
import re
import logging
import uuid
from flask_session import Session
from konlpy.tag import Okt
import requests
from io import BytesIO
import tempfile
from werkzeug.utils import secure_filename
import PyPDF2
import nltk
from nltk.tokenize import sent_tokenize
import io

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 giờ

Session(app)

# Khởi tạo client với API key
client = OpenAI(api_key=os.getenv("XAI_API_KEY"), base_url="https://api.x.ai/v1")

# Cấu hình các model
MODELS = {
    "text": "grok-2-1212",
    "vision": "grok-2-vision-1212",
    # "image": "grok-2-image-1212"
}

# Tạo thư mục để lưu dữ liệu trích xuất
PDF_DATA_DIR = os.path.join('static', 'pdf_data')
os.makedirs(PDF_DATA_DIR, exist_ok=True)

# Khởi tạo NLTK (nếu cần)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# --- HangulMate System Prompt ---
HANGULMATE_SYSTEM_PROMPT = """Bạn là HangulMate, một trợ lý gia sư tiếng Hàn chuyên nghiệp, thân thiện và đầy kiến thức. Mục tiêu của bạn là giảng dạy tiếng Hàn từ cơ bản đến nâng cao, giúp người học tiếp thu kiến thức một cách hiệu quả.

**Chế độ hoạt động:**
1.  **Phân tích văn bản/ảnh:** Khi người dùng cung cấp văn bản tiếng Hàn (hoặc ảnh có chứa văn bản tiếng Hàn), bạn phân tích theo cấu trúc JSON bên dưới. Ưu tiên phân tích văn bản nhập vào nếu có cả văn bản và ảnh. Nếu chỉ có ảnh, hãy mô tả ngắn gọn nội dung ảnh bằng tiếng Hàn và phân tích câu mô tả đó.
2.  **Bài học ngữ pháp:** Khi yêu cầu là về một chủ đề ngữ pháp cụ thể (vd: "phân biệt 은/는 và 이/가"), cung cấp bài học theo cấu trúc JSON ngữ pháp.
3.  **Tìm từ đồng nghĩa:** Khi người dùng yêu cầu tìm từ đồng nghĩa (synonym) hoặc từ có nghĩa tương tự với một từ tiếng Hàn hoặc tiếng Việt, cung cấp danh sách các từ đồng nghĩa kèm phiên âm và ví dụ sử dụng. Trả về phản hồi trong trường "conversation_response".
4.  **Giao tiếp:** Khi yêu cầu không thuộc các loại trên, xem đó là câu hỏi giao tiếp thông thường. Trả lời bằng tiếng Việt hoặc tiếng Hàn (tùy ngữ cảnh) với giọng điệu thân thiện, lịch sự. Trả về JSON chỉ chứa khóa "conversation_response".

**Cấu trúc JSON cho Phân tích (Văn bản/Ảnh):**
```json
{
    "vocabulary": [
        {"hangul": "안녕하세요", "roman": "annyeonghaseyo", "meaning": "Xin chào", "pos": "Thán từ"},
        {"hangul": "...", "roman": "...", "meaning": "...", "pos": "..."}
    ],
    "grammar": "Cấu trúc ngữ pháp....",
    "grammar_formula": {
        "formula": "Cấu trúc ngữ pháp",
        "explanation": "Giải thích về công thức ngữ pháp"
    },
    "translation": {
        "original": "Câu gốc tiếng Hàn...",
        "literal": "Dịch nghĩa đen...",
        "natural": "Dịch tự nhiên..."
    },
    "examples": [
        "Ví dụ 1...",
        "Ví dụ 2..."
    ],
    "culture": "Ghi chú văn hóa (nếu có)...",
    "pronunciation": "안녕하세요 (annyeonghaseyo) [Tiếng Việt: ăn nyeong ha sê yo]"
}
```

**Lưu ý về trường pronunciation:**
Đảm bảo trường pronunciation tuân theo định dạng "tiếng Hàn (phiên âm)" không còn phần phát âm tiếng Việt vì hệ thống đã được cập nhật để không đọc phần tiếng Việt.

**Lưu ý về trường grammar:**
Grammar có thể được trả về dưới một trong các dạng sau:
1. String đơn giản: Khi chỉ có một luật ngữ pháp cần giải thích
2. Mảng các string: Khi có nhiều luật ngữ pháp liên quan cần giải thích
3. Mảng các object, mỗi object có dạng {"name": "Tên luật", "description": "Mô tả luật", "formula": "Công thức ngữ pháp"}
4. Object với key là tên luật và value là mô tả: {"luật A": "mô tả A", "luật B": "mô tả B"}

**Cấu trúc JSON cho Bài học ngữ pháp:**
```json
{
    "topic": "Chủ đề ngữ pháp...",
    "definition": "Định nghĩa...",
    "formula": "Công thức ngữ pháp...",
    "usage": "Cách dùng...",
    "comparison": "So sánh (nếu có)...",
    "common_mistakes": "Lỗi thường gặp...",
    "examples": [
        "Ví dụ 1...",
        "Ví dụ 2..."
    ],
    "exercise": "Bài tập thực hành..."
}
```

**Cấu trúc JSON cho Giao tiếp hoặc Tìm từ đồng nghĩa:**
```json
{
    "conversation_response": "Câu trả lời của bạn..."
}
```

**Lưu ý quan trọng:**
*   Luôn xác định đúng chế độ hoạt động (Phân tích, Bài học, Tìm từ đồng nghĩa, Giao tiếp) dựa trên nội dung đầu vào.
*   Đảm bảo trả về ĐÚNG MỘT JSON object duy nhất theo cấu trúc tương ứng. Không thêm các trường không được yêu cầu.
*   Khi nói về ngữ pháp, luôn cố gắng cung cấp công thức ngữ pháp rõ ràng, gọn gàng trong trường formula.
*   Giọng điệu: Thân thiện, tôn trọng, kiên nhẫn và khích lệ như một người thầy tận tâm. Sử dụng xưng hô "tôi - bạn" hoặc "thầy/cô - bạn".
*   Ngôn ngữ phản hồi: Chủ yếu là tiếng Việt, trừ khi trả lời câu giao tiếp tiếng Hàn.
*   Đánh giá mức độ khó: Khi phân tích văn bản, nêu rõ mức độ khó (sơ cấp, trung cấp, cao cấp) nếu có thể.
*   Phần romanization (phiên âm Latin): Đảm bảo chính xác, nhất quán theo chuẩn phổ biến.
"""

@app.route('/')
def hangulmate_page():
    return render_template('index.html')

# Route để xử lý phân tích tiếng Hàn (API endpoint)
@app.route('/analyze_korean', methods=['POST'])
def analyze_korean():
    data = request.get_json()
    korean_text = data.get('text', '')
    image_data = data.get('image') # Nhận dữ liệu ảnh base64

    # Kiểm tra xem có input không
    if not korean_text and not image_data:
        return jsonify({'error': 'Vui lòng nhập văn bản hoặc tải ảnh lên.'}), 400

    try:
        # --- Chuẩn bị messages cho LLM ---
        messages = [
            {"role": "system", "content": HANGULMATE_SYSTEM_PROMPT}
        ]
        
        user_content = []
        use_vision_model = False

        if korean_text:
            user_content.append({"type": "text", "text": korean_text})

        if image_data:
            # Kiểm tra định dạng base64 hợp lệ
            try:
                if "," in image_data:
                    # Nếu image_data chứa header thì đã được tách rồi
                    image_data = image_data.split(",")[1]
                    
                # Kiểm tra xem chuỗi base64 có hợp lệ không
                base64.b64decode(image_data)
            except Exception as base64_error:
                logging.error(f"Lỗi xử lý dữ liệu base64: {base64_error}")
                return jsonify({'error': 'Định dạng ảnh không hợp lệ, vui lòng tải ảnh JPG hoặc PNG.'}), 400
                
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"} # Giả định là JPEG, có thể cần xác định loại MIME nếu khác
            })
            use_vision_model = True # Cần dùng model vision nếu có ảnh
            # Nếu chỉ có ảnh, thêm yêu cầu mô tả và phân tích
            if not korean_text:
                 user_content.insert(0, {"type": "text", "text": "Vui lòng xem hình ảnh này, nếu có văn bản tiếng Hàn trong đó, hãy trích xuất, mô tả và phân tích nó theo yêu cầu. Nếu không có văn bản tiếng Hàn, hãy mô tả ngắn gọn nội dung của hình ảnh bằng tiếng Việt."})

        messages.append({"role": "user", "content": user_content})

        # Chọn model phù hợp
        model_to_use = MODELS["vision"] if use_vision_model else MODELS["text"]
        logging.info(f"Sử dụng model: {model_to_use}")

        # Thêm hướng dẫn rõ ràng hơn khi user muốn tạo hội thoại hoặc mẫu văn bản
        if korean_text and ('tạo cuộc hội thoại' in korean_text.lower() or 
                           'tạo đoạn hội thoại' in korean_text.lower() or
                           'tạo mẫu hội thoại' in korean_text.lower() or
                           'mẫu câu' in korean_text.lower()):
            logging.info("Phát hiện yêu cầu tạo hội thoại/mẫu câu")
            conversation_messages = messages.copy()
            conversation_messages.append({"role": "user", "content": [
                {"type": "text", "text": "Sau khi tạo đoạn hội thoại/mẫu câu, hãy phân tích chi tiết các ngữ pháp sử dụng trong đoạn hội thoại/mẫu câu đó. Trả về kết quả trong một JSON bao gồm cả conversation_response, vocabulary, grammar và examples."}
            ]})
            
            response = client.chat.completions.create(
                model=model_to_use,
                messages=conversation_messages,
                max_tokens=2000,
                temperature=0.5,
                response_format={"type": "json_object"}
            )
        else:
            response = client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                max_tokens=2000, # Tăng thêm cho vision và phân tích phức tạp
                temperature=0.5,
                response_format={"type": "json_object"}
            )

        analysis_result_str = response.choices[0].message.content

        # Parse chuỗi JSON nhận được từ LLM
        try:
            analysis_result = json.loads(analysis_result_str)
            
            # Kiểm tra lỗi SOURCE_LANG_VI và xử lý
            if "error" in analysis_result and "SOURCE_LANG_VI" in analysis_result["error"]:
                # Nếu là lỗi ngôn ngữ nguồn là tiếng Việt, điều chỉnh phân tích
                logging.warning("Phát hiện lỗi SOURCE_LANG_VI, thử phân tích lại với ngôn ngữ nguồn tiếng Việt")
                return jsonify({
                    "conversation_response": "Đã phát hiện văn bản tiếng Việt trong ảnh. Hệ thống HangulMate được thiết kế để phân tích văn bản tiếng Hàn. Vui lòng tải lên ảnh có văn bản tiếng Hàn để được phân tích.",
                    "translation": {
                        "original": "",
                        "literal": "",
                        "natural": "Vui lòng tải lên ảnh có văn bản tiếng Hàn để được phân tích."
                    }
                })
                
            return jsonify(analysis_result)
            
        except json.JSONDecodeError as json_err:
             logging.error(f"Lỗi giải mã JSON từ LLM: {json_err}")
             # Đảm bảo analysis_result_str được định nghĩa trước khi truy cập
             raw_response_content = analysis_result_str if 'analysis_result_str' in locals() else "[Không lấy được phản hồi raw]"
             logging.error(f"Dữ liệu nhận được: {raw_response_content}")
             error_message = "Lỗi khi xử lý phản hồi từ AI (định dạng không đúng JSON). Vui lòng thử lại hoặc thay đổi câu hỏi."
             return jsonify({'error': error_message, 'raw_response': raw_response_content}), 500

    except Exception as e:
        logging.error(f"Lỗi khi phân tích tiếng Hàn bằng LLM: {e}")
        # import traceback
        # logging.error(traceback.format_exc())
        error_message = f"Xin lỗi, đã có lỗi xảy ra trong quá trình phân tích: {str(e)}"
        # Trả về lỗi raw nếu có thể và là lỗi JSON
        raw_response_content = analysis_result_str if 'analysis_result_str' in locals() else None
        if raw_response_content:
             return jsonify({'error': error_message, 'raw_response': raw_response_content}), 500
        else:
            return jsonify({'error': error_message}), 500

# Route để xử lý phát âm tiếng Hàn
@app.route('/tts_korean', methods=['POST'])
def text_to_speech_korean():
    try:
        data = request.get_json()
        text = data.get('text', '')
        speed = data.get('speed', 1.0)
        
        if not text:
            return jsonify({'error': 'Vui lòng cung cấp văn bản tiếng Hàn để phát âm.'}), 400
        
        # Xử lý tốc độ để đảm bảo giá trị hợp lệ
        try:
            speed = float(speed)
            if speed < 0.5:
                speed = 0.5
            elif speed > 1.5:
                speed = 1.5
        except:
            speed = 1.0
        
        # Phương pháp 1: Sử dụng API Google Text-to-Speech
        # Lưu ý: Nếu sử dụng API này cho mục đích thương mại, cần kiểm tra lại điều khoản sử dụng
        try:
            # Tạo tham số URL
            params = {
                'ie': 'UTF-8',
                'tl': 'ko-KR',  # Ngôn ngữ tiếng Hàn
                'q': text,
                'client': 'tw-ob',
                'speed': speed
            }
            
            # Giới hạn độ dài của text
            if len(text) > 200:
                text = text[:197] + '...'
                params['q'] = text
            
            # Gọi Google TTS API
            response = requests.get(
                'https://translate.google.com/translate_tts',
                params=params,
                headers={'Referer': 'https://translate.google.com/'}
            )
            
            if response.status_code == 200:
                # Trả về file âm thanh dưới dạng base64
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                return jsonify({
                    'success': True,
                    'audio': audio_base64,
                    'format': 'mp3'
                })
            else:
                raise Exception(f"Lỗi API TTS: {response.status_code}")
                
        except Exception as tts_error:
            logging.error(f"Lỗi khi gọi TTS API: {tts_error}")
            # Nếu không thể sử dụng Google TTS, trả về thông báo lỗi
            return jsonify({
                'error': f"Không thể tạo phát âm cho văn bản: {str(tts_error)}",
                'message': 'Vui lòng sử dụng chức năng phát âm tích hợp trong trình duyệt.'
            }), 500
            
    except Exception as e:
        logging.error(f"Lỗi trong route phát âm: {e}")
        return jsonify({'error': f"Lỗi hệ thống: {str(e)}"}), 500

# Route để lấy các biến thể câu tiếng Hàn (dạng tương đương)
@app.route('/korean_variations', methods=['POST'])
def get_korean_variations():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Vui lòng cung cấp văn bản tiếng Hàn.'}), 400
        
        # Sử dụng model để lấy các biến thể câu
        messages = [
            {"role": "system", "content": """Bạn là một chuyên gia ngôn ngữ tiếng Hàn. Nhiệm vụ của bạn là tạo ra các biến thể của câu tiếng Hàn đầu vào với các cấp độ ngôn ngữ khác nhau (trang trọng, lịch sự, thân mật, v.v.).

Hãy trả về dữ liệu dưới dạng JSON với cấu trúc sau:
```json
{
    "original": "Câu gốc",
    "variations": [
        {"text": "Biến thể 1", "description": "Mô tả (ví dụ: Dạng thân mật)", "level": "Cấp độ ngôn ngữ (vd: 반말, 존댓말, etc.)", "vietnamese": "Ý nghĩa tương đương bằng tiếng Việt"},
        {"text": "Biến thể 2", "description": "Mô tả (ví dụ: Dạng trang trọng)", "level": "Cấp độ ngôn ngữ", "vietnamese": "Ý nghĩa tương đương bằng tiếng Việt"}
    ],
    "grammar_explanation": {
        "rules": "Giải thích ngắn gọn về luật ngữ pháp áp dụng",
        "levels": "Mô tả các cấp độ giao tiếp trong tiếng Hàn",
        "endings": "Giải thích về các đuôi kết thúc câu khác nhau",
        "examples": "Ví dụ về việc áp dụng luật ngữ pháp"
    }
}
```

Chỉ trả về JSON, không thêm bất kỳ giải thích nào khác. Đảm bảo mỗi biến thể đều có trường 'vietnamese' để người dùng hiểu được ý nghĩa bằng tiếng Việt."""},
            {"role": "user", "content": f"Tạo các biến thể của câu tiếng Hàn sau và cung cấp ý nghĩa tiếng Việt cho mỗi biến thể: {text}"}
        ]
        
        # Gọi API để lấy các biến thể
        response = client.chat.completions.create(
            model=MODELS["text"],
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result_str = response.choices[0].message.content
        
        # Parse kết quả JSON
        variations = json.loads(result_str)
        
        return jsonify(variations)
        
    except json.JSONDecodeError as json_err:
        logging.error(f"Lỗi giải mã JSON từ LLM khi lấy biến thể: {json_err}")
        error_message = "Lỗi khi xử lý phản hồi từ AI (định dạng không đúng JSON). Vui lòng thử lại."
        return jsonify({'error': error_message}), 500
    except Exception as e:
        logging.error(f"Lỗi khi lấy biến thể câu tiếng Hàn: {e}")
        return jsonify({'error': f"Lỗi khi xử lý yêu cầu: {str(e)}"}), 500

# API endpoint cho phân tích giọng nói (giả lập)
@app.route('/analyze_voice', methods=['POST'])
def analyze_voice():
    try:
        # Kiểm tra xem có file audio không
        if 'audio' not in request.files:
            return jsonify({'error': 'Không tìm thấy file audio'}), 400
            
        audio_file = request.files['audio']
        reference_text = request.form.get('reference_text', '')
        
        # Kiểm tra tính hợp lệ của file
        if audio_file.filename == '':
            return jsonify({'error': 'Tên file không hợp lệ'}), 400
            
        # Đây chỉ là mô phỏng, trong thực tế bạn sẽ gửi file âm thanh đến API phân tích giọng nói
        # Ví dụ: Google Cloud Speech-to-Text API
        
        # Mô phỏng kết quả phân tích
        import random
        
        # Tạo kết quả mô phỏng
        overall_score = random.randint(70, 95)
        
        # Tạo điểm số cho từng âm tiết
        syllable_scores = []
        if reference_text:
            for syllable in reference_text:
                if '가' <= syllable <= '힣':  # Kiểm tra ký tự Hangul
                    syllable_scores.append({
                        'syllable': syllable,
                        'score': random.randint(65, 100),
                        'feedback': random.choice([
                            'Phát âm chính xác', 
                            'Cần cải thiện độ cao', 
                            'Cần kéo dài âm hơn', 
                            'Tốt'
                        ])
                    })
        
        # Trả về kết quả
        return jsonify({
            'success': True,
            'overall_score': overall_score,
            'syllable_scores': syllable_scores,
            'general_feedback': 'Phát âm của bạn tốt. Hãy tiếp tục luyện tập!'
        })
        
    except Exception as e:
        logging.error(f"Lỗi khi phân tích giọng nói: {e}")
        return jsonify({'error': f"Lỗi khi phân tích giọng nói: {str(e)}"}), 500





# API để tạo phương pháp ghi nhớ từ vựng
@app.route('/create_mnemonics', methods=['POST'])
def create_mnemonics():
    data = request.json
    word = data.get('word', '')
    meaning = data.get('meaning', '')
    
    if not word:
        return jsonify({"error": "Không tìm thấy từ vựng"}), 400
    
    # Sử dụng OpenAI API để tạo phương pháp ghi nhớ
    try:
        prompt = f"""
        Tạo phương pháp ghi nhớ Mnemonics cho từ vựng tiếng Hàn "{word}" {f'có nghĩa là "{meaning}"' if meaning else ''}.
        Hãy trả về kết quả dưới dạng JSON với định dạng sau:
        {{
            "word": "{word}",
            "pronunciation": "<phiên âm tiếng Hàn>",
            "meaning": "<nghĩa tiếng Việt chi tiết>",
            "mnemonics": [
                {{"method": "<tên phương pháp>", "description": "<mô tả cụ thể về cách ghi nhớ>"}},
                ...
            ],
            "example_sentences": [
                {{"korean": "<câu ví dụ tiếng Hàn>", "vietnamese": "<nghĩa tiếng Việt>", "pronunciation": "<phiên âm>"}},
                ...
            ],
            "related_words": [
                {{"word": "<từ liên quan>", "meaning": "<nghĩa>"}},
                ...
            ]
        }}

        Các phương pháp ghi nhớ có thể bao gồm:
        1. Liên kết âm thanh: Liên kết âm của từ tiếng Hàn với từ/cụm từ tiếng Việt có âm tương tự
        2. Phân tích cấu trúc từ: Phân tích các thành phần cấu tạo nên từ
        3. Liên kết hình ảnh: Tạo hình ảnh liên tưởng giúp ghi nhớ
        4. Kể câu chuyện: Tạo câu chuyện nhỏ liên quan đến từ
        5. Kết hợp các phương pháp trên

        Hãy sáng tạo, cụ thể và chi tiết khi mô tả phương pháp ghi nhớ.
        Đưa ra ít nhất 3 phương pháp ghi nhớ khác nhau.
        Đưa ra ít nhất 2 câu ví dụ sử dụng từ vựng đó.
        Đưa ra ít nhất 3 từ liên quan.
        """
        
        # Gọi OpenAI API để tạo phương pháp ghi nhớ
        messages = [{"role": "system", "content": "Bạn là một trợ lý ngôn ngữ chuyên giúp người học ghi nhớ từ vựng tiếng Hàn một cách hiệu quả."},
                    {"role": "user", "content": prompt}]
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        result = response.choices[0].message.content.strip()
        
        # Phân tích kết quả JSON
        try:
            mnemonics_data = json.loads(result)
            return jsonify(mnemonics_data)
        except json.JSONDecodeError:
            # Nếu kết quả không phải JSON, thử trích xuất phần JSON
            match = re.search(r'```json(.*?)```', result, re.DOTALL)
            if match:
                try:
                    mnemonics_data = json.loads(match.group(1).strip())
                    return jsonify(mnemonics_data)
                except:
                    pass
            
            return jsonify({
                "error": "Không thể phân tích kết quả",
                "word": word,
                "meaning": meaning,
                "raw_response": result
            }), 500
            
    except Exception as e:
        print(f"Error generating mnemonics: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API endpoint để tạo mnemonics cho trang chủ
@app.route('/create_mnemonics_api', methods=['POST'])
def create_mnemonics_api():
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Vui lòng cung cấp từ vựng tiếng Hàn.'}), 400
        
        # Sử dụng model để tạo phương pháp ghi nhớ
        messages = [
            {"role": "system", "content": """Bạn là một chuyên gia về phương pháp ghi nhớ từ vựng tiếng Hàn. Nhiệm vụ của bạn là tạo các phương pháp ghi nhớ hiệu quả (mnemonics) cho từ vựng tiếng Hàn.

Hãy trả về dữ liệu dưới dạng JSON với cấu trúc sau:
```json
{
    "word": "Từ vựng gốc",
    "pronunciation": "Phiên âm",
    "meaning": "Nghĩa tiếng Việt",
    "mnemonics": [
        {"title": "Tên phương pháp 1", "description": "Mô tả cụ thể về cách ghi nhớ 1"},
        {"title": "Tên phương pháp 2", "description": "Mô tả cụ thể về cách ghi nhớ 2"},
        {"title": "Tên phương pháp 3", "description": "Mô tả cụ thể về cách ghi nhớ 3"}
    ],
    "examples": [
        {"korean": "Câu ví dụ tiếng Hàn 1", "vietnamese": "Nghĩa tiếng Việt 1"},
        {"korean": "Câu ví dụ tiếng Hàn 2", "vietnamese": "Nghĩa tiếng Việt 2"}
    ],
    "related_words": [
        {"word": "Từ liên quan 1", "meaning": "Nghĩa 1"},
        {"word": "Từ liên quan 2", "meaning": "Nghĩa 2"},
        {"word": "Từ liên quan 3", "meaning": "Nghĩa 3"}
    ]
}
```

Các loại phương pháp ghi nhớ có thể sử dụng:
1. Liên tưởng âm thanh: Liên kết âm tiếng Hàn với từ/cụm từ tiếng Việt có âm tương tự
2. Phân tích thành phần: Chia nhỏ từ tiếng Hàn thành các thành phần có nghĩa
3. Liên tưởng hình ảnh: Tạo hình ảnh liên tưởng trong tâm trí
4. Kể chuyện: Tạo câu chuyện ngắn liên quan đến từ
5. Từ đồng âm: Liên kết với từ có âm tương tự trong tiếng Việt hoặc tiếng Anh

Hãy đề xuất ít nhất 3 phương pháp ghi nhớ khác nhau, ít nhất 2 ví dụ câu, và ít nhất 3 từ liên quan."""},
            {"role": "user", "content": f"Hãy tạo phương pháp ghi nhớ cho từ vựng tiếng Hàn sau: {text}"}
        ]
        
        # Gọi API để tạo phương pháp ghi nhớ
        response = client.chat.completions.create(
            model=MODELS["text"],
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result_str = response.choices[0].message.content
        
        # Parse kết quả JSON
        mnemonics_data = json.loads(result_str)
        
        return jsonify(mnemonics_data)
        
    except json.JSONDecodeError as json_err:
        logging.error(f"Lỗi giải mã JSON từ LLM khi tạo mnemonics: {json_err}")
        error_message = "Lỗi khi xử lý phản hồi từ AI (định dạng không đúng JSON). Vui lòng thử lại."
        return jsonify({'error': error_message}), 500
    except Exception as e:
        logging.error(f"Lỗi khi tạo phương pháp ghi nhớ: {e}")
        return jsonify({'error': f"Lỗi khi xử lý yêu cầu: {str(e)}"}), 500

# Route để xử lý việc reset cuộc trò chuyện
@app.route('/reset_chat', methods=['POST'])
def reset_chat():
    try:
        # Xóa session hiện tại
        if 'conversation_history' in session:
            session.pop('conversation_history')
        
        return jsonify({'success': True, 'message': 'Đã xóa lịch sử trò chuyện thành công'})
    except Exception as e:
        logging.error(f"Lỗi khi reset chat: {e}")
        return jsonify({'error': f"Lỗi khi reset chat: {str(e)}"}), 500


# Hàm tạo câu hỏi đơn giản từ một câu
def generate_question(sentence):
    # Loại bỏ dấu chấm cuối câu
    sentence = sentence.rstrip('.!?')
    
    # Xác định một mẫu câu hỏi ngẫu nhiên
    question_templates = [
        "Giải thích ý nghĩa của câu: '{}'?",
        "Câu '{}' có nghĩa là gì?",
        "Nội dung chính của câu '{}' là gì?",
        "Điều gì được đề cập trong '{}' ?",
        "Hãy giải thích '{}' trong ngữ cảnh này?",
        "Tôi cần thông tin về '{}', bạn giải thích được không?",
    ]
    
    template = random.choice(question_templates)
    
    # Nếu câu quá dài, có thể rút gọn
    if len(sentence) > 100:
        words = sentence.split()
        shortened = ' '.join(words[:10]) + '...'
        return template.format(shortened)
    
    return template.format(sentence)

if __name__ == '__main__':
    app.run(debug=True)