import requests
import sys
def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

def collect_home_copper(session, token, user_id):
    """
    领取守家铜币 - 修正版
    """
    # 参数检查
    if not isinstance(user_id, (int, str)):
        print_and_flush(f"❌ 无效的 user_id：{user_id}，请检查 ensure_session_token 返回值顺序")
        return None

    url = "https://q-jiang.myprint.top/api/bas-assets/rentCollection"
    data = {"userId": user_id}
    headers = {"Token": token, "Content-Type": "application/json"}

    print_and_flush(f"🏠 正在为用户 {user_id} 领取守家铜币...")

    try:
        response = session.post(url, headers=headers, json=data, timeout=10)
        response.encoding = 'utf-8'

        if response.status_code != 200 or not response.text.strip():
            print_and_flush(f"❌ 网络错误：HTTP {response.status_code}")
            return None

        result = response.json()

        if result.get("success") and str(result.get("code")) == "200":
            add_copper = result["data"].get("addCopper", 0)
            if add_copper > 0:
                print_and_flush(f"✅ 领取成功！获得 {add_copper} 铜钱")
            else:
                print_and_flush("🟡 本次未获得铜钱（可能尚未产生收益）")
            return result["data"]

        else:
            msg = result.get("msg", "未知错误")
            if "守城时间不足30分钟" in msg:
                print_and_flush("🟡 无法领取：守城时间不足30分钟")
            elif "已征收" in msg or "已领取" in msg:
                print_and_flush(f"🟢 {msg}")
            else:
                print_and_flush(f"🟡 领取失败：{msg}")  # 打印真实原因

            return None

    except Exception as e:
        print_and_flush(f"❌ 请求异常：{e}")
        return None
