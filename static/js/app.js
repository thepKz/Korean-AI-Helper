// Hàm xử lý ghi âm và nhận dạng giọng nói
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let audioContext;
let analyser;
let microphone;

// Hàm toggle ghi âm
function toggleRecording() {
    const recordButton = document.getElementById('recordButton');
    const recordButtonText = document.getElementById('recordButtonText');
    const recordingIndicator = document.getElementById('recordingIndicator');
    const audioPlaybackContainer = document.getElementById('audio-playback-container');
    const voiceFeedback = document.getElementById('voiceFeedback');
    
    if (!isRecording) {
        // Bắt đầu ghi âm
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                // Xử lý khi có dữ liệu âm thanh
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };
                
                // Xử lý khi ghi âm hoàn tất
                mediaRecorder.onstop = async () => {
                    // Tạo blob âm thanh
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    // Hiển thị trình phát audio
                    const audioPlayback = document.getElementById('audio-playback');
                    audioPlayback.src = audioUrl;
                    audioPlaybackContainer.classList.remove('hidden');
                    
                    // Xử lý đánh giá phát âm
                    processPronunciationFeedback(audioBlob);
                };
                
                // Bắt đầu ghi âm
                mediaRecorder.start();
                isRecording = true;
                
                // Cập nhật UI
                recordButtonText.textContent = 'Dừng ghi âm';
                recordButton.classList.add('recording');
                recordingIndicator.classList.remove('hidden');
                voiceFeedback.classList.add('hidden');
                
                // Thiết lập phân tích âm thanh để hiển thị sóng âm
                setupAudioAnalysis(stream);
            })
            .catch(error => {
                console.error('Không thể truy cập microphone:', error);
                alert('Vui lòng cho phép truy cập microphone để sử dụng tính năng này!');
            });
    } else {
        // Dừng ghi âm
        if (mediaRecorder) {
            mediaRecorder.stop();
            
            // Dừng stream microphone
            if (microphone) {
                microphone.getAudioTracks().forEach(track => track.stop());
            }
            
            // Đóng AudioContext nếu đã tạo
            if (audioContext && audioContext.state !== 'closed') {
                audioContext.close();
            }
        }
        
        isRecording = false;
        
        // Cập nhật UI
        recordButtonText.textContent = 'Bắt đầu ghi âm';
        recordButton.classList.remove('recording');
        recordingIndicator.classList.add('hidden');
    }
}

// Thiết lập phân tích âm thanh
function setupAudioAnalysis(stream) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    microphone = audioContext.createMediaStreamSource(stream);
    
    microphone.connect(analyser);
    // Không kết nối với đầu ra để tránh feedback
    // analyser.connect(audioContext.destination);
    
    // Thiết lập các tham số cho analyser
    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    // Cập nhật hiệu ứng sóng
    function updateWaveform() {
        if (!isRecording) return;
        
        requestAnimationFrame(updateWaveform);
        analyser.getByteFrequencyData(dataArray);
        
        // Cập nhật hiệu ứng sóng trong UI
        const waveSpans = document.querySelectorAll('.wave-animation span');
        const waveCount = waveSpans.length;
        
        for (let i = 0; i < waveCount; i++) {
            const waveIndex = Math.floor((i / waveCount) * bufferLength);
            const value = dataArray[waveIndex] / 255;  // Chuyển về tỷ lệ 0-1
            
            const height = Math.max(1, value * 30);  // Giới hạn chiều cao tối thiểu là 1px
            waveSpans[i].style.height = `${height}px`;
        }
    }
    
    // Bắt đầu cập nhật hiệu ứng sóng
    updateWaveform();
}

// Xử lý đánh giá phát âm
async function processPronunciationFeedback(audioBlob) {
    // Hiển thị trạng thái đang xử lý
    const voiceFeedback = document.getElementById('voiceFeedback');
    voiceFeedback.classList.remove('hidden');
    voiceFeedback.innerHTML = `
        <div class="flex items-center justify-center p-4">
            <div class="loader"></div>
            <span class="ml-2">Đang phân tích phát âm...</span>
        </div>
    `;
    
    try {
        // Lấy cài đặt và dữ liệu phát âm
        const practiceType = document.getElementById('practice-type').value;
        const currentWord = document.querySelector('.word-container.current')?.dataset.word || '';
        const allText = document.querySelector('.pronunciation-guide .font-medium')?.textContent || '';
        
        // Tạo FormData để gửi file âm thanh
        const formData = new FormData();
        formData.append('audio', audioBlob);
        formData.append('text', practiceType === 'full' ? allText : currentWord);
        formData.append('type', practiceType);
        
        // Lấy API key từ biến môi trường
        const apiKey = document.getElementById('xai-api-key').value;
        
        // Gọi API phân tích phát âm
        const response = await fetch('https://api.xai-services.com/v1/speech/korean-evaluation', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${apiKey}`
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Lỗi API: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Hiển thị kết quả đánh giá
        displayPronunciationFeedback(data);
    } catch (error) {
        console.error('Lỗi khi xử lý đánh giá phát âm:', error);
        
        // Hiển thị thông báo lỗi
        voiceFeedback.innerHTML = `
            <div class="p-3 bg-red-50 rounded-md text-red-700">
                <i class="fas fa-exclamation-circle mr-1"></i>
                Không thể phân tích phát âm. Vui lòng thử lại.
                <div class="text-xs mt-1">${error.message}</div>
            </div>
        `;
    }
}

// Hiển thị kết quả đánh giá phát âm
function displayPronunciationFeedback(data) {
    const voiceFeedback = document.getElementById('voiceFeedback');
    const score = Math.round(data.score * 100);
    
    // Xác định màu sắc dựa trên điểm số
    let scoreColor = 'text-red-600';
    if (score >= 80) {
        scoreColor = 'text-green-600';
    } else if (score >= 60) {
        scoreColor = 'text-yellow-600';
    } else if (score >= 40) {
        scoreColor = 'text-orange-600';
    }
    
    // HTML cho phần phản hồi
    let feedbackHTML = `
        <div class="text-sm font-medium text-blue-700 mb-1">
            <i class="fas fa-chart-bar mr-1"></i> Kết quả đánh giá:
        </div>
        
        <div class="voice-feedback-score">
            <div class="score-number ${scoreColor}">${score}</div>
            <div class="score-bar w-full bg-gray-200 rounded-full h-2.5">
                <div class="bg-blue-600 h-2.5 rounded-full" style="width: ${score}%"></div>
            </div>
        </div>
    `;
    
    // Nếu có phản hồi chi tiết, hiển thị chúng
    if (data.details && data.details.length > 0) {
        feedbackHTML += `
            <div class="voice-feedback-details mt-2">
                <div class="text-sm font-medium mb-1">Chi tiết phát âm:</div>
                <div class="grid grid-cols-1 gap-2" id="syllableFeedback">
        `;
        
        data.details.forEach(detail => {
            const detailScore = Math.round(detail.score * 100);
            let detailScoreColor = 'text-red-600';
            
            if (detailScore >= 80) {
                detailScoreColor = 'text-green-600';
            } else if (detailScore >= 60) {
                detailScoreColor = 'text-yellow-600';
            } else if (detailScore >= 40) {
                detailScoreColor = 'text-orange-600';
            }
            
            feedbackHTML += `
                <div class="bg-gray-50 p-2 rounded-md flex items-center justify-between">
                    <span class="font-medium">${detail.text}</span>
                    <span class="${detailScoreColor}">${detailScore}/100</span>
                </div>
            `;
        });
        
        feedbackHTML += `
                </div>
            </div>
        `;
    }
    
    // Thêm lời khuyên cải thiện
    feedbackHTML += `
        <div class="mt-3 p-2 bg-blue-50 rounded-md">
            <div class="text-sm font-medium text-blue-700 mb-1">Lời khuyên:</div>
            <ul class="list-disc list-inside text-sm text-gray-700">
    `;
    
    // Thêm lời khuyên dựa trên điểm số
    if (score < 60) {
        feedbackHTML += `
            <li>Hãy luyện tập nhiều hơn và chú ý đến ngữ điệu.</li>
            <li>Cố gắng phát âm chậm và rõ ràng.</li>
            <li>Tập trung vào các từ có điểm số thấp.</li>
        `;
    } else if (score < 80) {
        feedbackHTML += `
            <li>Phát âm khá tốt! Hãy tiếp tục luyện tập.</li>
            <li>Chú ý đến các phụ âm cuối và ngữ điệu.</li>
        `;
    } else {
        feedbackHTML += `
            <li>Phát âm rất tốt! Tiếp tục giữ vững phong độ.</li>
            <li>Bạn có thể thử phát âm nhanh hơn để tăng độ tự nhiên.</li>
        `;
    }
    
    // Thêm lời khuyên tùy chỉnh từ API nếu có
    if (data.feedback) {
        feedbackHTML += `<li>${data.feedback}</li>`;
    }
    
    feedbackHTML += `
            </ul>
        </div>
    `;
    
    // Cập nhật nội dung phản hồi
    voiceFeedback.innerHTML = feedbackHTML;
}

// Khởi tạo trang khi document đã sẵn sàng
document.addEventListener('DOMContentLoaded', function() {
    // Thiết lập các nút phát âm
    setupPronunciationButtons();
    
    // Thiết lập form ghi âm nếu có
    setupRecordForm();
    
    // Xử lý sự kiện khi thay đổi tốc độ phát âm
    const speedControl = document.getElementById('pronunciation-speed');
    const speedValue = document.getElementById('speed-value');
    
    if (speedControl && speedValue) {
        speedControl.addEventListener('input', function() {
            speedValue.textContent = `${speedControl.value}x`;
        });
    }
    
    // Xử lý sự kiện khi thay đổi chế độ luyện đọc từng từ
    const wordByWordMode = document.getElementById('word-by-word-mode');
    const pronunciationWordByWord = document.querySelector('.pronunciation-word-by-word');
    
    if (wordByWordMode && pronunciationWordByWord) {
        wordByWordMode.addEventListener('change', function() {
            if (wordByWordMode.checked) {
                pronunciationWordByWord.style.display = 'flex';
            } else {
                pronunciationWordByWord.style.display = 'none';
            }
        });
    }
    
    // Khởi tạo các tính năng khác trên trang
    initOtherFeatures();
});

// Thiết lập form ghi âm nếu có
function setupRecordForm() {
    const recordButton = document.getElementById('record-button');
    if (recordButton) {
        recordButton.addEventListener('click', toggleRecording);
    }
}

// Khởi tạo các tính năng khác trên trang
function initOtherFeatures() {
    // Thêm API key vào trang (nếu cần)
    const apiKeyInput = document.createElement('input');
    apiKeyInput.type = 'hidden';
    apiKeyInput.id = 'xai-api-key';
    apiKeyInput.value = 'xai-V9YVzmyoVwBjtdIIFOvKDgNiIuungvSkdUDro8AGZj3Xx0gQbF1g9NAfuMGROAD1VAWxuRgjXbucuVZL';
    document.body.appendChild(apiKeyInput);
    
    // Các tính năng khác có thể được thêm ở đây
}

// Hàm thiết lập các nút phát âm trên trang
function setupPronunciationButtons() {
    try {
        // Chọn tất cả các nút phát âm
        const buttons = document.querySelectorAll('.pronunciation-button');
        
        // Xóa các sự kiện cũ để tránh trùng lặp
        buttons.forEach(btn => {
            if (btn) {
                // Tạo bản sao của button để xóa tất cả event listeners
                const newBtn = btn.cloneNode(true);
                if (btn.parentNode) {
                    btn.parentNode.replaceChild(newBtn, btn);
                }
            }
        });
        
        // Chọn lại các nút sau khi thay thế
        const newButtons = document.querySelectorAll('.pronunciation-button');
        
        // Thêm sự kiện click cho mỗi nút
        newButtons.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    // Lấy văn bản cần đọc từ thuộc tính data-text
                    const textToSpeak = this.getAttribute('data-text');
                    if (textToSpeak) {
                        speakKorean(textToSpeak);
                    }
                });
            }
        });
        
        console.log(`Đã thiết lập ${newButtons.length} nút phát âm trên trang.`);
    } catch (error) {
        console.error('Lỗi khi thiết lập nút phát âm:', error);
    }
}

// Hàm phát âm tiếng Hàn với tốc độ có thể điều chỉnh
function speakKorean(text, options = {}) {
    if (!text || typeof text !== 'string' || text.trim() === '') {
        console.warn("speakKorean: Văn bản trống hoặc không hợp lệ");
        return;
    }
    
    // Lấy tốc độ phát âm từ cài đặt
    let speed = 1.0; // Tốc độ mặc định
    
    try {
        // Thử lấy cài đặt từ localStorage
        const settings = JSON.parse(localStorage.getItem('hangulMateSettings') || '{}');
        if (settings && settings.pronunciationSpeed) {
            speed = parseFloat(settings.pronunciationSpeed);
        } else if (window.hangulMateSpeedSetting) {
            // Fallback vào biến toàn cục nếu có
            speed = window.hangulMateSpeedSetting;
        }
    } catch (e) {
        console.warn("Không thể đọc cài đặt tốc độ phát âm:", e);
    }
    
    // Đảm bảo tốc độ hợp lệ
    if (isNaN(speed) || speed < 0.5 || speed > 2.0) {
        speed = 1.0;
    }
    
    // Bắt đầu phát âm
    try {
        // Thử dùng API của server (nếu có)
        useServerTTS(text, speed)
            .catch(e => {
                console.warn("Không thể sử dụng TTS server, dùng Web Speech API:", e);
                useBrowserTTS(text, speed);
            });
    } catch (error) {
        console.error("Lỗi khi phát âm:", error);
        // Phương án dự phòng là Web Speech API
        useBrowserTTS(text, speed);
    }
}

// Hàm phát âm sử dụng Web Speech API
function useBrowserTTS(text, speed) {
    try {
        // Dừng tất cả phát âm đang chạy
        window.speechSynthesis.cancel();
        
        // Tạo utterance mới
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'ko-KR';
        utterance.rate = speed;
        
        // Tìm giọng tiếng Hàn nếu có
        const voices = window.speechSynthesis.getVoices();
        const koreanVoice = voices.find(voice => voice.lang.includes('ko'));
        if (koreanVoice) {
            utterance.voice = koreanVoice;
        }
        
        // Bắt đầu phát âm
        window.speechSynthesis.speak(utterance);
    } catch (error) {
        console.error("Lỗi khi sử dụng Web Speech API:", error);
    }
}

// Hàm xử lý hiện/ẩn bảng cài đặt phát âm
function togglePronunciationSettings() {
    const settingsPanel = document.getElementById('pronunciation-settings-panel');
    if (settingsPanel) {
        if (settingsPanel.style.display === 'block') {
            settingsPanel.style.display = 'none';
        } else {
            settingsPanel.style.display = 'block';
        }
    }
}

// Hàm xử lý hiện/ẩn nội dung mở rộng kiến thức
function toggleExpandKnowledge() {
    const content = document.getElementById('expand-knowledge-content');
    const button = document.getElementById('expand-knowledge-btn');
    
    if (content.style.display === 'block') {
        content.style.display = 'none';
        button.innerHTML = '<i class="fas fa-lightbulb mr-1"></i> Mở rộng kiến thức';
    } else {
        content.style.display = 'block';
        button.innerHTML = '<i class="fas fa-times mr-1"></i> Thu gọn';
        
        // Tải nội dung mở rộng nếu chưa có
        if (content.querySelector('p').textContent === 'Đang tải nội dung mở rộng...') {
            // Mô phỏng tải nội dung
            setTimeout(() => {
                const currentWord = document.querySelector('.pronunciation-guide .font-medium')?.textContent || '';
                
                content.innerHTML = `
                    <div class="text-sm font-medium text-blue-800 mb-2">Các dạng tương đương:</div>
                    <div class="p-2 border-l-2 border-blue-200">
                        <p>Đây là một số thông tin bổ sung về cách phát âm và cách sử dụng từ hoặc mẫu câu này trong các tình huống khác nhau.</p>
                        <ul class="list-disc list-inside mt-2 space-y-1">
                            <li>Ngữ cảnh trang trọng: <span class="font-medium text-slate-800">${currentWord}</span></li>
                            <li>Ngữ cảnh thân mật: <span class="font-medium text-slate-800">${currentWord}</span></li>
                            <li>Biến thể khu vực: <span class="font-medium text-slate-800">${currentWord}</span></li>
                        </ul>
                    </div>
                `;
            }, 1000);
        }
    }
}

// Mnemonics page functionality
document.addEventListener('DOMContentLoaded', function() {
  const mnemonicsForm = document.getElementById('mnemonics-form');
  
  if (mnemonicsForm) {
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultsContainer = document.getElementById('results-container');
    const wordDisplay = document.getElementById('word-display');
    const mnemonicsList = document.getElementById('mnemonics-list');
    const examplesList = document.getElementById('examples-list');
    const relatedWords = document.getElementById('related-words');
    
    mnemonicsForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const vocabularyInput = document.getElementById('vocabulary-input').value.trim();
      
      if (!vocabularyInput) {
        return;
      }
      
      // Show loading indicator
      loadingIndicator.classList.remove('hidden');
      resultsContainer.classList.add('hidden');
      
      try {
        const response = await fetch('/create-mnemonics', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ word: vocabularyInput }),
        });
        
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        
        const data = await response.json();
        
        // Display the results
        wordDisplay.textContent = data.word;
        
        // Populate mnemonics
        mnemonicsList.innerHTML = '';
        data.mnemonics.forEach(mnemonic => {
          const li = document.createElement('li');
          li.className = 'mb-3 p-3 bg-purple-50 rounded-lg';
          li.innerHTML = `<span class="font-medium">${mnemonic.method}:</span> ${mnemonic.description}`;
          mnemonicsList.appendChild(li);
        });
        
        // Populate examples
        examplesList.innerHTML = '';
        data.examples.forEach(example => {
          const li = document.createElement('li');
          li.className = 'mb-2';
          li.innerHTML = `<p class="mb-1">${example.sentence}</p>
                          <p class="text-sm text-gray-600">${example.translation}</p>`;
          examplesList.appendChild(li);
        });
        
        // Populate related words
        relatedWords.innerHTML = '';
        data.related_words.forEach(word => {
          const div = document.createElement('div');
          div.className = 'mr-2 mb-2 inline-block px-3 py-1 bg-blue-100 rounded-full text-blue-800';
          div.textContent = word;
          relatedWords.appendChild(div);
        });
        
        // Show results
        resultsContainer.classList.remove('hidden');
      } catch (error) {
        console.error('Error:', error);
        alert('Đã xảy ra lỗi khi tạo phương pháp ghi nhớ. Vui lòng thử lại sau.');
      } finally {
        // Hide loading indicator
        loadingIndicator.classList.add('hidden');
      }
    });
  }
}); 