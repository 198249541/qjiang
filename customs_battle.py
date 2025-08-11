import json
import requests
import time
import sys
# 难度映射表
DIFFICULTY_MAP = {
    0: "普通",
    1: "英雄",
    2: "烈焰",
    3: "地狱"
}

# 关卡名称映射
LEVEL_NAMES = {
    1: "阳谷县",
    2: "快活林",
    3: "鸳鸯楼",
    4: "清风寨",
    5: "江州城",
    6: "祝家庄",
    7: "大名府",
    8: "汴梁城"
}
def request_input(prompt, timeout=30000):
    """发送输入请求给前端，并等待回填"""
    print(f"[INPUT_REQUEST]{json.dumps({'prompt': prompt, 'timeout': timeout, 'callback': str(time.time())}, ensure_ascii=False)}")
    sys.stdout.flush()
    return input().strip()
def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()
def check_response_success(response_data):
    """检查API响应是否成功"""
    if not isinstance(response_data, dict):
        return False
    return (response_data.get("success") is True and 
            str(response_data.get("code")) == "200")

def extract_uuid_from_reward(response_data):
    """从响应数据中提取UUID"""
    try:
        if isinstance(response_data, dict):
            data = response_data.get("data")
            if isinstance(data, dict):
                battle_result = data.get("battleResult")
                if isinstance(battle_result, dict):
                    reward = battle_result.get("reward")
                    if isinstance(reward, dict):
                        return reward.get("uuid")
    except Exception:
        pass
    return None

def luck_draw_later(uuid_value, bcId, token):
    """邮件抽奖功能"""
    if not uuid_value:
        print_and_flush("📧 无有效UUID，跳过邮件抽奖")
        return False

    url = "https://q-jiang.myprint.top/api/bas-checkpoint/luckDrawLater"
    headers = {"Token": token}
    data = {"uuid": uuid_value, "bcId": bcId}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if check_response_success(result):
                print_and_flush("✅ 邮件抽奖成功，奖励已存入邮件")
                return True
            else:
                print_and_flush(f"❌ 邮件抽奖失败: {result.get('msg', '未知错误')}")
    except Exception as e:
        print_and_flush(f"❌ 邮件抽奖异常: {e}")
    return False

def customs_battle(session, token, user_id):
    print_and_flush("选择难度：0=普通 1=英雄 2=烈焰 3=地狱")
    diff = int(request_input("请输入难度编号："))

    print_and_flush("选择关卡：")
    for k, v in LEVEL_NAMES.items():
        print_and_flush(f"{k} - {v}")
    level = int(request_input("请输入关卡编号(1-8)："))

    bcId = diff * 8 + level
    total_times = int(request_input("请输入挑战次数："))

    print_and_flush(f"\n📝 战斗参数：难度={DIFFICULTY_MAP.get(diff, '未知')} 关卡={LEVEL_NAMES.get(level, '未知')} 次数={total_times}")
    print_and_flush("-" * 50)

    for t in range(1, total_times + 1):
        print_and_flush(f"🚀 第 {t}/{total_times} 次挑战开始")
        common_headers = {"Token": token}

        # 请求1：进入关卡第一步
        try:
            start_response = requests.post(
                "https://q-jiang.myprint.top/api/bas-checkpoint/startCustoms",
                json={"bcId": bcId},
                headers=common_headers,
                timeout=10
            )
            if not check_response_success(start_response.json()):
                print_and_flush("❌ 进入关卡第一步失败，结束挑战")
                break
        except Exception as e:
            print_and_flush(f"❌ 请求1异常: {e}")
            break

        # 请求2：进入关卡第二步
        try:
            defender_response = requests.post(
                "https://q-jiang.myprint.top/api/bas-checkpoint/checkpointDefender",
                json={"bcId": bcId},
                headers=common_headers,
                timeout=10
            )
            if not check_response_success(defender_response.json()):
                print_and_flush("❌ 进入关卡第二步失败，结束挑战")
                break
        except Exception as e:
            print_and_flush(f"❌ 请求2异常: {e}")
            break

        # 四小节战斗
        battle_failed = False
        fourth_battle_result = None

        for sec in range(4):
            enemyId = -(1000 + (bcId - 1) * 4 + sec)
            try:
                stage_response = requests.post(
                    "https://q-jiang.myprint.top/api/battle/customs",
                    json={"bcId": bcId, "enemyId": enemyId},
                    headers=common_headers,
                    timeout=10
                )
                result = stage_response.json()
                if not check_response_success(result):
                    print_and_flush(f"❌ 第{sec+1}小节战斗失败，本轮结束")
                    battle_failed = True
                    break
                else:
                    print_and_flush(f"✅ 第{sec+1}小节胜利")
                    if sec == 3:
                        fourth_battle_result = result
            except Exception as e:
                print_and_flush(f"❌ 第{sec+1}小节异常: {e}")
                battle_failed = True
                break
            time.sleep(0.1)  # 加快间隔

        if battle_failed:
            break  # 本轮失败直接结束整个挑战

        # 检查第四节 UUID
        uuid_value = extract_uuid_from_reward(fourth_battle_result) if fourth_battle_result else None
        if not uuid_value:
            print_and_flush("⚠️ 未找到抽奖UUID，尝试重打一遍第四小节")
            # 重打一遍第四节
            enemyId = -(1000 + (bcId - 1) * 4 + 3)
            try:
                retry_response = requests.post(
                    "https://q-jiang.myprint.top/api/battle/customs",
                    json={"bcId": bcId, "enemyId": enemyId},
                    headers=common_headers,
                    timeout=10
                )
                retry_result = retry_response.json()
                if check_response_success(retry_result):
                    print_and_flush("✅ 重打第四小节胜利")
                    uuid_value = extract_uuid_from_reward(retry_result)
            except Exception as e:
                print_and_flush(f"❌ 重打第四小节异常: {e}")

        if uuid_value:
            luck_draw_later(uuid_value, bcId, token)
        else:
            print_and_flush("❌ 两次第四小节都未拿到UUID，结束挑战")
            break

    print_and_flush("🎉 挑战流程结束！")
