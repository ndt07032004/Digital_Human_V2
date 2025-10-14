// static/js/chat.js (fixed ASR)

document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const recordBtn = document.getElementById('record-btn');

    let socket;
    let mediaRecorder;
    let audioChunks = [];

    function connectWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(`${wsProtocol}//${window.location.host}/fay/ws/chat`);

        socket.onopen = () => appendMessage("✅ Đã kết nối máy chủ!", 'system-message');
        socket.onclose = () => {
            appendMessage("⚠️ Mất kết nối, thử lại sau 3s...", 'system-message error');
            setTimeout(connectWebSocket, 3000);
        };
        socket.onerror = err => {
            console.error("WebSocket error:", err);
            appendMessage("❌ Lỗi kết nối WebSocket.", 'system-message error');
        };
        socket.onmessage = event => {
            if (event.data instanceof Blob) {
                const audioUrl = URL.createObjectURL(event.data);
                const audio = new Audio(audioUrl);
                audio.play().catch(e => console.error("Lỗi phát audio:", e));
            } else {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'user_text') appendMessage(data.content, 'user-message');
                    else if (data.type === 'ai_text') appendMessage(data.content, 'ai-message');
                } catch (e) {
                    console.error("JSON parse error:", e);
                }
            }
        };
    }

    function appendMessage(text, className) {
        if (!text) return;
        const div = document.createElement('div');
        div.textContent = text;
        div.className = 'message ' + className;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function sendTextMessage() {
        const msg = userInput.value.trim();
        if (msg && socket && socket.readyState === WebSocket.OPEN) {
            appendMessage(msg, 'user-message');
            socket.send(JSON.stringify({ text: msg }));
            userInput.value = '';
        }
    }

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : 'audio/webm';

            mediaRecorder = new MediaRecorder(stream, { mimeType });
            audioChunks = [];

            mediaRecorder.ondataavailable = e => {
                if (e.data.size > 0) audioChunks.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                if (audioChunks.length === 0) {
                    console.warn("Không có dữ liệu âm thanh!");
                    return;
                }

                // Ghép các phần audio lại thành 1 blob
                const webmBlob = new Blob(audioChunks, { type: mimeType });
                const arrayBuffer = await webmBlob.arrayBuffer();

                // ✅ Chuyển WebM sang WAV trước khi gửi
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
                const wavBuffer = audioBufferToWav(audioBuffer);
                const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });

                if (socket && socket.readyState === WebSocket.OPEN) {
                    // 🚀 Sửa ở đây: gửi mảng byte, không gửi Blob
                    const bytes = await wavBlob.arrayBuffer();
                    socket.send(bytes);
                    console.log("✅ Đã gửi âm thanh:", wavBlob.size, "bytes");
                } else {
                    console.warn("⚠️ WebSocket chưa sẵn sàng, không gửi được audio.");
                }

                stream.getTracks().forEach(t => t.stop());
            };

            mediaRecorder.start();
            recordBtn.textContent = "⏺ Đang ghi...";
            recordBtn.classList.add("recording");

        } catch (err) {
            console.error("Không thể khởi động ghi âm:", err);
            appendMessage("❌ Không thể truy cập micro. Hãy kiểm tra quyền.", "system-message error");
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            recordBtn.textContent = "🎤 Ghi âm";
            recordBtn.classList.remove("recording");
        }
    }

    // Hàm chuyển AudioBuffer sang WAV
    function audioBufferToWav(buffer) {
        const numOfChan = buffer.numberOfChannels;
        const length = buffer.length * numOfChan * 2 + 44;
        const result = new ArrayBuffer(length);
        const view = new DataView(result);
        let offset = 0;

        function writeString(s) { for (let i = 0; i < s.length; i++) view.setUint8(offset + i, s.charCodeAt(i)); offset += s.length; }
        function write16(v) { view.setInt16(offset, v, true); offset += 2; }
        function write32(v) { view.setInt32(offset, v, true); offset += 4; }

        writeString("RIFF"); write32(length - 8); writeString("WAVE");
        writeString("fmt "); write32(16); write16(1);
        write16(numOfChan); write32(buffer.sampleRate);
        write32(buffer.sampleRate * numOfChan * 2);
        write16(numOfChan * 2); write16(16);
        writeString("data"); write32(buffer.length * numOfChan * 2);

        const interleaved = new Float32Array(buffer.length * numOfChan);
        for (let i = 0; i < buffer.length; i++) {
            for (let c = 0; c < numOfChan; c++) {
                interleaved[i * numOfChan + c] = buffer.getChannelData(c)[i];
            }
        }

        let index = 0;
        while (offset < length) {
            const s = Math.max(-1, Math.min(1, interleaved[index++]));
            view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
            offset += 2;
        }
        return result;
    }

    sendBtn.onclick = sendTextMessage;
    userInput.onkeydown = e => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendTextMessage();
        }
    };

    recordBtn.onmousedown = startRecording;
    recordBtn.onmouseup = stopRecording;
    recordBtn.onmouseleave = stopRecording;
    recordBtn.ontouchstart = e => { e.preventDefault(); startRecording(); };
    recordBtn.ontouchend = e => { e.preventDefault(); stopRecording(); };

    connectWebSocket();
});
