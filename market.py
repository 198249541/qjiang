# market.py
import requests
import sys
def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()
# 中文字段映射（已移除 userId）
MARKET_FIELDS = {
    "rank": "市场等级",
    "maxCopper": "最大铜钱容量",
    "maxForceLevy": "每日最大强征次数",
    "canForceLevy": "剩余可强征次数",
    "lastLevyTime": "上次征收时间",
    "copper": "可征收铜钱",
    "minutes": "已积攒分钟数"
}

def get_user_info(session, token):
    """
    获取用户个人信息
    """
    url = "https://q-jiang.myprint.top/api/bas-assets/userInfo"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }

    try:
        print_and_flush("🔍 正在获取用户个人信息...")
        response = session.post(url, headers=headers, json={})
        response.raise_for_status()

        result = response.json()

        if result.get("success") and result.get("code") == "200":
            data = result["data"]
            user_info = data.get("userInfo", {})
            
            print_and_flush("✅ 用户个人信息获取成功！")
            print_and_flush("=" * 40)
            
            # 显示关键信息
            username = user_info.get("userName", "未知")
            copper = user_info.get("copper", 0)
            army_provisions = user_info.get("armyProvisions", 0)
            silver_ticket = user_info.get("silverTicket", 0)
            
            print_and_flush(f"用户名: {username}")
            print_and_flush(f"铜钱: {copper}")
            print_and_flush(f"粮食: {army_provisions}")
            print_and_flush(f"银票: {silver_ticket}")
            
            print_and_flush("=" * 40)
            return user_info

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 获取用户信息失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求用户信息失败: {e}")
        return None

def auto_change_silver_ticket(session, token):
    """
    自动兑换银票（保留100万铜钱，其余用于兑换）
    每一张银票需要扣除100铜钱和1粮食
    """
    # 先获取用户信息
    user_info = get_user_info(session, token)
    if not user_info:
        print_and_flush("❌ 无法获取用户信息，取消自动兑换")
        return False
    
    copper = user_info.get("copper", 0)
    army_provisions = user_info.get("armyProvisions", 0)
    
    # 计算可兑换的铜钱数量（保留100万）
    reserve_copper = 1000000
    available_copper = max(0, copper - reserve_copper)
    
    if available_copper < 100:
        print_and_flush("保留一百万铜钱后ℹ️  可用铜钱不足100，无法兑换银票")
        return False
    
    # 计算可兑换的银票数量（受铜钱和粮食限制）
    max_by_copper = available_copper // 100
    max_by_provisions = army_provisions
    num_to_exchange = min(max_by_copper, max_by_provisions)
    
    if num_to_exchange <= 0:
        print_and_flush("ℹ️  无可兑换的银票数量（铜钱或粮食不足）")
        return False
    
    # 执行兑换
    return change_silver_ticket(session, token, num_to_exchange)

def get_market_info(session, token):
    """
    获取市场信息，判断是否可征收，并计算距离满还剩多少时间
    """
    url = "https://q-jiang.myprint.top/api/bas-assets/marketInfo"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }

    try:
        print_and_flush("🔍 正在获取市场信息...")
        response = session.post(url, headers=headers, json={})
        response.raise_for_status()

        result = response.json()

        if result.get("success") and result.get("code") == "200":
            data = result["data"]
            user_market = data.get("userMarket", {})

            # 提取关键数值
            current_copper = user_market.get("copper", 0)
            max_copper = user_market.get("maxCopper", 0)
            minutes_accumulated = user_market.get("minutes", 0)

            print_and_flush("✅ 市场信息获取成功！")
            print_and_flush("=" * 40)

            # 打印字段（不包含 userId）
            for key, value in user_market.items():
                if key in MARKET_FIELDS:
                    label = MARKET_FIELDS[key]
                    print_and_flush(f"{label}: {value}")

            # 判断是否可征收
            if current_copper >= max_copper:
                print_and_flush("是否可征收: ✅ 是（铜钱已满，建议立即征收！）")
                levy_response = levy_copper(session, token)
                if levy_response:
                    print_and_flush("征收成功！")
                else:
                    print_and_flush("征收失败，请检查网络或稍后再试。")
            else:
                remaining_copper = max_copper - current_copper
                remaining_seconds = remaining_copper  # 每秒1铜钱
                remaining_minutes = remaining_seconds // 60
                remaining_hours = remaining_minutes // 60
                remaining_minutes %= 60

                if current_copper > 0.8 * max_copper:
                    print_and_flush("是否可征收: ⏳ 否（铜钱接近满，正在积累...）")
                    print_and_flush(f"建议关注: 还差 {remaining_copper} 铜钱")
                    print_and_flush(f"预计还需: {remaining_hours} 小时 {remaining_minutes} 分钟")
                else:
                    print_and_flush("是否可征收: ❌ 否（铜钱未满）")
                    print_and_flush(f"还差 {remaining_copper} 铜钱，约 {remaining_hours} 小时 {remaining_minutes} 分钟")

            # 已积攒时间说明
            hours_acc = minutes_accumulated // 60
            mins_acc = minutes_accumulated % 60
            print_and_flush(f"📌 当前已积攒: {hours_acc} 小时 {mins_acc} 分钟")

            print_and_flush("=" * 40)

            return data

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 接口返回失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求市场信息失败: {e}")
        return None

def levy_copper(session, token):
    """
    发送征收请求
    """
    url = "https://q-jiang.myprint.top/api/bas-assets/levy"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }
    data = {"u": 1, "i": 1}  # 根据实际需求调整数据

    try:
        print_and_flush("🚀 正在发送征收请求...")
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        if result.get("success") and result.get("code") == "200":
            print_and_flush("征收请求发送成功！")
            return True
        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 征收请求失败: {msg}")
            return False

    except Exception as e:
        print_and_flush(f"❌ 发送征收请求失败: {e}")
        return False

def change_silver_ticket(session, token, num=15):
    """
    兑换银票接口
    每一张银票需要扣除100铜钱和1粮食
    :param session: requests session
    :param token: 用户token
    :param num: 兑换银票数量，默认15张
    """
    url = "https://q-jiang.myprint.top/api/bas-assets/changeSilverTicket"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }
    data = {"num": num}  # 使用num参数，表示兑换银票的数量

    try:
        print_and_flush(f"🔄 正在兑换银票... (兑换数量: {num}张)")
        print_and_flush(f"📌 将消耗 {num * 100} 铜钱和 {num} 粮食")
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        if result.get("success") and result.get("code") == "200":
            print_and_flush("✅ 银票兑换成功！")
            return True
        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 银票兑换失败: {msg}")
            return False

    except Exception as e:
        print_and_flush(f"❌ 发送银票兑换请求失败: {e}")
        return False