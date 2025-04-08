document.addEventListener("DOMContentLoaded", function() {
    // メッセージをセッションストレージから読み込み、表示
    const messageContainer = document.getElementById('message-container');
    const shiftForm = document.getElementById('shift-form');

    // メッセージコンテナが存在する場合のみ処理
    if (messageContainer) {
        const savedMessage = sessionStorage.getItem('flashMessage');
        if (savedMessage) {
            try {
                const message = JSON.parse(savedMessage);
                messageContainer.innerHTML = '';  // 以前のメッセージをクリア
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${message.category}`;
                messageDiv.textContent = message.message;
                messageContainer.appendChild(messageDiv);
                sessionStorage.removeItem('flashMessage');  // メッセージを一度表示したら削除
            } catch (error) {
                console.error('メッセージの解析に失敗しました:', error);
            }
        }
    }

    // シフトフォームが存在する場合のみ処理
    if (shiftForm) {
        shiftForm.addEventListener("submit", function(event) {
            event.preventDefault();
            
            let formData = new FormData(this);
            // CSRFトークンを追加
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            formData.append('csrf_token', csrfToken);

            fetch('/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(`HTTP error! status: ${response.status}, body: ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                // セッションストレージにメッセージを保存
                sessionStorage.setItem('flashMessage', JSON.stringify(data));
                // メッセージを表示
                messageContainer.innerHTML = '';  // 以前のメッセージをクリア
                const message = document.createElement('div');
                message.className = `message ${data.category}`;
                message.textContent = data.message;
                messageContainer.appendChild(message);
            })
            .catch(error => {
                console.error('エラー:', error);
                messageContainer.innerHTML = '';  // 以前のメッセージをクリア
                const errorMessage = document.createElement('div');
                errorMessage.className = 'message error';
                errorMessage.textContent = 'シフトの送信に失敗しました。もう一度お試しください。';
                messageContainer.appendChild(errorMessage);
            });
        });
    }
});

function updateCalendarWithShifts(shiftData) {
    document.querySelectorAll("td[data-date]").forEach(td => {
        let date = td.getAttribute("data-date");
        td.innerHTML += `<div class="shift-info"></div>`; // シフト情報用の div を追加
        let shiftInfoDiv = td.querySelector(".shift-info");

        if (shiftData[date]) {
            shiftData[date].forEach(shift => {
                let shiftText = `<p>${shift.name}: 午前(${shift.shift.morning}) / 午後(${shift.shift.afternoon})</p>`;
                shiftInfoDiv.innerHTML += shiftText;
            });
        }
    });
}

function displayShiftDetails(date) {
    const shiftDetails = document.getElementById('shift-details');
    shiftDetails.innerHTML = '<p>シフト情報を取得中...</p>';

    fetch(`/get_shifts/${date}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new TypeError("サーバーからのレスポンスがJSONではありません");
        }
        return response.json();
    })
    .then(data => {
        console.log("取得したシフトデータ:", data);
        if (data && data.length > 0) {
            let html = '<h3>シフト詳細</h3><ul>';
            data.forEach(shift => {
                html += `<li>${shift.user_name}: 午前(${shift.morning || '未回答'}) / 午後(${shift.afternoon || '未回答'})</li>`;
            });
            html += '</ul>';
            shiftDetails.innerHTML = html;
        } else {
            shiftDetails.innerHTML = '<p>この日のシフトはまだ登録されていません。</p>';
        }
    })
    .catch(error => {
        console.error('エラー:', error);
        shiftDetails.innerHTML = '<p>シフトデータの取得に失敗しました。もう一度お試しください。</p>';
    });
}    