document.addEventListener("DOMContentLoaded", function () {
    const phoneInput = document.getElementById("phone");
    const passwordInput = document.getElementById("password");
    const checkBtn = document.getElementById("run-check");  // 改为与index.html中的按钮一致
    const logArea = document.getElementById("logBox");

    let currentPhone = null;

    // 绑定检查按钮
    checkBtn.addEventListener("click", function () {
        const phone = phoneInput.value.trim();
        if (!phone) {
            alert("请输入手机号");
            return;
        }

        currentPhone = phone;

        fetch("/api/user-check", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone: phone })
        })
        .then(res => res.json())
        .then(data => {
            if (data.exists) {
                appendLog(`[${phone}] 账号已存在，开始运行任务`);
                runTask(phone);
            } else {
                const pwd = prompt("请输入密码进行注册：");
                if (!pwd) {
                    alert("注册取消");
                    return;
                }
                registerAccount(phone, pwd);
            }
        })
        .catch(err => {
            console.error(err);
            alert("检查账号失败");
        });
    });

    function registerAccount(phone, pwd) {
        fetch("/api/user-add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone: phone, password: pwd })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                appendLog(`[${phone}] 注册成功，开始运行任务`);
                runTask(phone);
            } else {
                alert("注册失败：" + data.error);
            }
        })
        .catch(err => {
            console.error(err);
            alert("注册失败");
        });
    }

    function runTask(phone) {
        // 开启日志流
        startLogStream(phone);

        fetch("/api/user-run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone: phone })
        })
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                alert("任务启动失败");
            }
        })
        .catch(err => {
            console.error(err);
            alert("启动任务失败");
        });
    }

    function startLogStream(phone) {
        const evtSource = new EventSource(`/api/stream?phone=${encodeURIComponent(phone)}`);

        evtSource.addEventListener("log", function (e) {
            const data = JSON.parse(e.data);
            appendLog(data.message);
        });

        evtSource.addEventListener("input_request", function (e) {
            const data = JSON.parse(e.data);
            // 延迟 0.5 秒再弹输入
            setTimeout(() => {
                const value = prompt(data.prompt || "请输入：");
                if (value !== null) {
                    fetch("/api/user-input", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ callback: data.callback, value: value })
                    });
                }
            }, 500);
        });

        evtSource.onerror = function () {
            appendLog("❌ 日志连接中断");
        };
    }

    function appendLog(message) {
        if (!logArea) return;
        logArea.textContent += message + "\n";
        logArea.scrollTop = logArea.scrollHeight;
    }
});
