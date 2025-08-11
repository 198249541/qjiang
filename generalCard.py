# generalCard.py
import requests
import sys
def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()
def get_quality_color_name(quality):
    """根据 quality 返回颜色名称（quality 从 0 开始）"""
    colors = {
        0: "白色",
        1: "绿色",
        2: "蓝色",
        3: "紫色",
        4: "橙色",
        5: "红色"
    }
    return colors.get(quality, "未知")

def get_star_text(star):
    """返回 '数字★' 格式，如 '5★'"""
    return f"{star}★"

def format_general_info(gen):
    """格式化单个武将信息输出"""
    name = gen.get("name", "未知武将").strip()
    star = gen.get("star", 0)           # 实际星级
    quality = gen.get("quality", 0)     # 品质（从 0 开始）
    rank = gen.get("rank")              # 可能为 None/null
    attack = gen.get("attack", 0)
    defense = gen.get("defense", 0)

    star_text = get_star_text(star)
    color_name = get_quality_color_name(quality)

    # 仅当 rank 存在且大于 0 时才显示等级
    level_str = f" ({rank}级)" if rank else ""

    return f"{star_text} ({color_name}) {name}{level_str} 攻:{attack} 防:{defense}"

def get_pub_general_list(session, token):
    """
    获取酒馆中的武将列表
    返回: 武将列表（list）或 None（失败）
    """
    url = "https://q-jiang.myprint.top/api/mid-user-pub/pubGeneralList"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }

    try:
        print_and_flush("🔍 正在获取酒馆武将列表...")
        response = session.post(url, headers=headers, json={})
        response.raise_for_status()

        result = response.json()

        if result.get("success") and result.get("code") == "200":
            user_pub = result["data"].get("userPub")
            if not user_pub:
                print_and_flush("❌ 响应数据中缺少 'userPub' 字段")
                return None

            general_list = user_pub.get("generalList")
            if not isinstance(general_list, list):
                print_and_flush("❌ 'generalList' 字段缺失或不是列表类型")
                return None

            print_and_flush(f"✅ 获取成功，共 {len(general_list)} 位酒馆武将：")
            for gen in general_list:
                print_and_flush(format_general_info(gen))

            return general_list

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 接口返回失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求酒馆列表失败: {e}")
        return None

def recruit_general(session, token, mup_id):
    """
    执行酒馆招募操作
    返回: 招募结果（dict）或 None（失败）
    """
    url = "https://q-jiang.myprint.top/api/mid-user-pub/recruitGeneral"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }

    data = {"mupId": mup_id}

    try:
        print_and_flush(f"🚀 正在执行酒馆招募 (mupId: {mup_id})...")
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()

        if result.get("success") and result.get("code") == "200":
            recruited_general = result["data"].get("general")
            if recruited_general:
                print_and_flush(f"✅ 招募成功！获得武将：{format_general_info(recruited_general)}")
                return recruited_general
            else:
                print_and_flush("❌ 响应数据中缺少 'general' 字段")
                return None

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 招募失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求招募失败: {e}")
        return None