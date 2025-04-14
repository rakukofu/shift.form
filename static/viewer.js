document.addEventListener("DOMContentLoaded", () => {
    const calendarContainer = document.getElementById("calendar-container");
    const calendarTitle = document.getElementById("calendar-title");
    const prevMonthButton = document.getElementById("prev-month");
    const nextMonthButton = document.getElementById("next-month");
    const detailsContent = document.getElementById("details-content");
    const userSearch = document.getElementById("user-search");

    // 必要な要素が存在しない場合は処理を中断
    if (!calendarContainer || !calendarTitle || !prevMonthButton || !nextMonthButton || !detailsContent || !userSearch) {
        console.log("カレンダー関連の要素が見つかりません。このページではカレンダー機能は使用できません。");
        return;
    }

    let currentYear = 2025;
    let currentMonth = 1;
    const shiftCache = {}; // シフトデータキャッシュ
    let currentRequestController; // 現在のリクエストコントローラー
    let allShifts = {}; // 全シフトデータを保持
    let lastClickedDate = null;
    let allUsers = new Set(); // 全ユーザーを保持するセット

    const holidays = [
        { month: 1, day: 1 }, { month: 2, day: 11 }, { month: 4, day: 29 },
        { month: 5, day: 3 }, { month: 5, day: 4 }, { month: 5, day: 5 },
        { month: 7, day: 20 }, { month: 9, day: 15 }, { month: 10, day: 14 },
        { month: 11, day: 3 }, { month: 11, day: 23 }, { month: 12, day: 23 }
    ];

    function changeMonth(direction) {
        currentMonth += direction;
        if (currentMonth < 1) {
            currentMonth = 12;
            currentYear--;
        } else if (currentMonth > 12) {
            currentMonth = 1;
            currentYear++;
        }
        displayCalendar(currentYear, currentMonth);
    }

    function generateCalendar(year, month) {
        const daysInMonth = new Date(year, month, 0).getDate();
        const firstDay = new Date(year, month - 1, 1).getDay();

        let html = `<table>
            <thead>
                <tr>
                    <th>日</th><th>月</th><th>火</th><th>水</th><th>木</th><th>金</th><th>土</th>
                </tr>
            </thead>
            <tbody>`;
        let dayCounter = 1;

        for (let i = 0; i < 6; i++) {
            html += "<tr>";
            for (let j = 0; j < 7; j++) {
                let dayClass = j === 0 || j === 6 ? "rest" : "weekday";
                const isHoliday = holidays.some(holiday => holiday.month === month && holiday.day === dayCounter);

                if (isHoliday) dayClass = "holiday";

                if (i === 0 && j < firstDay) {
                    html += "<td></td>";
                } else if (dayCounter <= daysInMonth) {
                    html += `<td class="${dayClass}" data-date="${year}-${month}-${dayCounter}">
                                ${dayCounter}
                             </td>`;
                    dayCounter++;
                } else {
                    html += "<td></td>";
                }
            }
            html += "</tr>";
            if (dayCounter > daysInMonth) break;
        }

        html += "</tbody></table>";
        return html;
    }

    function attachDateClickListeners() {
        const dateCells = calendarContainer.querySelectorAll("[data-date]");
        dateCells.forEach(cell => {
            cell.addEventListener("click", () => {
                const date = cell.getAttribute("data-date");
                if (date && date !== lastClickedDate) {
                    lastClickedDate = date;
                    
                    if (currentRequestController) {
                        currentRequestController.abort();
                    }

                    currentRequestController = new AbortController();
                    const signal = currentRequestController.signal;

                    fetch(`/get_shifts/${date}`, { method: "GET", signal })
                        .then(response => response.json())
                        .then(data => {
                            currentRequestController = null;
                            shiftCache[date] = data;
                            updateDetails(data);
                        })
                        .catch(error => {
                            if (error.name === "AbortError") {
                                console.log("リクエストがキャンセルされました:", date);
                            } else {
                                console.error("エラー:", error);
                                detailsContent.innerHTML = `<p>データ取得中にエラーが発生しました。</p>`;
                            }
                        });
                }
            });
        });
    }

    function displayCalendar(year, month) {
        if (!calendarContainer || !calendarTitle) {
            console.log("カレンダーコンテナまたはタイトル要素が見つかりません。");
            return;
        }
        calendarContainer.innerHTML = generateCalendar(year, month);
        calendarTitle.textContent = `${year}年 ${month}月`;
        attachDateClickListeners();
    }

    // ユーザーリストを取得して選択肢に追加
    function updateUserList() {
        allUsers.clear();
        Object.values(allShifts).flat().forEach(shift => {
            allUsers.add(shift.user_name);
        });
        
        // 選択肢を更新
        const userSearch = document.getElementById("user-search");
        const currentValue = userSearch.value;
        userSearch.innerHTML = '<option value="">全ユーザーを表示</option>';
        
        Array.from(allUsers).sort().forEach(user => {
            const option = document.createElement("option");
            option.value = user;
            option.textContent = user;
            userSearch.appendChild(option);
        });
        
        // 以前の選択値を復元
        userSearch.value = currentValue;
    }

    // 検索機能の実装
    userSearch.addEventListener("change", (e) => {
        const selectedUser = e.target.value;
        if (selectedUser === "") {
            if (lastClickedDate) {
                updateDetails(shiftCache[lastClickedDate]);
            }
            return;
        }

        const filteredShifts = Object.values(allShifts).flat().filter(shift => 
            shift.user_name === selectedUser
        );

        if (filteredShifts.length > 0) {
            detailsContent.innerHTML = filteredShifts.map(shift => {
                let morningStatus = getShiftStatusHTML('午前', shift.morning);
                let afternoonStatus = getShiftStatusHTML('午後', shift.afternoon);
                
                return `
                    <div class="shift-item">
                        <p class="user-name">${shift.user_name}</p>
                        <p><strong>日付:</strong> ${shift.date}</p>
                        <div class="shift-times">
                            ${morningStatus}
                            ${afternoonStatus}
                        </div>
                    </div>
                `;
            }).join("");
        } else {
            detailsContent.innerHTML = `
                <div class="shift-item">
                    <p>${selectedUser}のシフトはまだ登録されていません。</p>
                </div>
            `;
        }
    });

    function updateDetails(data) {
        console.log("データ更新:", data);
        const detailsContainer = document.getElementById('details-container');
        const selectedUser = document.getElementById('user-search').value;
        
        if (!data || !data.date) {
            detailsContainer.innerHTML = '<p>日付を選択してください。</p>';
            return;
        }

        const shifts = data.shifts || [];
        let content = '';

        if (selectedUser) {
            // 特定のユーザーのシフトを表示
            const userShifts = shifts.filter(shift => shift.user_name === selectedUser);
            if (userShifts.length > 0) {
                content = `
                    <h2>${selectedUser}のシフト詳細</h2>
                    <div class="shift-details">
                        <div class="shift-header">
                            <div class="shift-time">午前</div>
                            <div class="shift-time">午後</div>
                        </div>
                        <div class="shift-row">
                            <div class="shift-status ${userShifts[0].morning === '出勤可能' ? 'available' : 'unavailable'}">
                                ${userShifts[0].morning}
                            </div>
                            <div class="shift-status ${userShifts[0].afternoon === '出勤可能' ? 'available' : 'unavailable'}">
                                ${userShifts[0].afternoon}
                            </div>
                        </div>
                    </div>
                `;
            } else {
                content = `<p>${selectedUser}のシフトは登録されていません。</p>`;
            }
        } else {
            // 全ユーザーのシフトを表示
            if (shifts.length > 0) {
                content = `
                    <h2>${data.date}のシフト詳細</h2>
                    <div class="shift-details">
                        <div class="shift-header">
                            <div class="shift-name">名前</div>
                            <div class="shift-time">午前</div>
                            <div class="shift-time">午後</div>
                        </div>
                        ${shifts.map(shift => `
                            <div class="shift-row">
                                <div class="shift-name">${shift.user_name}</div>
                                <div class="shift-status ${shift.morning === '出勤可能' ? 'available' : 'unavailable'}">
                                    ${shift.morning}
                                </div>
                                <div class="shift-status ${shift.afternoon === '出勤可能' ? 'available' : 'unavailable'}">
                                    ${shift.afternoon}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            } else {
                content = `<p>${data.date}のシフトは登録されていません。</p>`;
            }
        }

        detailsContainer.innerHTML = content;
    }

    function getShiftStatusHTML(time, status) {
        if (!status) return '';
        
        const statusClass = status === '〇' ? 'available' : 'unavailable';
        const statusText = status === '〇' ? '出勤可能' : '出勤不可';
        
        return `
            <p>
                <span class="shift-time">${time}</span>
                <span class="shift-status ${statusClass}">${statusText}</span>
            </p>
        `;
    }

    // スクロール時のジャーキーな動きを防ぐためのイベント最適化
    let scrollTimeout;
    window.addEventListener("scroll", () => {
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }
        scrollTimeout = setTimeout(() => {
            console.log("スクロール中...");
        }, 100); // デバウンスを適用
    });

    // ボタンのイベントリスナーを設定
    if (prevMonthButton && nextMonthButton) {
        prevMonthButton.addEventListener("click", () => changeMonth(-1));
        nextMonthButton.addEventListener("click", () => changeMonth(1));
    }

    // カレンダーを表示
    displayCalendar(currentYear, currentMonth);
});
