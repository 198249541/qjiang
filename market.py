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
