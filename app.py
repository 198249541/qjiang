import json
import logging
import threading
import queue
import subprocess
import sys
import os
import re
import time
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, Response
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from scheduler import schedule_all_accounts  # 导入定时任务模块
from flask import Flask, request, abort
import ipaddress

# 创建 Flask 应用
admin_app = Flask(__name__)
admin_app.secret_key = "admin_secret_key"

# 定义允许的 IP 地址范围
ALLOWED_NETWORK = ipaddress.IPv4Network('192.168.8.0/24', strict=False)

# 在每个请求之前检查 IP 地址
@admin_app.before_request
def limit_remote_addr():
    client_ip = request.remote_addr
    if ipaddress.ip_address(client_ip) not in ALLOWED_NETWORK:
        abort(403)  # 返回 403 Forbidden 错误，表示拒绝访问

# 在此之后，定义你的其他视图和处理逻辑
@admin_app.route("/")
def admin_dashboard():
    # 你的后台管理逻辑
    return "Welcome to the admin dashboard"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

ACCOUNTS_FILE = "accounts.json"
callback_inputs = {}       # 保存 callback_id -> 输入内容
callback_events = {}       # 保存 callback_id -> threading.Event()
callback_phone_map = {}    # 保存 callback_id -> phone（关联到哪个用户）

# 用户端消息队列 {phone: queue.Queue()}
user_event_queues = {}
# 管理端全局队列
admin_event_queue = queue.Queue()
lock = threading.Lock()

# ----------------- 工具函数 -----------------
def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

def get_user_queue(phone):
    with lock:
        if phone not in user_event_queues:
            user_event_queues[phone] = queue.Queue()
        return user_event_queues[phone]

def broadcast_event(phone, event_type, data):
    """向指定手机号推送事件"""
    payload = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    get_user_queue(phone).put(payload)

def broadcast_admin(event_type, data):
    """向 admin 推送事件"""
    payload = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    admin_event_queue.put(payload)

def push_log(message, phone=None):
    """推送日志，phone=None 表示全局"""
    logging.info(message)
    if phone:
        broadcast_event(phone, "log", {"message": message})
    broadcast_admin("log", {"message": f"[{phone or 'GLOBAL'}] {message}"})

def push_input_request(data, phone):
    """推送输入请求，延迟显示"""
    callback_id = data.get("callback") or f"cb_{int(time.time()*1000)}"
    data["callback"] = callback_id
    callback_events[callback_id] = threading.Event()
    callback_phone_map[callback_id] = phone

    # 先推送一条日志，让前端先显示
    prompt_text = data.get("prompt", "请输入：")
    push_log(f"收到输入请求: {prompt_text}", phone)

    # 再推送输入事件
    broadcast_event(phone, "input_request", data)
    broadcast_admin("input_request", {"phone": phone, **data})

# ----------------- Flask 应用 -----------------
user_app = Flask(__name__)
user_app.secret_key = "user_secret_key"

admin_app = Flask(__name__)
admin_app.secret_key = "admin_secret_key"

# 用 werkzeug 生成的 hash，明文是 admin_password
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$zpgYxAob9yU2zomS$8011f3c93e23760019e412630ee6d8dfd9c35f49d2aabc992f945a8ebdb6fd378c374f747961c75a314529263c61a3d7dbae7885974216b11ef33cdddd88206"

# ----------------- 用户端接口 -----------------
@user_app.route("/")
def index():
    return render_template("index.html")

@user_app.route("/api/stream")
def stream():
    phone = request.args.get("phone")
    if not phone:
        return jsonify({"error": "缺少 phone 参数"}), 400
    q = get_user_queue(phone)

    def event_stream():
        while True:
            try:
                payload = q.get()
                yield payload
            except GeneratorExit:
                break

    return Response(event_stream(), mimetype="text/event-stream")

@user_app.route("/api/user-check", methods=["POST"])
def user_check():
    phone = request.json.get("phone")
    accounts = load_accounts()
    exists = any(acc.get("tel") == phone for acc in accounts)
    return jsonify({"exists": exists})

@user_app.route("/api/user-add", methods=["POST"])
def user_add():
    tel = request.json.get("phone")  # 前端还是发 phone，这里接收后转成 tel
    pwd = request.json.get("password")

    accounts = load_accounts()

    if any(acc.get("tel") == tel for acc in accounts):
        return jsonify({"success": False, "error": "账号已存在"})

    accounts.append({
        "id": len(accounts) + 1,
        "tel": tel,
        "pwd": pwd
    })

    save_accounts(accounts)
    return jsonify({"success": True})

@user_app.route("/api/user-run", methods=["POST"])
def user_run():
    phone = request.json.get("phone")
    threading.Thread(target=run_main_with_account, args=(phone,), daemon=True).start()
    return jsonify({"success": True})

@user_app.route("/api/user-input", methods=["POST"])
def user_input():
    callback_id = request.json.get("callback")
    value = request.json.get("value", "")
    if callback_id in callback_events:
        callback_inputs[callback_id] = value
        callback_events[callback_id].set()
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "无效的回调ID"})

# ----------------- 管理端接口 -----------------
@admin_app.route("/", methods=["GET"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html")

@admin_app.route("/login", methods=["POST"])
def admin_login_post():
    password = request.form.get("password")
    if check_password_hash(ADMIN_PASSWORD_HASH, password):
        session["admin_logged_in"] = True
        return redirect(url_for("admin_dashboard"))
    return "<script>alert('密码错误'); window.history.back();</script>"

def get_next_run_time():
    current_time = datetime.now()
    next_run = current_time + timedelta(hours=1)  # 下次运行时间设为一小时后
    return next_run

@admin_app.route("/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    accounts = load_accounts()
    for acc in accounts:
        tel = acc.get("tel", "")
        pwd = acc.get("pwd", "")
        acc["tel_masked"] = tel[:3] + "****" + tel[-4:] if tel else "未知"
        acc["pwd_masked"] = "*" * len(pwd) if pwd else ""
    
    # 获取下次运行时间和剩余时间
    next_run_time = get_next_run_time()  # 获取下次运行时间
    time_left = next_run_time - datetime.now()  # 计算剩余时间
    minutes_left = time_left.total_seconds() // 60  # 转换为分钟数
    seconds_left = int(time_left.total_seconds() % 60)  # 取余得到秒数

    return render_template("admin_dashboard.html", accounts=accounts, total=len(accounts), 
                           minutes_left=minutes_left, seconds_left=seconds_left)


@admin_app.route("/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@admin_app.route("/api/admin-delete/<int:acc_id>", methods=["DELETE"])
def admin_delete(acc_id):
    accounts = load_accounts()
    accounts = [acc for acc in accounts if acc.get("id") != acc_id]
    save_accounts(accounts)
    return jsonify({"success": True})

@admin_app.route("/api/admin-stream")
def admin_stream():
    def event_stream():
        while True:
            try:
                payload = admin_event_queue.get()
                yield payload
            except GeneratorExit:
                break
    return Response(event_stream(), mimetype="text/event-stream")

# ----------------- 定时任务执行 -----------------
def run_all_accounts():
    accounts = load_accounts()
    for acc in accounts:
        phone = acc.get("tel")
        if phone:
            threading.Thread(target=run_main_with_account, args=(phone,), daemon=True).start()
    push_log("已执行所有账号任务。")

def schedule_all_accounts():
    """每小时执行一次所有账号的任务"""
    while True:
        time.sleep(3600)  # 每小时执行一次
        run_all_accounts()

# ----------------- 主任务执行 -----------------
def run_main_with_account(phone):
    push_log("任务已启动", phone)
    push_log(f"检查账号：{phone}", phone)

    accounts = load_accounts()
    acc = next((a for a in accounts if a.get("tel") == phone), None)
    if not acc:
        push_log(f"账号 {phone} 未找到", phone)
        return

    try:
        proc = subprocess.Popen(
            [sys.executable, "main.py", "--tel", acc["tel"], "--pwd", acc["pwd"]],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace"
        )

        for line in proc.stdout:
            line = line.strip()
            if "[INPUT_REQUEST]" in line:
                try:
                    match = re.search(r"\{.*\}$", line)
                    if match:
                        data = json.loads(match.group(0))
                        push_input_request(data, phone)
                        callback_id = data["callback"]

                        # 延迟 0.5 秒再等待用户输入，防止偷跑
                        time.sleep(0.5)

                        if callback_events[callback_id].wait(timeout=15):
                            value = callback_inputs.pop(callback_id, "")
                            proc.stdin.write(value + "\n")
                        else:
                            proc.stdin.write("N\n")
                        proc.stdin.flush()
                except Exception as e:
                    push_log(f"处理 INPUT_REQUEST 失败: {e}", phone)
            else:
                push_log(line, phone)

        proc.wait()
    except Exception as e:
        push_log(f"运行出错: {e}", phone)
    

# ----------------- 启动 -----------------
if __name__ == "__main__":
    run_all_accounts()
    threading.Thread(target=lambda: user_app.run(host="0.0.0.0", port=5000), daemon=True).start()
    threading.Thread(target=schedule_all_accounts, daemon=True).start()  # 启动定时任务
    admin_app.run(host="0.0.0.0", port=5001)
