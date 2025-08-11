import threading
import time

def schedule_all_accounts():
    """每小时执行一次所有账号的任务"""
    while True:
        time.sleep(3600)  # 每小时执行一次
        run_all_accounts()

def run_all_accounts():
    accounts = load_accounts()
    for acc in accounts:
        phone = acc.get("tel")
        if phone:
            threading.Thread(target=run_main_with_account, args=(phone,), daemon=True).start()
    push_log("已执行所有账号任务。")
