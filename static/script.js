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
        .then(response => response.text())
        .then(text => {
            try {
                if (text.startsWith("{") || text.startsWith("{")) {
                    return JSON.parse(text);  
                } else {  
                    throw new Error("予期しないHTMLレスポンスが返されました");  
                }  
            } catch (error) {  
                throw new Error("JSON のパースに失敗: " + error.message);  
            }  
        })  
        .then(data => {  
            console.log("パース後のデータ:", data);  
            // シフト詳細の表示処理を追加  
        })  
        .catch(error => console.error('エラー:', error));  
    }    