# login.py
import requests
import sys
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)
UA = DEFAULT_USER_AGENT
def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()
def login(tel, pwd):
    """
    使用手机号和密码登录，返回 {'token': str, 'user_id': int, 'user_name': str}
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Connection": "keep-alive"
    })

    url = "https://q-jiang.myprint.top/api/user/login"
    payload = {
        "tel": tel,
        "pwd": pwd
    }

    try:
        print_and_flush("🚪 正在登录...")
        response = session.post(url, json=payload, timeout=10)

        if response.status_code != 200:
            print_and_flush(f"❌ 请求失败，状态码: {response.status_code}")
            return None

        result = response.json()
        if result.get("success") and str(result.get("code")) == "200":
            data = result.get("data", {})
            token = data.get("token")
            user_info = data.get("userInfo", {})

            user_id = user_info.get("id")
            user_name = user_info.get("userName", "未知玩家")

            if not token or not user_id:
                print_and_flush("⚠️ 登录响应缺少 token 或 user_id")
                return None

            print_and_flush(f"✅ 登录成功！欢迎 {user_name}！")
            print_and_flush(f"🆔 用户ID: {user_id}")

            # 统一返回 dict，让 main.py 可以直接存
            return {
                "token": token,
                "user_id": user_id,
                "user_name": user_name
            }

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 登录失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 登录异常: {e}")
        return None
