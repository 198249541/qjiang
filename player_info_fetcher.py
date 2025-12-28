# file:刷战功.py
import requests
import json
import time

def login(tel, pwd):
    """
    用户登录获取token
    
    Args:
        tel (str): 手机号码
        pwd (str): 密码
        
    Returns:
        dict: 登录结果，包含token等信息
    """
    url = "https://q-jiang.myprint.top/api/user/login"
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "tel": "tel",  # 替换为实际电话号码
        "pwd": "pwd"       # 替换为实际密码
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"登录请求失败: {e}")
        return None

def fetch_other_player_info(user_id, token=None):
    """
    获取其他玩家信息用于刷战功功能
    
    Args:
        user_id (int): 用户ID
        token (str, optional): 登录token
        
    Returns:
        dict: API响应结果
    """
    url = "https://q-jiang.myprint.top/api/bas-assets/otherPlayerInfo"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
    }
    
    # 添加认证信息
    if token:
        headers['token'] = token  # 注意这里使用的是token而不是Authorization
        # headers['Authorization'] = f'Bearer {token}'
        
    payload = {
        "userId": user_id
    }
    
    try:
        # print(f"发送请求到: {url}")
        # print(f"请求参数: {payload}")
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        # print(f"响应状态码: {response.status_code}")
        # print(f"响应内容长度: {len(response.text)} 字符")
        
        # 检查状态码
        if response.status_code != 200:
            print(f"服务器返回错误状态码: {response.status_code}")
            return None
        
        # 检查响应内容是否为空
        if not response.text.strip():
            print("服务器返回空响应")
            return {"success": False, "msg": "服务器返回空响应"}
        
        # 尝试解析JSON
        try:
            result = response.json()
            # print(f"成功解析JSON响应")
            return result
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            # print(f"响应内容: {response.text}")
            return {"success": False, "msg": "响应不是有效的JSON格式"}
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

def fetch_general_list(token=None):
    """
    获取武将列表
    """
    url = "https://q-jiang.myprint.top/api/bas-generals/freeGeneralList"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
    }
    
    if token:
        headers['token'] = token
    
    try:
        # 使用 POST 方法而不是 GET 方法
        response = requests.post(url, headers=headers, data=json.dumps({}))
        print(f"获取武将列表: {url}")
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容长度: {len(response.text)} 字符")
        
        if response.status_code != 200:
            print(f"服务器返回错误状态码: {response.status_code}")
            return None
            
        if not response.text.strip():
            print("服务器返回空响应")
            return {"success": False, "msg": "服务器返回空响应"}
            
        # 尝试解析JSON
        try:
            result = response.json()
            print(f"成功解析武将列表JSON响应")
            return result
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"响应内容: {response.text}")
            return {"success": False, "msg": "响应不是有效的JSON格式"}
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
def occupy_city(mug_id, user_id, token=None):
    """
    攻打城市接口
    """
    url = "https://q-jiang.myprint.top/api/bas-assets/occupyCityer"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
    }
    
    if token:
        headers['token'] = token
        
    payload = {
        "mugId": mug_id,
        "userId": user_id
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        # 调试输出，确认战功值位置
        # print(f"完整响应: {json.dumps(result, ensure_ascii=False)[:200]}...")
        return result
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
def retreat_from_city(user_id, token=None):
    """
    从城市撤离接口
    """
    url = "https://q-jiang.myprint.top/api/bas-assets/retreatOtherDefenCityer"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
    }
    
    if token:
        headers['token'] = token
        
    payload = {
        "userId": user_id
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
def display_generals(generals):
    """
    显示武将列表信息
    
    Args:
        generals (list): 武将列表
    """
    print(f"\n共有 {len(generals)} 名武将:")
    
    for i, general in enumerate(generals):
        print(f"{i+1}. {general.get('name', '未知')} - {general.get('typeFormat', '未知类型')} "
              f"(星级: {general.get('star', '未知')}, 等级: {general.get('rank', '未知')}, "
              f"ID: {general.get('mugId', '未知')})")

def select_general(generals):
    """
    选择武将
    
    Args:
        generals (list): 武将列表
        
    Returns:
        dict: 选中的武将信息
    """
    if not generals:
        return None
        
    while True:
        try:
            choice = int(input(f"请选择武将 (1-{len(generals)}): ")) - 1
            if 0 <= choice < len(generals):
                return generals[choice]
            else:
                print("选择无效，请重新输入")
        except ValueError:
            print("请输入有效的数字")

def auto_battle_loop(target_user_id, general, rounds, token=None):
    """
    自动刷战功循环
    
    Args:
        target_user_id (int): 目标用户ID
        general (dict): 选中的武将
        rounds (int): 执行次数
        token (str, optional): 登录token
    """
    mug_id = general.get('mugId')
    general_name = general.get('name')
    
    print(f"\n开始自动刷战功循环")
    print(f"目标用户ID: {target_user_id}")
    print(f"使用武将: {general_name} (ID: {mug_id})")
    print(f"执行次数: {rounds}")
    print("-" * 40)
    
    success_count = 0
    total_battle_achievement = 0  # 记录总战功
    
    for i in range(rounds):
        print(f"\n第 {i+1}/{rounds} 轮:")
        
        # 第一步：攻打城市
        print("1. 发送攻打请求...")
        occupy_result = occupy_city(mug_id, target_user_id, token)
        
        if not occupy_result:
            print("   攻打请求发送失败，跳过本轮")
            continue
            
        if not occupy_result.get("success"):
            print(f"   攻打失败: {occupy_result.get('msg')}")
            continue
            
        # 显示获得的战功 - 从正确的路径提取
        battle_achievement = occupy_result.get("data", {}).get("battleResult", {}).get("battleAchievement", 0)
        # 如果上面的路径没有找到，尝试备用路径
        if battle_achievement == 0:
            battle_achievement = occupy_result.get("data", {}).get("battleAchievement", 0)
            
        print(f"   攻打成功，获得战功: {battle_achievement}")
        total_battle_achievement += battle_achievement
        
        # 等待一段时间再撤离（模拟真实操作）
        print("2. 等待5分钟后撤离...")
        time.sleep(310)
        
        # 第二步：撤离城市
        print("3. 发送撤离请求...")
        retreat_result = retreat_from_city(target_user_id, token)
        
        if not retreat_result:
            print("   撤离请求发送失败")
            continue
            
        if not retreat_result.get("success"):
            print(f"   撤离失败: {retreat_result.get('msg')}")
            continue
            
        print("   撤离成功")
        success_count += 1
        
        # 每轮之间等待一段时间
        if i < rounds - 1:  # 最后一轮不需要等待
            print(f"4. 等待1秒后进行下一轮... (当前总战功: {total_battle_achievement})")
            time.sleep(0.5)
    
    print("-" * 40)
    print(f"循环完成! 成功执行 {success_count}/{rounds} 轮")
    print(f"总计获得战功: {total_battle_achievement}")
    if rounds > 0:
        print(f"平均每轮战功: {total_battle_achievement/rounds:.2f}")
def main():
    """
    主函数 - 执行刷战功逻辑
    """
    token = None  # 保存登录token
    
    while True:
        print("\n请选择功能:")
        print("1. 用户登录")
        if token:
            print("2. 查询玩家信息")
            print("3. 获取武将列表")
            print("4. 自动刷战功循环")
            print("5. 退出")
        else:
            print("2. 查询玩家信息 (需先登录)")
            print("3. 获取武将列表 (需先登录)")
            print("4. 自动刷战功循环 (需先登录)")
            print("5. 退出")
        
        choice = input("请输入选项 (1/2/3/4/5): ")
        
        if choice == "1":
            # 用户登录
            tel = input("请输入手机号: ")
            pwd = input("请输入密码: ")
            
            print("正在登录...")
            login_result = login(tel, pwd)
            
            if login_result and login_result.get("success"):
                token = login_result.get("data", {}).get("token")
                if token:
                    print("登录成功!")
                    print(f"Token: {token[:20]}...")  # 只显示前20位
                else:
                    print("登录失败: 未获取到token")
            else:
                print(f"登录失败: {login_result.get('msg') if login_result else '未知错误'}")
                
        elif choice == "2":
            # 查询玩家信息
            if not token:
                print("请先登录!")
                continue
                
            user_id = input("请输入要查询的用户ID: ")
            
            if not user_id.isdigit():
                print("用户ID必须是数字")
                continue
            
            user_id = int(user_id)
            
            # 获取玩家信息
            player_info = fetch_other_player_info(user_id, token)
            
            if player_info:
                print("获取玩家信息成功:")
                print(json.dumps(player_info, indent=2, ensure_ascii=False))
            else:
                print("获取玩家信息失败")
                
        elif choice == "3":
            # 获取武将列表
            if not token:
                print("请先登录!")
                continue
                
            general_list = fetch_general_list(token)
            
            if general_list and general_list.get("success"):
                print("获取武将列表成功:")
                generals = general_list.get("data", [])
                
                # 显示详细信息
                display_generals(generals)
                
                # 询问是否显示详细JSON
                show_detail = input("\n是否显示详细JSON信息? (y/n): ")
                if show_detail.lower() == 'y':
                    print(json.dumps(general_list, indent=2, ensure_ascii=False))
            else:
                print("获取武将列表失败")
                
        elif choice == "4":
            # 自动刷战功循环
            if not token:
                print("请先登录!")
                continue
                
            try:
                # 获取目标用户ID
                target_user_id = int(input("请输入目标用户ID: "))
                
                # 获取武将列表
                general_list = fetch_general_list(token)
                if not general_list or not general_list.get("success"):
                    print("无法获取武将列表")
                    continue
                    
                generals = general_list.get("data", [])
                if not generals:
                    print("没有可用的武将")
                    continue
                    
                # 显示武将列表并选择
                print("\n可用武将:")
                display_generals(generals)
                selected_general = select_general(generals)
                
                if not selected_general:
                    print("未选择武将")
                    continue
                
                # 获取执行次数
                rounds = int(input("请输入执行次数: "))
                if rounds <= 0:
                    print("执行次数必须大于0")
                    continue
                
                # 确认开始
                print(f"\n确认信息:")
                print(f"目标用户ID: {target_user_id}")
                print(f"武将: {selected_general.get('name')}")
                print(f"执行次数: {rounds}")
                
                confirm = input("确认开始自动刷战功? (y/n): ")
                if confirm.lower() != 'y':
                    print("操作已取消")
                    continue
                
                # 开始自动循环
                auto_battle_loop(target_user_id, selected_general, rounds, token)
                
            except ValueError:
                print("输入无效，请输入正确的数字")
            except Exception as e:
                print(f"发生错误: {e}")
                
        elif choice == "5":
            print("退出程序")
            break
            
        else:
            print("无效选项，请重新输入")

if __name__ == "__main__":
    main()