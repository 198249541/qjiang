# daily_tasks.py
import requests
import json
import time
from typing import List, Dict, Any
import sys
def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

def get_daily_tasks(session: requests.Session, token: str) -> List[Dict[str, Any]]:
    """
    获取日常任务列表
    
    Args:
        session: requests会话对象
        token: 用户认证token
    
    Returns:
        任务列表
    """
    url = "https://q-jiang.myprint.top/api/activity/getRiChangRenWu"
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    
    try:
        response = session.post(url, headers=headers, json={}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 检查响应是否成功
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            
            # 从data字段中提取任务列表
            if isinstance(data.get("data"), list):
                return data.get("data")
            
            print_and_flush(f"❌ 获取日常任务失败: 数据格式不正确")
            return []
        else:
            print_and_flush(f"❌ 获取日常任务失败: {data.get('msg', '未知错误')}")
            return []
            
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
    except json.JSONDecodeError as e:
        print_and_flush(f"⚠️ JSON解析错误: {e}")
    except Exception as e:
        print_and_flush(f"⚠️ 获取日常任务时发生未知错误: {e}")
    
    return []

def format_task_info(task: Dict[str, Any]) -> str:
    """
    格式化任务信息
    
    Args:
        task: 任务字典
    
    Returns:
        格式化后的任务信息字符串
    """
    # 获取任务信息
    name = task.get("name", "未知任务")
    desc = task.get("desc", task.get("content", ""))
    do_num = task.get("doNum", 0)  # 可领取次数
    num = task.get("num", 1)  # 需要完成次数
    receive_num = task.get("receiveNum", 0)  # 已领取次数
    receive_limit_num = task.get("receiveLimitNum", 1)  # 最多可领取次数
    
    # 获取奖励信息
    reward_info = ""
    receive_goods = task.get("receiveGoods", [])
    if receive_goods and isinstance(receive_goods, list):
        reward_items = []
        for goods in receive_goods:
            if isinstance(goods, dict):
                goods_name = goods.get("name", "未知物品")
                goods_num = goods.get("num", 1)
                reward_items.append(f"{goods_name}x{goods_num}")
        if reward_items:
            reward_info = " 奖励: " + ", ".join(reward_items)
    
    # 构建显示文本
    result = f"📋 {name}"
    if desc and desc != name:
        result += f" - {desc}"
    
    # 显示任务进度
    result += f" (可领{do_num}次)"
    
    # 显示领取状态
    if receive_limit_num > 0:
        result += f" [已领取 {receive_num}/{receive_limit_num}次]"
    
    result += reward_info
    
    return result

def claim_task_reward(session: requests.Session, token: str, ma_id: int) -> bool:
    """
    领取任务奖励
    
    Args:
        session: requests会话对象
        token: 用户认证token
        ma_id: 任务ID
    
    Returns:
        是否成功领取奖励
    """
    url = "https://q-jiang.myprint.top/api/activity/receiveRiChangRenWu"
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    payload = {"maId": ma_id}
    
    try:
        response = session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if (str(data.get("code")) == "200" or 
            data.get("success") in [True, 1, "1", "true", "True"]):
            print_and_flush(f"✅ 任务 {ma_id} 奖励领取成功: {data.get('msg', '')}")
            return True
        else:
            print_and_flush(f"❌ 任务 {ma_id} 奖励领取失败: {data.get('msg', '未知错误')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络请求异常: {e}")
    except Exception as e:
        print_and_flush(f"⚠️ 领取任务奖励时发生未知错误: {e}")
    
    return False

def claim_all_available_rewards(session: requests.Session, token: str) -> None:
    """
    领取所有可领取的任务奖励
    
    Args:
        session: requests会话对象
        token: 用户认证token
    """
    print_and_flush("🎁 正在检查可领取的日常任务奖励...")
    tasks = get_daily_tasks(session, token)
    
    if not tasks:
        print_and_flush("⚠️ 暂无日常任务或获取失败")
        return
    
    claimed_count = 0
    for task in tasks:
        try:
            do_num = task.get("doNum", 0)  # 可领取次数
            ma_id = task.get("maId", 0)
            name = task.get("name", "未知任务")
            receive_num = task.get("receiveNum", 0)  # 已领取次数
            receive_limit_num = task.get("receiveLimitNum", 1)  # 最多可领取次数
            
            # 检查是否还可以领取奖励
            # 条件1: 有可领取次数 (do_num > 0)
            # 条件2: 还未达到领取上限 (receive_num < receive_limit_num)
            # 条件3: 任务ID有效
            if do_num > 0 and receive_num < receive_limit_num and ma_id != 0:
                print_and_flush(f"📥 正在领取任务 '{name}' 的奖励...")
                # 计算还能领取的次数，取 do_num 和剩余可领次数的较小值
                remaining_limit = receive_limit_num - receive_num
                actual_claim_times = min(do_num, remaining_limit)
                
                # 根据可领取次数循环领取
                for i in range(actual_claim_times):
                    print_and_flush(f"  -> 第 {i+1} 次领取...")
                    if not claim_task_reward(session, token, ma_id):
                        break  # 领取失败则停止
                    claimed_count += 1
                    # 短暂延迟避免请求过于频繁
                    time.sleep(0.5)
            elif do_num > 0 and receive_num >= receive_limit_num:
                print_and_flush(f"⏭️ 任务 '{name}' 已达到领取上限 ({receive_num}/{receive_limit_num})，跳过领取")
        except Exception as e:
            print_and_flush(f"⚠️ 处理任务 {task.get('name', '未知')} 时出错: {e}")
    
    if claimed_count > 0:
        print_and_flush(f"✅ 共领取了 {claimed_count} 个任务奖励")
    else:
        print_and_flush("🔍 没有可领取的任务奖励")

def display_daily_tasks(session: requests.Session, token: str):
    """
    获取并显示日常任务
    
    Args:
        session: requests会话对象
        token: 用户认证token
    """
    print_and_flush("📅 正在获取日常任务...")
    tasks = get_daily_tasks(session, token)
    
    if not tasks:
        print_and_flush("⚠️ 暂无日常任务或获取失败")
        return
    
    print_and_flush(f"✅ 获取到 {len(tasks)} 个日常任务:")
    for i, task in enumerate(tasks, 1):
        try:
            print_and_flush(f"  {i}. {format_task_info(task)}")
        except Exception as e:
            print_and_flush(f"  {i}. 任务信息解析失败: {e}")

# 使用示例
if __name__ == "__main__":
    # 这里只是一个使用示例，实际使用时需要传入有效的session和token
    print("daily_tasks.py 模块")
    print("提供以下功能:")
    print("- get_daily_tasks(session, token): 获取日常任务列表")
    print("- format_task_info(task): 格式化单个任务信息")
    print("- display_daily_tasks(session, token): 显示所有日常任务")
    print("- claim_task_reward(session, token, ma_id): 领取单个任务奖励")
    print("- claim_all_available_rewards(session, token): 领取所有可领取的任务奖励")