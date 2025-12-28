# arena.py
import requests
import sys

def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

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
        response = session.post(url, headers=headers, json={})
        response.raise_for_status()

        result = response.json()

        if result.get("success") and result.get("code") == "200":
            data = result["data"]
            user_info = data.get("userInfo", {})
            return user_info
        else:
            return None

    except Exception as e:
        return None

def get_arena_rank_list(session, token):
    """
    获取擂台排行榜信息
    """
    # 先获取用户自己的信息，以确定自己的用户ID
    user_info = get_user_info(session, token)
    if not user_info:
        print_and_flush("❌ 无法获取用户信息")
        return None
        
    my_user_id = user_info.get("userId", 0)
    
    url = "https://q-jiang.myprint.top/api/bas-assets/arenaRankList"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }
    data = {}  # 根据需要可以添加请求参数

    try:
        print_and_flush("🔍 正在获取擂台排行榜...")
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()

        if result.get("success") and result.get("code") == "200":
            # 修复数据结构问题 - 根据实际返回的数据结构调整
            if isinstance(result["data"], list):
                rank_list = result["data"]
            else:
                rank_list = result["data"].get("rankList", [])
            
            print_and_flush("✅ 擂台排行榜获取成功！")
            print_and_flush("=" * 50)
            print_and_flush("🏆 当前排名")
            print_and_flush("=" * 50)
            
            # 显示排行榜前10名
            for i, user in enumerate(rank_list[:10]):
                rank = user.get("arenaRank", "未知")
                username = user.get("userName", "未知")
                combat_power = user.get("combatPower", 0)
                battle_achievement = user.get("battleAchievement", 0)
                integral = user.get("integral", 0)  # 积分
                user_id = user.get("userId", 0)
                
                # 标记自己
                self_mark = " (我)" if user_id == my_user_id else ""
                
                print_and_flush(f"{i+1:2d}. {username}{self_mark}")
                print_and_flush(f"    排名: {rank} | 战力: {combat_power} | 功勋: {battle_achievement} | 积分: {integral}")
            
            print_and_flush("=" * 50)
            return rank_list

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 获取擂台排行榜失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求擂台排行榜失败: {e}")
        return None

def get_arena_info(session, token):
    """
    获取用户擂台信息
    """
    url = "https://q-jiang.myprint.top/api/bas-assets/arenaInfo"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }

    try:
        print_and_flush("🔍 正在获取擂台信息...")
        response = session.post(url, headers=headers, json={})
        response.raise_for_status()

        result = response.json()

        if result.get("success") and result.get("code") == "200":
            data = result["data"]
            user_arena = data.get("userArena", {})
            
            print_and_flush("✅ 擂台信息获取成功！")
            print_and_flush("=" * 40)
            
            arena_rank = user_arena.get("arenaRank", "未知")
            max_arena_num = user_arena.get("maxArenaNum", 0)
            current_arena_num = user_arena.get("currentArenaNum", 0)
            integral = user_arena.get("integral", 0)  # 用户积分
            
            print_and_flush(f"当前排名: {arena_rank}")
            print_and_flush(f"挑战次数: {current_arena_num}/{max_arena_num}")
            print_and_flush(f"当前积分: {integral}")
            
            print_and_flush("=" * 40)
            return data

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 获取擂台信息失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求擂台信息失败: {e}")
        return None

def get_arena_award_list(session, token):
    """
    获取擂台积分可兑换物品列表
    """
    url = "https://q-jiang.myprint.top/api/bas-assets/arenaAwardList"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }

    try:
        print_and_flush("🔍 正在获取积分兑换物品列表...")
        response = session.post(url, headers=headers, json={})
        response.raise_for_status()

        result = response.json()

        if result.get("success") and result.get("code") == "200":
            award_list = result["data"]
            
            print_and_flush("✅ 积分兑换物品列表获取成功！")
            print_and_flush("=" * 50)
            print_and_flush("🎁 积分兑换物品列表")
            print_and_flush("=" * 50)
            
            # 显示可兑换物品
            for i, item in enumerate(award_list):
                name = item.get("name", "未知物品")
                need_integral = item.get("needIntegral", 0)
                deposit_num = item.get("depositNum", 0)
                desc = item.get("desc", "无描述")
                buy_is = item.get("buyIs", 0)  # 是否可购买
                
                status = "✅ 可兑换" if buy_is == 1 else "❌ 不可兑换"
                
                print_and_flush(f"{i+1:2d}. {name}")
                print_and_flush(f"    所需积分: {need_integral} | 库存: {deposit_num} | 状态: {status}")
                print_and_flush(f"    描述: {desc}")
                print_and_flush("-" * 30)
            
            print_and_flush("=" * 50)
            return award_list

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 获取积分兑换物品列表失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求积分兑换物品列表失败: {e}")
        return None

def exchange_arena_goods(session, token, goods_id, num=1):
    """
    兑换擂台积分物品
    :param session: requests session
    :param token: 用户token
    :param goods_id: 物品ID
    :param num: 兑换数量，默认为1
    """
    url = "https://q-jiang.myprint.top/api/bas-assets/exchangeArenaGoods"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }
    data = {"goodsId": goods_id, "num": num}

    try:
        print_and_flush(f"🔄 正在兑换物品 ID: {goods_id} (数量: {num})...")
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        if result.get("success") and result.get("code") == "200":
            # 显示兑换后的剩余积分
            user_info = result.get("data", {}).get("userInfo", {})
            remaining_integral = user_info.get("integral", 0)
            goods_list = result.get("data", {}).get("goodsList", {})
            goods_name = goods_list.get("name", "未知物品")
            
            print_and_flush(f"✅ {goods_name}兑换成功！")
            print_and_flush(f"💰 剩余积分: {remaining_integral}")
            return True
        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 物品兑换失败: {msg}")
            return False

    except Exception as e:
        print_and_flush(f"❌ 发送物品兑换请求失败: {e}")
        return False

def auto_exchange_arena_goods(session, token, target_item=None):
    """
    自动兑换擂台积分物品
    :param session: requests session
    :param token: 用户token
    :param target_item: 目标兑换物品信息，格式: {"id": 物品ID, "name": 物品名称, "points": 所需积分}
    """
    total_exchanged = 0  # 记录总兑换次数
    exchanged_items = {}  # 记录各物品兑换数量
    
    # 获取初始积分
    user_info = get_user_info(session, token)
    if not user_info:
        print_and_flush("❌ 无法获取用户信息")
        return False
    
    initial_integral = 0
    rank_list_response = None
    url = "https://q-jiang.myprint.top/api/bas-assets/arenaRankList"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }
    
    try:
        response = session.post(url, headers=headers, json={})
        response.raise_for_status()
        rank_list_response = response.json()
    except Exception as e:
        print_and_flush(f"❌ 获取排行榜信息失败: {e}")
        return False
    
    if rank_list_response and rank_list_response.get("success") and rank_list_response.get("code") == "200":
        my_user_id = user_info.get("userId", 0)
        rank_list = rank_list_response["data"] if isinstance(rank_list_response["data"], list) else rank_list_response["data"].get("rankList", [])
        
        # 查找自己的积分信息
        for user in rank_list:
            if user.get("userId") == my_user_id:
                initial_integral = user.get("integral", 0)
                break
    
    print_and_flush(f"💰 初始积分: {initial_integral}")
    
    # 获取可兑换物品列表
    award_list = get_arena_award_list(session, token)
    if not award_list:
        print_and_flush("❌ 无法获取可兑换物品列表")
        return False
    
    exchange_count = 0  # 兑换轮次计数
    
    while True:  # 循环兑换直到积分不足
        # 获取用户当前积分
        user_info = get_user_info(session, token)
        if not user_info:
            print_and_flush("❌ 无法获取用户信息")
            return False
        
        current_integral = 0
        if rank_list_response and rank_list_response.get("success") and rank_list_response.get("code") == "200":
            my_user_id = user_info.get("userId", 0)
            rank_list = rank_list_response["data"] if isinstance(rank_list_response["data"], list) else rank_list_response["data"].get("rankList", [])
            
            # 查找自己的积分信息
            for user in rank_list:
                if user.get("userId") == my_user_id:
                    current_integral = user.get("integral", 0)
                    break
        
        # 如果指定了目标物品，则只兑换该物品
        if target_item:
            item_id = target_item["id"]
            item_name = target_item["name"]
            item_points = target_item["points"]
            
            # 查找目标物品
            target_award = None
            for item in award_list:
                if item.get("id") == item_id:
                    target_award = item
                    break
            
            if not target_award:
                print_and_flush(f"❌ 未找到目标物品: {item_name}")
                return False
                
            # 检查是否可兑换
            buy_is = target_award.get("buyIs", 0)
            deposit_num = target_award.get("depositNum", 0)
            need_integral = target_award.get("needIntegral", 0)
            
            if buy_is != 1:
                print_and_flush(f"❌ {item_name}当前不可兑换")
                return False
                
            if deposit_num <= 0:
                print_and_flush(f"❌ {item_name}库存不足")
                return False
                
            if current_integral < need_integral:
                print_and_flush(f"❌ 积分不足，需要 {need_integral} 积分，当前 {current_integral} 积分")
                return False
                
            # 计算可兑换数量
            max_exchange = min(current_integral // need_integral, deposit_num)
            if max_exchange <= 0:
                print_and_flush(f"❌ 积分不足兑换 {item_name}")
                return False
                
            # 执行兑换
            if exchange_arena_goods(session, token, item_id, max_exchange):
                total_exchanged += 1
                exchanged_items[item_name] = exchanged_items.get(item_name, 0) + max_exchange
                continue  # 兑换成功后继续下一轮兑换
            else:
                return False
        
        # 如果未指定目标物品，则按优先级自动兑换
        else:
            # 从配置文件获取兑换优先级
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                priority_list = config.get("arena_exchange_priority", [
                    {"id": 56, "name": "蓝武魂", "points": 1500}
                ])
            except Exception:
                # 如果配置文件不存在或格式错误，使用默认值
                priority_list = [
                    {"id": 56, "name": "蓝武魂", "points": 1500}
                ]
            
            # 每轮只兑换一种物品
            exchanged = False
            item_id = priority_list[exchange_count % len(priority_list)]["id"]
            item_name = priority_list[exchange_count % len(priority_list)]["name"]
            item_points = priority_list[exchange_count % len(priority_list)]["points"]
            
            # 查找物品
            target_award = None
            for item in award_list:
                if item.get("id") == item_id:
                    target_award = item
                    break
            
            if target_award:
                # 检查是否可兑换
                buy_is = target_award.get("buyIs", 0)
                deposit_num = target_award.get("depositNum", 0)
                need_integral = target_award.get("needIntegral", 0)
                
                if buy_is == 1 and deposit_num > 0 and current_integral >= need_integral:
                    # 计算可兑换数量
                    max_exchange = min(current_integral // need_integral, deposit_num)
                    if max_exchange > 0:
                        # 显示进度信息
                        progress = f"🔄 第{exchange_count + 1}轮兑换: {item_name} x{max_exchange} "
                        progress += f"| 积分: {current_integral} → {current_integral - need_integral * max_exchange}"
                        print_and_flush(progress)
                        
                        # 执行兑换
                        if exchange_arena_goods(session, token, item_id, max_exchange):
                            total_exchanged += 1
                            exchanged_items[item_name] = exchanged_items.get(item_name, 0) + max_exchange
                            exchanged = True
            
            exchange_count += 1
            
            # 如果本轮没有兑换任何物品，说明积分不足以兑换任何物品
            if not exchanged:
                # 汇总输出兑换结果
                if total_exchanged > 0:
                    print_and_flush(f"✅ 兑换完成！共兑换 {total_exchanged} 批物品:")
                    for item_name, count in exchanged_items.items():
                        print_and_flush(f"    {item_name}: {count} 个")
                    print_and_flush(f"💰 积分变化: {initial_integral} → {current_integral} (消耗: {initial_integral - current_integral})")
                else:
                    print_and_flush("ℹ️ 没有可兑换的物品")
                return True  # 所有物品都无法兑换时结束