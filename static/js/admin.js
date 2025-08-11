document.addEventListener("DOMContentLoaded", function () {
    const logContainer = document.getElementById("log-container");
    const timerDisplay = document.getElementById("timer-display"); // 倒计时显示区域

    // 连接 SSE
    const evtSource = new EventSource("/api/admin-stream?all=1");

    evtSource.addEventListener("log", function (event) {
        const data = JSON.parse(event.data);
        const message = data.message;
        appendLog(message);
    });

    evtSource.addEventListener("input_request", function (event) {
        const data = JSON.parse(event.data);
        appendLog(`📥 [${data.phone}] ${data.prompt || "需要输入"}`);
    });

    evtSource.addEventListener("timer", function (event) {
        const data = JSON.parse(event.data);
        if (timerDisplay) {
            const remain = data.remain;
            const min = Math.floor(remain / 60);
            const sec = remain % 60;
            timerDisplay.textContent = `距离下次运行还有 ${min}分${sec}秒`;
        }
    });

    evtSource.onerror = function () {
        appendLog("❌ SSE 连接已断开");
    };

    function appendLog(message) {
        const time = new Date().toLocaleTimeString();
        const div = document.createElement("div");
        div.textContent = `[${time}] ${message}`;
        logContainer.appendChild(div);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
});
