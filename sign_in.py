# sign_in.py
# 功能：每月签到奖励模块
# 特点：隐藏 goodsId / mpgId 等技术字段，仅输出用户可见信息

import requests
from datetime import datetime
import sys

# 🌐 接口地址
MONTH_ONLINE_URL = "https://q-jiang.myprint.top/api/bas-assets/monthOnLine"
SIGN_IN_URL = "https://q-jiang.myprint.top/api/bas-assets/receiveMonthOnLineGoods"
CONTINUOUS_ONLINE_URL = "https://q-jiang.myprint.top/api/bas-assets/continuousOnLine"
RECEIVE_ONLINE_REWARD_URL = "https://q-jiang.myprint.top/api/bas-assets/receiveOnLineReward"

def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

def get_sign_in_info(session, token):
    """
    获取签到信息
    :param session: requests.Session() 对象
    :param token: 用户认证 Token
    :return: dict 签到信息或 None
    """
    print_and_flush("🔍 正在获取签到信息...")
    
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    
    try:
        response = session.post(MONTH_ONLINE_URL, headers=headers, json={})
        response.raise_for_status()
        result = response.json()
        
        if result.get("success") and result.get("code") == "200":
            data = result.get("data", {})
            print_and_flush("✅ 签到信息获取成功")
            return data
        else:
            error_msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 获取签到信息失败：{error_msg}")
            return None
            
    except requests.exceptions.RequestException as e:
        print_and_flush(f"❌ 网络请求异常：{e}")
        return None
    except Exception as e:
        print_and_flush(f"❌ 解析响应失败：{e}")
        return None


def daily_check_in(session, token, day=None):
    """
    执行每月签到，自动获取奖励并输出结果
    :param session: requests.Session() 对象
    :param token: 用户认证 Token
    :param day: 签到日期（默认为今天）
    :return: bool 是否成功
    """
    # 先获取签到信息
    sign_info = get_sign_in_info(session, token)
    if not sign_info:
        print_and_flush("❌ 无法获取签到信息，签到失败")
        return False
    
    # 确定签到日期
    if day is None:
        day = datetime.now().day
    else:
        try:
            day = int(day)
            if not (1 <= day <= 31):
                print_and_flush("❌ 日期必须在 1~31 之间")
                return False
        except (ValueError, TypeError):
            print_and_flush("❌ 日期格式错误")
            return False

    print_and_flush(f"\n📅 正在尝试签到：{day} 号 ...")

    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    payload = {"day": day}

    try:
        response = session.post(SIGN_IN_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if result.get("success") and result.get("code") == "200":
            data = result.get("data", {})
            goods_list = data.get("goodsList", [])

            if goods_list:
                # 解析第一个奖励（通常只有一个）
                item = goods_list[0]
                name = item.get("name", "未知物品")
                count = item.get("goodsNum", 0)

                print_and_flush(f"✅ 签到成功！获得：{name} ×{count}")
            else:
                # 兜底：使用 msg 字段
                msg = result.get("msg", "签到成功")
                print_and_flush(f"✅ {msg}")
            return True

        else:
            error_msg = result.get("msg", "未知错误")
            if "已领取" in error_msg or "已经签到" in error_msg or "已签到" in error_msg:
                print_and_flush(f"🟡 今天 {day} 号已签到过")
            else:
                print_and_flush(f"❌ 签到失败：{error_msg}")
            return False

    except requests.exceptions.RequestException as e:
        print_and_flush(f"❌ 网络请求异常：{e}")
        return False
    except Exception as e:
        print_and_flush(f"❌ 解析响应失败：{e}")
        return False


def auto_daily_check_in(session, token):
    """
    快捷函数：自动对今天进行签到
    """
    return daily_check_in(session, token)


def get_continuous_sign_in_info(session, token):
    """
    获取连续签到信息
    :param session: requests.Session() 对象
    :param token: 用户认证 Token
    :return: dict 签到信息或 None
    """
    print_and_flush("🔍 正在获取连续签到信息...")
    
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    
    try:
        response = session.post(CONTINUOUS_ONLINE_URL, headers=headers, json={})
        response.raise_for_status()
        result = response.json()
        
        if result.get("success") and result.get("code") == "200":
            data = result.get("data", {})
            print_and_flush("✅ 连续签到信息获取成功")
            return data
        else:
            error_msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 获取连续签到信息失败：{error_msg}")
            return None
            
    except requests.exceptions.RequestException as e:
        print_and_flush(f"❌ 网络请求异常：{e}")
        return None
    except Exception as e:
        print_and_flush(f"❌ 解析响应失败：{e}")
        return None


def continuous_check_in(session, token, day=None):
    """
    执行连续签到奖励领取
    :param session: requests.Session() 对象
    :param token: 用户认证 Token
    :param day: 星期几（1-7， 默认为今天星期几）
    :return: bool 是否成功
    """
    # 先获取连续签到信息
    sign_info = get_continuous_sign_in_info(session, token)
    if not sign_info:
        print_and_flush("❌ 无法获取连续签到信息，签到失败")
        return False
    
    # 确定签到星期
    if day is None:
        day = datetime.now().isoweekday()  # 返回 1-7，周一为1
    else:
        try:
            day = int(day)
            if not (1 <= day <= 7):
                print_and_flush("❌ 星期必须在 1~7 之间")
                return False
        except (ValueError, TypeError):
            print_and_flush("❌ 星期格式错误")
            return False

    print_and_flush(f"\n📅 正在尝试领取连续签到奖励：星期 {day} ...")

    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    payload = {"day": day}

    try:
        response = session.post(RECEIVE_ONLINE_REWARD_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if result.get("success") and result.get("code") == "200":
            data = result.get("data", {})
            goods_list = data.get("goodsList", [])

            if goods_list:
                # 解析第一个奖励（通常只有一个）
                item = goods_list[0]
                name = item.get("name", "未知物品")
                count = item.get("goodsNum", 0)

                print_and_flush(f"✅ 连续签到奖励领取成功！获得：{name} ×{count}")
            else:
                # 兜底：使用 msg 字段
                msg = result.get("msg", "签到成功")
                print_and_flush(f"✅ {msg}")
            return True

        else:
            error_msg = result.get("msg", "未知错误")
            if "已领取" in error_msg or "已经签到" in error_msg or "已签到" in error_msg:
                print_and_flush(f"🟡 星期 {day} 的奖励已领取过")
            else:
                print_and_flush(f"❌ 连续签到奖励领取失败：{error_msg}")
            return False

    except requests.exceptions.RequestException as e:
        print_and_flush(f"❌ 网络请求异常：{e}")
        return False
    except Exception as e:
        print_and_flush(f"❌ 解析响应失败：{e}")
        return False


def auto_continuous_check_in(session, token):
    """
    快捷函数：自动对今天进行连续签到奖励领取
    """
    return continuous_check_in(session, token)


# ==================== 使用示例（仅用于测试）====================
if __name__ == "__main__":
    print_and_flush("💡 提示：请在主程序中导入使用")
    print_and_flush("       from sign_in import auto_daily_check_in")
    print_and_flush("       auto_daily_check_in(session, token)")
    print_and_flush("       from sign_in import auto_continuous_check_in")
    print_and_flush("       auto_continuous_check_in(session, token)")

    # 示例调用（取消注释并填写真实数据可测试）
    # import requests
    # s = requests.Session()
    # auto_daily_check_in(s, "your_real_token_here")
    # auto_continuous_check_in(s, "your_real_token_here")