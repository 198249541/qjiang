# email_manager.py
import requests
import json
import time
from typing import List, Dict, Any
from datetime import datetime
from collections import OrderedDict
import sys

def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

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
    attachment_status = "📎" if goods_list or email_type == 40 else ""
    receive_status = "已领" if receive_is == 1 else "未领"
    result = f"{attachment_status}[{receive_status}][类型{email_type}] {title}"
    if goods_list and isinstance(goods_list, list):
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
    
    # 只显示未领取附件的邮件，并过滤掉类型为40的邮件
    unclaimed_emails = [email for email in emails 
                       if email.get("receiveIs", 0) == 0 and 
                       not is_email_expired(email.get("invalidDay", "")) and
                       email.get("type", 0) != 40]  # 过滤掉类型为40的邮件
    
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
    url = "https://q-jiang.myprint.top/api/user-email/delEmail"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"id": email_id}
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            print_and_flush(f"✅ 邮件 {email_id} 删除成功")
            return True
        else:
            print_and_flush(f"❌ 删除邮件 {email_id} 失败: {data.get('msg', '未知错误')}")
            return False
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
    except Exception as e:
        print_and_flush(f"⚠️ 删除邮件时发生未知错误: {e}")
    return False

def delete_expired_email(session: requests.Session, token: str, email_id: int) -> bool:
    """
    删除过期邮件
    使用专门的删除过期邮件接口
    """
    url = "https://q-jiang.myprint.top/api/user-email/delEmail"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"id": email_id}
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            print_and_flush(f"✅ 过期邮件 {email_id} 删除成功")
            return True
        else:
            print_and_flush(f"❌ 删除过期邮件 {email_id} 失败: {data.get('msg', '未知错误')}")
            return False
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
    except Exception as e:
        print_and_flush(f"⚠️ 删除过期邮件时发生未知错误: {e}")
    return False

def delete_email_all(session: requests.Session, token: str, email_id: int) -> bool:
    """
    使用 delEmailAll 接口删除邮件
    专门用于删除类型为50的邮件
    """
    url = "https://q-jiang.myprint.top/api/user-email/delEmailAll"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"id": email_id}
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            print_and_flush(f"✅ 邮件 {email_id} 删除成功 (使用delEmailAll接口)")
            return True
        else:
            print_and_flush(f"❌ 删除邮件 {email_id} 失败: {data.get('msg', '未知错误')} (使用delEmailAll接口)")
            return False
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e} (使用delEmailAll接口)")
    except Exception as e:
        print_and_flush(f"⚠️ 删除邮件时发生未知错误: {e} (使用delEmailAll接口)")
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
    领取类型为50的邮件附件
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

def process_all_customs_emails(session: requests.Session, token: str) -> None:
    print_and_flush("🔍 类型为40的关卡邮件已被过滤，不进行处理")
    return

def get_all_attachments(session: requests.Session, token: str) -> None:
    print_and_flush("📎 正在检查可领取的邮件附件...")
    emails = get_email_list(session, token)
    if not emails:
        print_and_flush("⚠️ 暂无邮件或获取失败")
        return
    claimed_count = 0
    skipped_count = 0
    for email in emails:
        try:
            email_id = email.get("id", 0)
            receive_is = email.get("receiveIs", 0)
            title = email.get("title", "无标题")
            goods_list = email.get("goodsListVo", [])
            email_type = email.get("type", 0)
            invalid_day = email.get("invalidDay", "")
            # 只处理未领取的普通邮件，并排除类型为40的邮件
            if email_type != 40 and goods_list and receive_is == 0 and email_id:
                if is_email_expired(invalid_day):
                    skipped_count += 1
                    continue
                print_and_flush(f"📥 正在领取邮件 '{title}' 的附件...")
                # 根据邮件类型选择合适的接口
                if email_type == 50:
                    # 类型为50的邮件使用 receiveEmail 接口
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
        print_and_flush(f"✅ 共领取了 {claimed_count} 个邮件附件")
    if skipped_count > 0:
        print_and_flush(f"⏭️ 共跳过了 {skipped_count} 个已过期的邮件")
    if claimed_count == 0 and skipped_count == 0:
        print_and_flush("🔍 没有可领取的普通邮件附件")

def delete_all_claimed_emails(session: requests.Session, token: str) -> None:
    """
    自动删除所有已领取附件的邮件（无论是否过期）
    包括类型为50的已领取邮件
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
                # 类型为50的邮件优先使用 delEmailAll 接口
                success = False
                if email_type == 50:
                    if delete_email_all(session, token, email_id):
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
                if email_type == 50:
                    # 类型为50的邮件优先使用 delEmailAll 接口
                    if delete_email_all(session, token, email_id):
                        deleted_count += 1
                        success = True
                    # 如果 delEmailAll 接口失败，再尝试其他接口
                    elif delete_expired_email(session, token, email_id):
                        deleted_count += 1
                        success = True
                    elif delete_email(session, token, email_id):
                        deleted_count += 1
                        success = True
                else:
                    # 对于过期邮件优先使用专门的删除接口
                    if is_email_expired(invalid_day):
                        if delete_expired_email(session, token, email_id):
                            deleted_count += 1
                            success = True
                        elif delete_email(session, token, email_id):
                            deleted_count += 1
                            success = True
                    else:
                        if delete_email(session, token, email_id):
                            deleted_count += 1
                            success = True
                
                # 如果所有接口都失败
                if not success:
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