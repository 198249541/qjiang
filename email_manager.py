# email_manager.py
import requests
import json
import time
import os
from typing import List, Dict, Any
from datetime import datetime
from collections import OrderedDict
import sys
from collections import defaultdict

def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

# 抽奖追踪器
lottery_tracker = {
    "total_draws": 0,
    "rewards": [],
    "draw_history": []
}

# 缓存文件路径
CACHE_FILE_PATH = "unprocessable_emails_cache.json"

# 无法处理的邮件缓存
unprocessable_emails_cache = set()

def load_cache_from_file():
    """从文件加载缓存"""
    global unprocessable_emails_cache
    try:
        if os.path.exists(CACHE_FILE_PATH):
            with open(CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                unprocessable_emails_cache = set(cache_data.get("unprocessable_emails", []))
            print_and_flush(f"✅ 已从文件加载 {len(unprocessable_emails_cache)} 个无法处理的邮件ID")
        else:
            print_and_flush("📝 缓存文件不存在，将创建新的缓存文件")
    except Exception as e:
        print_and_flush(f"⚠️ 读取缓存文件时出错: {e}")
        unprocessable_emails_cache = set()

def save_cache_to_file():
    """将缓存保存到文件"""
    try:
        cache_data = {
            "unprocessable_emails": list(unprocessable_emails_cache),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print_and_flush(f"✅ 已将 {len(unprocessable_emails_cache)} 个无法处理的邮件ID 保存到文件")
    except Exception as e:
        print_and_flush(f"⚠️ 保存缓存文件时出错: {e}")

def reset_lottery_tracker():
    """重置抽奖记录"""
    global lottery_tracker
    lottery_tracker = {
        "total_draws": 0,
        "rewards": [],
        "draw_history": []
    }

def record_lottery_result(email_id: int, title: str, reward: str):
    """记录抽奖结果"""
    global lottery_tracker
    lottery_tracker["total_draws"] += 1
    lottery_tracker["rewards"].append(reward)
    lottery_tracker["draw_history"].append({
        "draw_number": lottery_tracker["total_draws"],
        "email_id": email_id,
        "email_title": title,
        "reward": reward
    })

def display_lottery_summary():
    """展示抽奖总结"""
    global lottery_tracker
    if lottery_tracker["total_draws"] == 0:
        print_and_flush("🎲 本次运行没有进行抽奖")
        return
    
    print_and_flush("\n" + "="*40)
    print_and_flush("🎲 抽奖结果统计")
    print_and_flush("="*40)
    print_and_flush(f"总抽奖次数: {lottery_tracker['total_draws']}")
    
    # 统计奖励分布
    reward_count = defaultdict(int)
    for reward in lottery_tracker["rewards"]:
        reward_count[reward] += 1
    
    print_and_flush("\n奖励获得情况:")
    for reward, count in reward_count.items():
        print_and_flush(f"  {reward}: {count}次")
    
    print_and_flush(f"\n详细抽奖记录:")
    for record in lottery_tracker["draw_history"]:
        print_and_flush(f"  {record['draw_number']}. 邮件'{record['email_title']}' 获得: {record['reward']}")
    print_and_flush("="*40)

def add_to_unprocessable_cache(email_id: int):
    """将邮件添加到无法处理的缓存中"""
    global unprocessable_emails_cache
    unprocessable_emails_cache.add(email_id)
    print_and_flush(f"📝 邮件 {email_id} 已添加到无法处理缓存中")
    save_cache_to_file()  # 保存到文件

def is_in_unprocessable_cache(email_id: int) -> bool:
    """检查邮件是否在无法处理的缓存中"""
    return email_id in unprocessable_emails_cache

def clear_unprocessable_cache():
    """清空无法处理的邮件缓存"""
    global unprocessable_emails_cache
    unprocessable_emails_cache.clear()
    print_and_flush("🧹 无法处理邮件缓存已清空")
    save_cache_to_file()  # 保存到文件

def get_email_list(session: requests.Session, token: str) -> List[Dict[str, Any]]:
    """
    获取邮件列表
    
    Args:
        session: requests会话对象
        token: 用户认证token
    
    Returns:
        邮件列表
    """
    url = "https://q-jiang.myprint.top/api/user-email/list"
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    
    try:
        response = session.post(url, headers=headers, json={}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            
            if isinstance(data.get("data"), list):
                emails = data.get("data")
                # 将 otherId 转为 uuid 字段
                for email in emails:
                    if "otherId" in email:
                        email["uuid"] = email.get("otherId", "")
                return emails
            
            print_and_flush(f"❌ 获取邮件列表失败: 数据格式不正确")
            return []
        else:
            print_and_flush(f"❌ 获取邮件列表失败: {data.get('msg', '未知错误')}")
            return []
            
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
    except json.JSONDecodeError as e:
        print_and_flush(f"⚠️ JSON解析错误: {e}")
    except Exception as e:
        print_and_flush(f"⚠️ 获取邮件列表时发生未知错误: {e}")
    
    return []

def is_email_expired(invalid_day: str) -> bool:
    if not invalid_day:
        return False
    try:
        expire_date = datetime.strptime(invalid_day, "%Y-%m-%d")
        current_date = datetime.now()
        # 修改为 <= 以包括今天过期的邮件
        return expire_date.date() <= current_date.date()
    except ValueError:
        return False

def format_email_info(email: Dict[str, Any]) -> str:
    email_id = email.get("id", "未知")
    title = email.get("title", "无标题")
    email_type = email.get("type", 0)
    receive_is = email.get("receiveIs", 0)
    invalid_day = email.get("invalidDay", "")
    goods_list = email.get("goodsListVo", [])
    
    # 为类型40邮件添加特殊标识
    if email_type == 40:
        attachment_status = "🎲"  # 使用骰子表情表示抽奖邮件
        receive_status = "已领" if receive_is == 1 else "未领"
        result = f"{attachment_status}[{receive_status}][抽奖] {title}"
    else:
        attachment_status = "📎" if goods_list or email_type == 40 else ""
        receive_status = "已领" if receive_is == 1 else "未领"
        result = f"{attachment_status}[{receive_status}][类型{email_type}] {title}"
    
    if goods_list and isinstance(goods_list, list) and email_type != 40:
        reward_items = []
        for goods in goods_list:
            if isinstance(goods, dict):
                goods_name = goods.get("name", "未知物品")
                goods_num = goods.get("num", 1)
                reward_items.append(f"{goods_name}x{goods_num}")
        if reward_items:
            result += " 奖励: " + ", ".join(reward_items)
    if invalid_day:
        result += f" (过期时间: {invalid_day})"
    return result

def display_emails(session: requests.Session, token: str) -> None:
    print_and_flush("📧 正在获取邮件列表...")
    emails = get_email_list(session, token)
    if not emails:
        print_and_flush("⚠️ 暂无邮件或获取失败")
        return
    
    # 只显示未领取附件的邮件（不再过滤类型为40的邮件）
    unclaimed_emails = [email for email in emails 
                       if email.get("receiveIs", 0) == 0 and 
                       not is_email_expired(email.get("invalidDay", ""))]  # 移除类型40的过滤
    
    unclaimed_count = sum(1 for email in unclaimed_emails if 
                         (email.get("goodsListVo") or email.get("type", 0) == 40))
    
    print_and_flush(f"✅ 获取到 {len(unclaimed_emails)} 封未领取邮件 (未领附件: {unclaimed_count}封):")
    for i, email in enumerate(unclaimed_emails, 1):
        try:
            print_and_flush(f"  {i}. {format_email_info(email)}")
        except Exception as e:
            print_and_flush(f"  {i}. 邮件信息解析失败: {e}")

def read_email(session: requests.Session, token: str, email_id: int) -> bool:
    url = "https://q-jiang.myprint.top/api/user-email/read"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"id": email_id}
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            print_and_flush(f"✅ 邮件 {email_id} 已标记为已读")
            return True
        else:
            print_and_flush(f"❌ 阅读邮件 {email_id} 失败: {data.get('msg', '未知错误')}")
            return False
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
    except Exception as e:
        print_and_flush(f"⚠️ 阅读邮件时发生未知错误: {e}")
    return False

def delete_email(session: requests.Session, token: str, email_id: int) -> bool:
    # 检查邮件是否在无法处理缓存中
    if is_in_unprocessable_cache(email_id):
        print_and_flush(f"⏭️ 邮件 {email_id} 在无法处理缓存中，跳过删除")
        return False
    
    url = "https://q-jiang.myprint.top/api/user-email/delEmail"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"id": email_id}
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        print_and_flush(f"📤 删除邮件 {email_id} 接口响应: {data}")  # 打印响应数据
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            print_and_flush(f"✅ 邮件 {email_id} 删除成功")
            # 从无法处理缓存中移除（如果存在）
            if email_id in unprocessable_emails_cache:
                unprocessable_emails_cache.discard(email_id)
                save_cache_to_file()  # 保存到文件
            return True
        else:
            print_and_flush(f"❌ 删除邮件 {email_id} 失败: {data.get('msg', '未知错误')}")
            # 添加到无法处理缓存
            add_to_unprocessable_cache(email_id)
            return False
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
    except Exception as e:
        print_and_flush(f"⚠️ 删除邮件时发生未知错误: {e}")
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
    return False

def delete_expired_email(session: requests.Session, token: str, email_id: int) -> bool:
    """
    删除过期邮件
    使用专门的删除过期邮件接口
    """
    # 检查邮件是否在无法处理缓存中
    if is_in_unprocessable_cache(email_id):
        print_and_flush(f"⏭️ 邮件 {email_id} 在无法处理缓存中，跳过删除")
        return False
    
    url = "https://q-jiang.myprint.top/api/user-email/delEmail"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"id": email_id}
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        print_and_flush(f"📤 删除过期邮件 {email_id} 接口响应: {data}")  # 打印响应数据
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            print_and_flush(f"✅ 过期邮件 {email_id} 删除成功")
            # 从无法处理缓存中移除（如果存在）
            if email_id in unprocessable_emails_cache:
                unprocessable_emails_cache.discard(email_id)
                save_cache_to_file()  # 保存到文件
            return True
        else:
            print_and_flush(f"❌ 删除过期邮件 {email_id} 失败: {data.get('msg', '未知错误')}")
            # 添加到无法处理缓存
            add_to_unprocessable_cache(email_id)
            return False
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
    except Exception as e:
        print_and_flush(f"⚠️ 删除过期邮件时发生未知错误: {e}")
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
    return False

def delete_email_all(session: requests.Session, token: str, email_id: int) -> bool:
    """
    使用 delEmailAll 接口删除邮件
    专门用于删除类型为50和60的邮件
    """
    # 检查邮件是否在无法处理缓存中
    if is_in_unprocessable_cache(email_id):
        print_and_flush(f"⏭️ 邮件 {email_id} 在无法处理缓存中，跳过删除")
        return False
    
    url = "https://q-jiang.myprint.top/api/user-email/delEmailAll"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"id": email_id}
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        print_and_flush(f"📤 删除邮件 {email_id} (delEmailAll接口) 响应: {data}")  # 打印响应数据
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            print_and_flush(f"✅ 邮件 {email_id} 删除成功 (使用delEmailAll接口)")
            # 从无法处理缓存中移除（如果存在）
            if email_id in unprocessable_emails_cache:
                unprocessable_emails_cache.discard(email_id)
                save_cache_to_file()  # 保存到文件
            return True
        else:
            print_and_flush(f"❌ 删除邮件 {email_id} 失败: {data.get('msg', '未知错误')} (使用delEmailAll接口)")
            # 添加到无法处理缓存
            add_to_unprocessable_cache(email_id)
            return False
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e} (使用delEmailAll接口)")
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
    except Exception as e:
        print_and_flush(f"⚠️ 删除邮件时发生未知错误: {e} (使用delEmailAll接口)")
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
    return False

def get_email_attachment(session: requests.Session, token: str, email_id: int) -> bool:
    url = "https://q-jiang.myprint.top/api/user-email/getAttachment"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"id": email_id}
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            print_and_flush(f"✅ 邮件 {email_id} 附件领取成功: {data.get('msg', '')}")
            return True
        else:
            print_and_flush(f"❌ 领取邮件 {email_id} 附件失败: {data.get('msg', '未知错误')}")
            return False
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
    except Exception as e:
        print_and_flush(f"⚠️ 领取邮件附件时发生未知错误: {e}")
    return False

def receive_email_attachment(session: requests.Session, token: str, email_id: int) -> bool:
    """
    领取类型为50和60的邮件附件
    使用 receiveEmail 接口
    """
    url = "https://q-jiang.myprint.top/api/user-email/receiveEmail"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"id": email_id}
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            print_and_flush(f"✅ 邮件 {email_id} 附件领取成功: {data.get('msg', '')}")
            return True
        else:
            print_and_flush(f"❌ 领取邮件 {email_id} 附件失败: {data.get('msg', '未知错误')}")
            return False
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
    except Exception as e:
        print_and_flush(f"⚠️ 领取邮件附件时发生未知错误: {e}")
    return False

def get_lottery_info(session: requests.Session, token: str, email_id: int, uuid: str) -> Dict[str, Any]:
    """
    获取类型40邮件的抽奖信息
    
    Args:
        session: requests会话对象
        token: 用户认证token
        email_id: 邮件ID
        uuid: 邮件UUID
    
    Returns:
        抽奖信息
    """
    # 检查邮件是否在无法处理缓存中
    if is_in_unprocessable_cache(email_id):
        print_and_flush(f"⏭️ 邮件 {email_id} 在无法处理缓存中，跳过处理")
        return {}
    
    url = "https://q-jiang.myprint.top/api/user-email/customsEmailRewardInfo"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"id": email_id, "uuid": uuid}
    
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            return data.get("data", {})
        else:
            error_msg = data.get('msg', '未知错误')
            print_and_flush(f"❌ 获取抽奖信息失败: {error_msg}")
            # 当出现"此接口只可访问一次"相关错误时，删除该邮件
            if "此接口只可访问一次" in error_msg:
                print_and_flush(f"⚠️ 邮件 {email_id} 已无有效抽奖次数，正在删除...")
                delete_email(session, token, email_id)
            # 添加到无法处理缓存
            add_to_unprocessable_cache(email_id)
            return {}
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
    except Exception as e:
        print_and_flush(f"⚠️ 获取抽奖信息时发生未知错误: {e}")
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
    
    return {}

def execute_lottery(session: requests.Session, token: str, email_id: int, uuid: str, lottery_info: Dict[str, Any] = None, email_title: str = "") -> bool:
    """
    执行类型40邮件的抽奖
    
    Args:
        session: requests会话对象
        token: 用户认证token
        email_id: 邮件ID
        uuid: 邮件UUID
        lottery_info: 抽奖信息（可选，避免重复请求）
        email_title: 邮件标题（用于记录）
    """
    # 检查邮件是否在无法处理缓存中
    if is_in_unprocessable_cache(email_id):
        print_and_flush(f"⏭️ 邮件 {email_id} 在无法处理缓存中，跳过处理")
        return False
    
    url = "https://q-jiang.myprint.top/api/user-email/customsEmailReward"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"id": email_id, "uuid": uuid, "giveUpList": []}
    
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            
            # 获取实际抽中的奖励信息
            reward_data = data.get("data")
            
            # 当数据异常（例如返回None或空数据）时，删除邮件
            if reward_data is None or (isinstance(reward_data, dict) and not reward_data):
                print_and_flush(f"⚠️ 邮件 {email_id} 抽奖数据异常，此接口只可访问一次，迎接审判吧！")
                # 调用删除接口删除此邮件
                delete_email(session, token, email_id)
                record_lottery_result(email_id, email_title, "数据异常已删除")
                # 添加到无法处理缓存
                add_to_unprocessable_cache(email_id)
                return False
            
            # 获取可抽奖物品列表（如果提供了lottery_info则使用，否则尝试重新获取）
            goods_list = []
            if lottery_info and isinstance(lottery_info, dict):
                goods_list = lottery_info.get("goodsVos", [])
            else:
                # 只有在没有提供lottery_info时才尝试获取，避免重复请求
                temp_lottery_info = get_lottery_info(session, token, email_id, uuid)
                if temp_lottery_info:
                    goods_list = temp_lottery_info.get("goodsVos", [])
            
            reward_name = "未知奖励"
            # 如果reward_data是整数，表示抽中的物品在列表中的索引（从0开始）
            if isinstance(reward_data, int) and goods_list:
                # 确保索引在有效范围内
                if 0 <= reward_data < len(goods_list):
                    reward_item = goods_list[reward_data]
                    reward_name = reward_item.get("name", "未知奖励")
                    reward_weight = reward_item.get("weight", 0)
                    print_and_flush(f"✅ 邮件 {email_id} 抽奖成功: 获得 {reward_name} (权重: {reward_weight})")
                else:
                    reward_name = f"第 {reward_data + 1} 个奖励"
                    print_and_flush(f"✅ 邮件 {email_id} 抽奖成功: 获得{reward_name}")
            elif reward_data:
                # 如果reward_data是字典或其他类型，按原有方式处理
                if isinstance(reward_data, dict):
                    reward_name = reward_data.get("name", "未知奖励")
                    reward_num = reward_data.get("num", 1)
                    print_and_flush(f"✅ 邮件 {email_id} 抽奖成功: 获得 {reward_name} x {reward_num}")
                else:
                    reward_name = str(reward_data)
                    print_and_flush(f"✅ 邮件 {email_id} 抽奖成功: {data.get('msg', '')}")
            else:
                reward_name = "未知奖励"
                print_and_flush(f"✅ 邮件 {email_id} 抽奖成功: {data.get('msg', '')}")
            
            # 记录抽奖结果
            record_lottery_result(email_id, email_title, reward_name)
            return True
        else:
            print_and_flush(f"❌ 邮件 {email_id} 抽奖失败: {data.get('msg', '未知错误')}")
            # 记录失败的抽奖
            record_lottery_result(email_id, email_title, "抽奖失败")
            # 添加到无法处理缓存
            add_to_unprocessable_cache(email_id)
            return False
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
    except Exception as e:
        print_and_flush(f"⚠️ 执行抽奖时发生未知错误: {e}")
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
    
    # 记录异常的抽奖
    record_lottery_result(email_id, email_title, "异常错误")
    return False

def process_lottery_email(session: requests.Session, token: str, email_id: int, uuid: str, email_title: str = "") -> bool:
    """
    处理类型为40的抽奖邮件
    
    Args:
        session: requests会话对象
        token: 用户认证token
        email_id: 邮件ID
        uuid: 邮件UUID
        email_title: 邮件标题
    
    Returns:
        是否成功处理
    """
    # 检查邮件是否在无法处理缓存中
    if is_in_unprocessable_cache(email_id):
        print_and_flush(f"⏭️ 邮件 {email_id} 在无法处理缓存中，跳过处理")
        return False
    
    # 首先获取抽奖信息
    print_and_flush(f"🎲 正在获取邮件 {email_id} 的抽奖信息...")
    lottery_info = get_lottery_info(session, token, email_id, uuid)
    
    if not lottery_info:
        print_and_flush(f"❌ 无法获取邮件 {email_id} 的抽奖信息")
        record_lottery_result(email_id, email_title, "获取抽奖信息失败")
        return False
    
    goods_list = lottery_info.get("goodsVos", [])
    if not goods_list:
        print_and_flush(f"⚠️ 邮件 {email_id} 没有可抽奖的物品")
        record_lottery_result(email_id, email_title, "无抽奖物品")
    
    # 显示可抽奖物品
    # print_and_flush(f"🎁 邮件 {email_id} 可抽取的物品:")
    # for i, goods in enumerate(goods_list, 1):
    #     name = goods.get("name", "未知物品")
    #     weight = goods.get("weight", 0)
    #     print_and_flush(f"  {i}. {name} (权重: {weight})")
    
    # 执行抽奖，传递lottery_info避免重复请求
    print_and_flush(f"🎲 正在执行抽奖...")
    result = execute_lottery(session, token, email_id, uuid, lottery_info, email_title)
    
    # 如果抽奖失败，添加到无法处理缓存
    if not result:
        add_to_unprocessable_cache(email_id)
    
    return result

def process_all_customs_emails(session: requests.Session, token: str) -> None:
    """
    处理所有类型为40的抽奖邮件
    """
    # 重置抽奖记录
    reset_lottery_tracker()
    
    print_and_flush("🎲 正在处理所有抽奖邮件...")
    emails = get_email_list(session, token)
    if not emails:
        print_and_flush("⚠️ 暂无邮件或获取失败")
        return
    
    lottery_count = 0
    for email in emails:
        try:
            email_id = email.get("id", 0)
            email_type = email.get("type", 0)
            receive_is = email.get("receiveIs", 0)
            title = email.get("title", "无标题")
            invalid_day = email.get("invalidDay", "")
            uuid = email.get("uuid", "")
            
            # 处理类型为40且未领取的邮件
            if email_type == 40 and receive_is == 0 and email_id and not is_email_expired(invalid_day):
                print_and_flush(f"🎲 正在处理抽奖邮件: '{title}' (ID: {email_id})")
                # 再次检查邮件是否仍然存在（可能在处理其他邮件时已被删除）
                current_emails = get_email_list(session, token)
                email_still_exists = any(e.get("id") == email_id for e in current_emails)
                
                if not email_still_exists:
                    print_and_flush(f"⚠️ 邮件 {email_id} 已被删除，跳过处理")
                    continue
                    
                if process_lottery_email(session, token, email_id, uuid, title):
                    lottery_count += 1
                    time.sleep(0.5)
        except Exception as e:
            print_and_flush(f"⚠️ 处理抽奖邮件 '{title}' 时出错: {e}")
    
    if lottery_count > 0:
        print_and_flush(f"✅ 共处理了 {lottery_count} 个抽奖邮件")
    else:
        print_and_flush("🔍 没有可处理的抽奖邮件")
    
    # 显示抽奖总结
    display_lottery_summary()

def get_all_attachments(session: requests.Session, token: str) -> None:
    print_and_flush("📎 正在检查可领取的邮件附件...")
    
    # 重置抽奖记录（如果是第一次调用）
    if lottery_tracker["total_draws"] == 0:
        reset_lottery_tracker()
        
    emails = get_email_list(session, token)
    if not emails:
        print_and_flush("⚠️ 暂无邮件或获取失败")
        return
    claimed_count = 0
    skipped_count = 0
    lottery_count = 0
    for email in emails:
        try:
            email_id = email.get("id", 0)
            receive_is = email.get("receiveIs", 0)
            title = email.get("title", "无标题")
            goods_list = email.get("goodsListVo", [])
            email_type = email.get("type", 0)
            invalid_day = email.get("invalidDay", "")
            uuid = email.get("uuid", "")
            # 处理未领取的邮件，包括类型为40的抽奖邮件
            if (goods_list or email_type == 40) and receive_is == 0 and email_id:
                if is_email_expired(invalid_day):
                    skipped_count += 1
                    continue
                
                # 再次检查邮件是否仍然存在
                current_emails = get_email_list(session, token)
                email_still_exists = any(e.get("id") == email_id for e in current_emails)
                
                if not email_still_exists:
                    print_and_flush(f"⚠️ 邮件 {email_id} 已被删除，跳过处理")
                    continue
                
                if email_type == 40:
                    print_and_flush(f"🎲 正在处理抽奖邮件 '{title}' ...")
                    if process_lottery_email(session, token, email_id, uuid, title):
                        lottery_count += 1
                        claimed_count += 1
                        time.sleep(0.5)
                else:
                    print_and_flush(f"📥 正在领取邮件 '{title}' 的附件...")
                    # 根据邮件类型选择合适的接口
                    if email_type in [50, 60]:  # 支持类型50和60
                        # 类型为50/60的邮件使用 receiveEmail 接口
                        result = receive_email_attachment(session, token, email_id)
                    else:
                        # 其他类型的邮件使用 getAttachment 接口
                        result = get_email_attachment(session, token, email_id)
                    
                    if result:
                        claimed_count += 1
                        time.sleep(0.5)
        except Exception as e:
            print_and_flush(f"⚠️ 处理邮件 '{email.get('title', '未知')}' 时出错: {e}")
    if claimed_count > 0:
        print_and_flush(f"✅ 共领取了 {claimed_count} 个邮件附件，其中抽奖邮件 {lottery_count} 个")
    if skipped_count > 0:
        print_and_flush(f"⏭️ 共跳过了 {skipped_count} 个已过期的邮件")
    if claimed_count == 0 and skipped_count == 0:
        print_and_flush("🔍 没有可领取的邮件附件")
    
    # 显示抽奖总结
    display_lottery_summary()

def delete_all_claimed_emails(session: requests.Session, token: str) -> None:
    """
    自动删除所有已领取附件的邮件（无论是否过期）
    包括类型为50和60的已领取邮件
    """
    print_and_flush("🗑️ 正在检查并删除已领取的邮件...")
    emails = get_email_list(session, token)
    if not emails:
        print_and_flush("⚠️ 暂无邮件或获取失败")
        return
    
    deleted_count = 0
    error_count = 0
    
    for email in emails:
        try:
            email_id = email.get("id", 0)
            title = email.get("title", "无标题")
            receive_is = email.get("receiveIs", 0)
            email_type = email.get("type", 0)
            invalid_day = email.get("invalidDay", "")
            
            # 检查邮件是否已领取且未过期，并排除类型为40的邮件
            if receive_is == 1 and email_id and not is_email_expired(invalid_day) and email_type != 40:
                print_and_flush(f"🗑️ 正在删除已领取邮件: '{title}' (ID: {email_id})")
                # 类型为50/60的邮件优先使用 delEmailAll 接口
                success = False
                if email_type in [50, 60]:  # 支持类型50和60
                    if delete_email_all_with_verification(session, token, email_id):
                        deleted_count += 1
                        success = True
                    elif delete_email(session, token, email_id):
                        deleted_count += 1
                        success = True
                else:
                    if delete_email(session, token, email_id):
                        deleted_count += 1
                        success = True
                
                if not success:
                    error_count += 1
                time.sleep(0.5)  # 避免请求过快
        except Exception as e:
            print_and_flush(f"⚠️ 删除已领取邮件 '{email.get('title', '未知')}' 时出错: {e}")
            error_count += 1
    
    if deleted_count > 0:
        print_and_flush(f"✅ 共删除了 {deleted_count} 封已领取的邮件")
    if error_count > 0:
        print_and_flush(f"⚠️ 共有 {error_count} 封已领取邮件删除失败")
    if deleted_count == 0 and error_count == 0:
        print_and_flush("🔍 没有已领取的邮件需要删除")
    
    if deleted_count > 0:
        print_and_flush(f"✅ 共删除了 {deleted_count} 封已领取的邮件")
    if error_count > 0:
        print_and_flush(f"⚠️ 共有 {error_count} 封已领取邮件删除失败")
    if deleted_count == 0 and error_count == 0:
        print_and_flush("🔍 没有已领取的邮件需要删除")

def delete_claimed_and_expired_emails(session: requests.Session, token: str) -> None:
    """
    删除所有已领取的邮件和所有过期的邮件
    """
    print_and_flush("🗑️ 正在删除已领取和过期的邮件...")
    emails = get_email_list(session, token)
    if not emails:
        print_and_flush("⚠️ 暂无邮件或获取失败")
        return
    
    deleted_count = 0
    error_count = 0
    
    for email in emails:
        try:
            email_id = email.get("id", 0)
            title = email.get("title", "无标题")
            receive_is = email.get("receiveIs", 0)
            invalid_day = email.get("invalidDay", "")
            email_type = email.get("type", 0)
            
            # 删除条件：已领取 或 已过期，并排除类型为40的邮件
            should_delete = False
            
            # 已领取的邮件（无论是否过期）
            if receive_is == 1 and email_id and email_type != 40:
                should_delete = True
                print_and_flush(f"🗑️ 正在删除已领取邮件: '{title}' (ID: {email_id})")
            
            # 过期的邮件（无论是否已领取）
            elif is_email_expired(invalid_day) and email_id and email_type != 40:
                receive_status = "已领" if receive_is == 1 else "未领"
                print_and_flush(f"🗑️ 正在删除过期邮件: [{receive_status}] '{title}' (ID: {email_id})")
                should_delete = True
            
            if should_delete:
                # 根据邮件类型选择删除接口
                success = False
                if email_type in [50, 60]:  # 支持类型50和60
                    # 类型为50/60的邮件优先使用 delEmailAll 接口
                    if delete_email_all(session, token, email_id):
                        success = True
                    # 如果 delEmailAll 接口失败，再尝试其他接口
                    elif delete_expired_email(session, token, email_id):
                        success = True
                    elif delete_email(session, token, email_id):
                        success = True
                else:
                    # 对于过期邮件优先使用专门的删除接口
                    if is_email_expired(invalid_day):
                        if delete_expired_email(session, token, email_id):
                            success = True
                        elif delete_email(session, token, email_id):
                            success = True
                    else:
                        if delete_email(session, token, email_id):
                            success = True
                
                # 如果所有接口都失败，检查是否是"审判"情况
                if not success:
                    # 尝试调用任意一个删除接口，检查返回信息
                    # 这里我们使用 delete_email 接口来检查是否是审判情况
                    url = "https://q-jiang.myprint.top/api/user-email/delEmail"
                    headers = {"Token": token, "Content-Type": "application/json"}
                    payload = {"id": email_id}
                    try:
                        response = session.post(url, headers=headers, json=payload, timeout=10)
                        response.raise_for_status()
                        data = response.json()
                        print_and_flush(f"📤 审判检查 - 邮件 {email_id} 接口响应: {data}")  # 打印响应数据
                        error_msg = data.get('msg', '')
                        # 当出现"此接口只可访问一次次数+1，迎接审判吧！"相关错误时
                        if "此接口只可访问一次" in error_msg and "迎接审判吧" in error_msg:
                            print_and_flush(f"⚠️ 邮件 {email_id} 触发审判机制，正在删除...")
                            # 审判情况下，我们视作删除成功
                            success = True
                    except Exception as e:
                        print_and_flush(f"⚠️ 检查审判情况时发生异常: {e}")
                        pass  # 忽略检查过程中的异常
                
                # 根据操作结果更新计数
                if success:
                    deleted_count += 1
                else:
                    error_count += 1
                    
                time.sleep(0.5)  # 避免请求过快
                
        except Exception as e:
            print_and_flush(f"⚠️ 删除邮件 '{email.get('title', '未知')}' 时出错: {e}")
            error_count += 1
    
    if deleted_count > 0:
        print_and_flush(f"✅ 共删除了 {deleted_count} 封邮件")
    if error_count > 0:
        print_and_flush(f"⚠️ 共有 {error_count} 封邮件删除失败")
    if deleted_count == 0 and error_count == 0:
        print_and_flush("🔍 没有需要删除的邮件")

def verify_email_deleted(session: requests.Session, token: str, email_id: int) -> bool:
    """
    验证邮件是否真的被删除
    """
    emails = get_email_list(session, token)
    if not emails:
        # 如果获取邮件列表失败，我们无法验证，返回True假设删除成功
        return True
    
    # 检查邮件是否还在列表中
    for email in emails:
        if email.get("id") == email_id:
            return False  # 邮件仍然存在
    return True  # 邮件已被删除

def delete_email_with_verification(session: requests.Session, token: str, email_id: int) -> bool:
    """
    删除邮件并验证是否成功
    """
    # 检查邮件是否在无法处理缓存中
    if is_in_unprocessable_cache(email_id):
        print_and_flush(f"⏭️ 邮件 {email_id} 在无法处理缓存中，跳过删除")
        return False
    
    # 先尝试删除
    if delete_email(session, token, email_id):
        # 验证是否真的删除
        if verify_email_deleted(session, token, email_id):
            print_and_flush(f"✅ 邮件 {email_id} 已确认删除成功")
            # 从无法处理缓存中移除（如果存在）
            if email_id in unprocessable_emails_cache:
                unprocessable_emails_cache.discard(email_id)
                save_cache_to_file()  # 保存到文件
            return True
        else:
            print_and_flush(f"⚠️ 邮件 {email_id} 删除接口返回成功，但邮件仍存在")
            # 添加到无法处理缓存
            add_to_unprocessable_cache(email_id)
            return False
    else:
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
        return False

def delete_expired_email_with_verification(session: requests.Session, token: str, email_id: int) -> bool:
    """
    删除过期邮件并验证是否成功
    """
    # 检查邮件是否在无法处理缓存中
    if is_in_unprocessable_cache(email_id):
        print_and_flush(f"⏭️ 邮件 {email_id} 在无法处理缓存中，跳过删除")
        return False
    
    # 先尝试删除
    if delete_expired_email(session, token, email_id):
        # 验证是否真的删除
        if verify_email_deleted(session, token, email_id):
            print_and_flush(f"✅ 过期邮件 {email_id} 已确认删除成功")
            # 从无法处理缓存中移除（如果存在）
            if email_id in unprocessable_emails_cache:
                unprocessable_emails_cache.discard(email_id)
                save_cache_to_file()  # 保存到文件
            return True
        else:
            print_and_flush(f"⚠️ 过期邮件 {email_id} 删除接口返回成功，但邮件仍存在")
            # 添加到无法处理缓存
            add_to_unprocessable_cache(email_id)
            return False
    else:
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
        return False

def delete_email_all_with_verification(session: requests.Session, token: str, email_id: int) -> bool:
    """
    使用delEmailAll接口删除邮件并验证是否成功
    """
    # 检查邮件是否在无法处理缓存中
    if is_in_unprocessable_cache(email_id):
        print_and_flush(f"⏭️ 邮件 {email_id} 在无法处理缓存中，跳过删除")
        return False
    
    # 先尝试删除
    if delete_email_all(session, token, email_id):
        # 验证是否真的删除
        if verify_email_deleted(session, token, email_id):
            print_and_flush(f"✅ 邮件 {email_id} (delEmailAll) 已确认删除成功")
            # 从无法处理缓存中移除（如果存在）
            if email_id in unprocessable_emails_cache:
                unprocessable_emails_cache.discard(email_id)
                save_cache_to_file()  # 保存到文件
            return True
        else:
            print_and_flush(f"⚠️ 邮件 {email_id} (delEmailAll) 删除接口返回成功，但邮件仍存在")
            # 添加到无法处理缓存
            add_to_unprocessable_cache(email_id)
            return False
    else:
        # 添加到无法处理缓存
        add_to_unprocessable_cache(email_id)
        return False