document.addEventListener("DOMContentLoaded", function() {
    // メッセージをセッションストレージから読み込み、表示
    const messageContainer = document.getElementById('message-container');
    const savedMessage = sessionStorage.getItem('flashMessage');
    if (savedMessage) {
        const message = JSON.parse(savedMessage);
        messageContainer.innerHTML = '';  // 以前のメッセージをクリア
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.category}`;
        messageDiv.textContent = message.message;
        messageContainer.appendChild(messageDiv);
        sessionStorage.removeItem('flashMessage');  // メッセージを一度表示したら削除
    }

    document.getElementById("shift-form").addEventListener("submit", function(event) {
        event.preventDefault();
        
        let formData = new FormData(this);

        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())  // JSONレスポンスを期待
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
            alert('エラーが発生しました');
        });
    });
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
        fetch(`/get_shifts/${date}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log("取得したシフトデータ:", data);
            // シフト詳細の表示処理
            const shiftDetails = document.getElementById('shift-details');
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
            const shiftDetails = document.getElementById('shift-details');
            shiftDetails.innerHTML = '<p>シフトデータの取得に失敗しました。</p>';
        });
    }    