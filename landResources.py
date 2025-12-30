# landResources.py
# 功能：获取并显示领地资源列表（一行一条，简洁格式）
import sys
import datetime
import time
import json 

def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

def get_re_list(session, token):
    """
    获取用户领地资源列表（简洁单行输出）
    :param session: requests.Session() 对象
    :param token: 登录 token
    :return: resourceList 列表 或 None
    """
    url = "https://q-jiang.myprint.top/api/mid-user-resource/reList"
    headers = {
        "Token": token,
    }

    try:
        print_and_flush("🌍 正在获取【领地资源】信息...")  # 主提示放这里，不重复
        response = session.post(url, headers=headers, json={})
        response.raise_for_status()

        result = response.json()
        if result.get("success") and result.get("code") == "200":
            resource_list = result["data"].get("resourceList", [])

            for res in resource_list:
                name = res.get("name", "未知资源")
                level = res.get("murRank", 0)

                general_desc = res.get("generalDesc")
                if general_desc:
                    player = general_desc.get("occupyUserName", "未知玩家")
                    general = general_desc.get("generalName", "无名武将")
                    print_and_flush(f"  🌲 {name} Lv.{level} 🔒 被『{player}』占领，武将：{general}")
                else:
                    print_and_flush(f"  🌲 {name} Lv.{level} ✅ 空闲")

            return resource_list

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 接口返回失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求领地资源列表异常: {e}")
        return None


def get_occupy_resource_list(session, token):
    """
    获取用户占领的领地资源列表
    :param session: requests.Session() 对象
    :param token: 登录 token
    :return: selfArmyInfo 列表 或 None
    """
    url = "https://q-jiang.myprint.top/api/battle/armyInfo"
    headers = {
        "Token": token,
    }

    try:
        print_and_flush("⚔️ 正在获取【我占领的领地资源】信息...")
        response = session.post(url, headers=headers, json={})
        response.raise_for_status()

        result = response.json()
        if result.get("success") and result.get("code") == "200":
            # 从新的数据结构中获取 selfArmyInfo
            army_data = result.get("data", {})
            occupy_resource_list = army_data.get("selfArmyInfo", [])

            if not occupy_resource_list:
                print_and_flush("  📭 暂无占领的领地资源")
                return occupy_resource_list

            # 按占领时间排序，最新的在前
            # 修复：处理 None 值和空字符串的情况
            occupy_resource_list.sort(
                key=lambda x: x.get("occupyTime") or "", 
                reverse=True
            )

            for res in occupy_resource_list:
                name = res.get("brName", "未知资源")
                level = res.get("murRank", 0)
                general_name = res.get("mugName", "无名武将")
                occupy_time = res.get("occupyTime", "")
                status_format = res.get("statusFormat", "")
                arrive_time = res.get("arriveTime", "")
                
                # 计算占领时长（仅对非返回/撤退状态显示）
                time_info = ""
                if occupy_time and status_format not in ["返回", "撤退"]:
                    try:
                        occupy_datetime = datetime.datetime.strptime(occupy_time, "%Y-%m-%d %H:%M:%S")
                        now = datetime.datetime.now()
                        duration = now - occupy_datetime
                        
                        days = duration.days
                        hours, remainder = divmod(duration.seconds, 3600)
                        
                        if days > 0:
                            time_info = f" ({days}天{hours}小时)"
                        elif hours > 0:
                            time_info = f" ({hours}小时)"
                        # 0小时不显示
                    except ValueError:
                        # 如果时间格式不正确，就显示原始时间
                        time_info = f" ({occupy_time})"

                # 添加回家剩余时间信息
                arrive_info = ""
                if arrive_time and status_format in ["返回", "撤退"]:
                    try:
                        arrive_datetime = datetime.datetime.strptime(arrive_time, "%Y-%m-%d %H:%M:%S")
                        now = datetime.datetime.now()
                        time_diff = arrive_datetime - now
                        
                        if time_diff.total_seconds() > 0:
                            hours, remainder = divmod(time_diff.seconds, 3600)
                            minutes = remainder // 60
                            if hours > 0:
                                arrive_info = f" (还需: {hours}小时{minutes}分钟)"
                            elif minutes > 0:
                                arrive_info = f" (还需: {minutes}分钟)"
                            else:
                                arrive_info = " (即将到达)"
                        else:
                            arrive_info = " (即将到达)"
                    except ValueError:
                        arrive_info = f" (回家时间: {arrive_time})"

                # 检查是否正在返回或撤退
                if status_format in ["返回", "撤退"]:
                    status_icon = "⏳" if status_format == "返回" else "🚩"
                    # 对于返回/撤退状态，只显示回家剩余时间
                    print_and_flush(f"  ⚔️ {name} Lv.{level} 👤 {general_name} {status_icon} {status_format}{arrive_info}")
                else:
                    print_and_flush(f"  ⚔️ {name} Lv.{level} 👤 {general_name}{time_info}")

            return occupy_resource_list

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 获取占领领地资源失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求占领领地资源列表异常: {e}")
        return None


def resource_recall(session, token, murg_id):
    """
    召回领地资源
    :param session: requests.Session() 对象
    :param token: 登录 token
    :param murg_id: 领地资源ID
    :return: 是否成功召回
    """
    url = "https://q-jiang.myprint.top/api/mid-user-resource/resourceRecall"
    headers = {
        "Token": token,
    }
    data = {
        "murgId": murg_id
    }

    try:
        print_and_flush(f"🔄 正在召回领地资源 ID: {murg_id}...")
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        if result.get("success") and result.get("code") == "200":
            print_and_flush(f"✅ 领地资源 ID: {murg_id} 召回成功")
            return True
        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 召回失败: {msg}")
            return False

    except Exception as e:
        print_and_flush(f"❌ 召回请求异常: {e}")
        return False


def check_and_recall_resources(session, token, occupy_resource_list):
    """
    检查并自动召回超过8小时的领地资源
    :param session: requests.Session() 对象
    :param token: 登录 token
    :param occupy_resource_list: 占领的领地资源列表
    :return: None
    """
    if not occupy_resource_list:
        return

    print_and_flush("🔍 检查是否有超过8小时的领地资源需要召回...")
    now = datetime.datetime.now()
    
    recalled_count = 0
    for res in occupy_resource_list:
        occupy_time = res.get("occupyTime", "")
        murg_id = res.get("murgId")
        status_format = res.get("statusFormat", "")
        
        # 跳过正在返回或撤退的资源
        if status_format in ["返回", "撤退"]:
            continue
        
        if not occupy_time or not murg_id:
            continue
            
        try:
            occupy_datetime = datetime.datetime.strptime(occupy_time, "%Y-%m-%d %H:%M:%S")
            duration = now - occupy_datetime
            
            # 如果超过8小时(28800秒)，则自动召回
            if duration.total_seconds() > 28800:  # 8小时 = 8 * 60 * 60 秒
                print_and_flush(f"⏰ 发现超过8小时的领地资源: {res.get('brName', '未知资源')}")
                if resource_recall(session, token, murg_id):
                    recalled_count += 1
        except ValueError:
            # 时间格式错误，跳过
            continue
    
    if recalled_count > 0:
        print_and_flush(f"✅ 共召回 {recalled_count} 个领地资源")
    else:
        print_and_flush("✅ 没有需要召回的领地资源")


def get_all_land_resources(session, token):
    """
    获取所有领地资源信息（包括资源列表和占领信息）
    :param session: requests.Session() 对象
    :param token: 登录 token
    :return: (resource_list, occupy_resource_list) 或 (None, None)
    """
    print_and_flush("🌍 正在获取【全部领地资源】信息...")
    
    # 获取所有领地资源
    resource_list = get_re_list(session, token)
    
    # 获取占领的领地资源
    occupy_resource_list = get_occupy_resource_list(session, token)
    
    # 检查并召回超过8小时的资源
    check_and_recall_resources(session, token, occupy_resource_list)
    
    return resource_list, occupy_resource_list


def get_friend_land_resources(session, token, user_id):
    """
    获取好友领地资源信息（只显示等级为9的资源）
    :param session: requests.Session() 对象
    :param token: 登录 token
    :param user_id: 好友用户ID
    :return: resourceList 列表 或 None
    """
    url = "https://q-jiang.myprint.top/api/mid-user-resource/reList"
    headers = {
        "Token": token,
    }
    data = {
        "userId": user_id
    }

    try:
        print_and_flush(f"👥 正在获取好友【{user_id}】的领地资源信息...")
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        if result.get("success") and result.get("code") == "200":
            resource_list = result["data"].get("resourceList", [])
            
            # 筛选等级为9的资源，并且只保留农田、森林、草原、山丘、沼泽
            target_resources = ["农田", "森林", "草原", "山丘", "沼泽"]
            level_9_resources = [
                res for res in resource_list 
                if res.get("murRank") == 9 and res.get("name") in target_resources
            ]
            
            if not level_9_resources:
                print_and_flush("  ❗ 好友没有符合条件的领地资源")
                return []

            for res in level_9_resources:
                name = res.get("name", "未知资源")
                level = res.get("murRank", 0)
                status = res.get("status")

                general_desc = res.get("generalDesc")
                if general_desc:
                    player = general_desc.get("occupyUserName", "未知玩家")
                    general = general_desc.get("generalName", "无名武将")
                    print_and_flush(f"  🌲 {name} Lv.{level} 🔒 被『{player}』占领，武将：{general}")
                elif status == 3:
                    print_and_flush(f"  🌲 {name} Lv.{level} ⏳ 正在被占领中")
                else:
                    print_and_flush(f"  🌲 {name} Lv.{level} ✅ 空闲")

            return level_9_resources

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 获取好友领地资源失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求好友领地资源列表异常: {e}")
        return None


def scan_users_for_resources(session, token, start_user_id=1, end_user_id=100):
    """
    扫描用户ID范围，查找空闲的9级农田、森林、草原、山丘、沼泽资源
    :param session: requests.Session() 对象
    :param token: 登录 token
    :param start_user_id: 起始用户ID
    :param end_user_id: 结束用户ID
    :return: 所有找到的空闲资源列表
    """
    print_and_flush(f"🔍 开始扫描用户 {start_user_id} 到 {end_user_id} 的空闲9级资源...")
    
    target_resources = ["农田", "森林", "草原", "山丘", "沼泽"]
    free_resources = []
    
    for user_id in range(start_user_id, end_user_id + 1):
        try:
            url = "https://q-jiang.myprint.top/api/mid-user-resource/reList"
            headers = {"Token": token}
            data = {"userId": user_id}
            
            response = session.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("success") and result.get("code") == "200":
                resource_list = result["data"].get("resourceList", [])
                
                # 筛选等级为9的资源，并且只保留农田、森林、草原、山丘、沼泽
                level_9_resources = [
                    res for res in resource_list 
                    if res.get("murRank") == 9 and res.get("name") in target_resources
                ]
                
                # 查找空闲资源
                for res in level_9_resources:
                    # 检查是否被他人占领
                    general_desc = res.get("generalDesc")
                    is_occupied_by_other = False
                    
                    if general_desc:
                        occupy_user_name = general_desc.get("occupyUserName")
                        # 如果存在占领用户名且不是空字符串，则认为被他人占领
                        if occupy_user_name:
                            is_occupied_by_other = True
                    
                    # 检查是否空闲（没有被他人占领且不是正在被占领状态）
                    if not is_occupied_by_other and not general_desc and res.get("status") != 3:
                        res["userId"] = user_id  # 添加用户ID信息
                        free_resources.append(res)
                        name = res.get("name", "未知资源")
                        print_and_flush(f"  🎯 发现空闲资源: {name} (用户ID: {user_id})")
            
            # 添加延迟避免请求过于频繁
            time.sleep(0.1)
            
        except Exception as e:
            # 忽略单个用户请求失败，继续扫描下一个
            continue
    
    print_and_flush(f"✅ 扫描完成，共找到 {len(free_resources)} 个空闲资源")
    return free_resources


def get_free_generals(session, token):
    """
    获取空闲武将列表
    :param session: requests.Session() 对象
    :param token: 登录 token
    :return: 武将列表 或 None
    """
    url = "https://q-jiang.myprint.top/api/bas-generals/freeGeneralList"
    headers = {
        "Token": token,
    }

    try:
        print_and_flush("👥 正在获取空闲武将列表...")
        response = session.post(url, headers=headers, json={})
        response.raise_for_status()

        result = response.json()
        # print_and_flush(f"  📡 API原始返回: {result}")  # 关闭这行的输出
        
        if result.get("success") and result.get("code") == "200":
            # 修复：正确处理返回的数据结构
            # API返回的data字段本身就是一个武将列表，而不是包含generalList字段的字典
            general_list = result.get("data", [])
            
            # print_and_flush(f"  📋 武将列表: {general_list}")  # 关闭这行的输出
            
            if not general_list:
                print_and_flush("  ❗ 没有空闲武将")
                return []
            
            # 确保列表中的每个元素都是字典类型
            valid_generals = []
            for i, general in enumerate(general_list):
                if isinstance(general, dict):
                    valid_generals.append(general)
                else:
                    print_and_flush(f"  ⚠️  跳过无效的武将数据: {general}")
            
            if not valid_generals:
                print_and_flush("  ❗ 没有有效的空闲武将")
                return []
            
            print_and_flush(f"  ✅ 找到 {len(valid_generals)} 个空闲武将")
            for i, general in enumerate(valid_generals):
                name = general.get("name", "无名武将")  # 注意：字段名是"name"而不是"generalName"
                rank = general.get("rank", 0)
                print_and_flush(f"    {i+1}. {name} (等级: {rank})")
            
            return valid_generals

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 获取空闲武将失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求空闲武将列表异常: {e}")
        return None


def get_resource_detail(session, token, mur_id, user_id):
    """
    获取9级领地详细信息
    :param session: requests.Session() 对象
    :param token: 登录 token
    :param mur_id: 领地ID
    :param user_id: 用户ID
    :return: 领地详细信息 或 None
    """
    url = "https://q-jiang.myprint.top/api/mid-user-resource/resourceDetail"
    headers = {
        "Token": token,
    }
    data = {
        "murId": mur_id,
        "userId": user_id
    }

    try:
        print_and_flush(f"🔍 正在获取领地详细信息 (murId: {mur_id}, userId: {user_id})...")
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        if result.get("success") and result.get("code") == "200":
            detail_data = result["data"]
            
            # 检查防守武将状态，如果正在行军则返回特殊标识
            generals_vo = detail_data.get("generalsVo", {})
            if generals_vo:
                mug_status_format = generals_vo.get("mugStatusFormat", "")
                if mug_status_format == "行军中":
                    print_and_flush(f"  ⚠️ 防守武将正在行军中，跳过该资源点")
                    return "under_attack"  # 返回特殊标识表示有行军
            
            print_and_flush("  ✅ 获取详细信息成功")
            
            # 显示防守武将信息
            if generals_vo:
                general_name = generals_vo.get("name", "未知武将")
                general_rank = generals_vo.get("rank", 0)
                general_type = generals_vo.get("typeFormat", "未知类型")
                print_and_flush(f"  🛡️ 防守武将: {general_name} (Lv.{general_rank}, {general_type})")
            
            # 显示资源信息
            resource = detail_data.get("resource", {})
            if resource:
                resource_name = resource.get("name", "未知资源")
                resource_type = resource.get("generalsTypeFormat", "未知类型")
                print_and_flush(f"  🌲 资源类型: {resource_name} ({resource_type})")
            
            return detail_data
        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 获取领地详细信息失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求领地详细信息异常: {e}")
        return None
def occupy_resource(session, token, mur_id, general_id):
    """
    占领资源
    :param session: requests.Session() 对象
    :param token: 登录 token
    :param mur_id: 领地ID
    :param general_id: 武将ID
    :return: True(成功) / False(其他失败) / "超出资源占领上限"(特定错误)
    """
    url = "https://q-jiang.myprint.top/api/mid-user-resource/resourceOccupy"
    headers = {
        "Token": token,
    }
    data = {
        "murId": mur_id,
        "mugId": general_id
    }

    try:
        print_and_flush(f"⚔️ 正在尝试占领资源 (murId: {mur_id}, mugId: {general_id})...")
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        if result.get("success") and result.get("code") == "200":
            print_and_flush("  ✅ 资源占领成功")
            return True
        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 资源占领失败: {msg}")
            # 检查是否是"超出资源占领上限"错误
            if "超出资源占领上限" in msg:
                return "超出资源占领上限"
            return False

    except Exception as e:
        print_and_flush(f"❌ 请求资源占领异常: {e}")
        return False


def get_current_occupied_count(session, token):
    """
    获取当前已占领和行军中的资源数量（预占名额）
    :param session: requests.Session() 对象
    :param token: 登录 token
    :return: 已占用的资源数量
    """
    print_and_flush("📊 正在统计当前已占用的领地资源数量...")
    
    # 获取已占领的资源
    occupy_resource_list = get_occupy_resource_list(session, token)
    
    if not occupy_resource_list:
        print_and_flush("  ✅ 当前没有占用任何资源")
        return 0
    
    # 统计占用名额的资源数量
    occupied_count = 0
    for res in occupy_resource_list:
        status_format = res.get("statusFormat", "")
        # "返回"状态表示资源已经释放，不占用名额
        # "正在前往"状态表示预占名额，需要计算在内
        if status_format != "返回":
            occupied_count += 1
    
    print_and_flush(f"  📊 当前已占用资源: {occupied_count} 个")
    return occupied_count


# ... existing code ...
def auto_occupy_resources_gradually(session, token, account_index=None):
    """
    逐个检查并占领资源，减少服务器压力
    增加对"超出资源占领上限"错误的处理
    :param account_index: 账号索引，用于获取对应账号的配置
    """
    print_and_flush("🚀 开始逐个占领资源流程...")
    
    # 从配置文件获取目标配比，优先使用当前账号的配置
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 如果提供了账号索引，则使用该账号的配置
        if account_index is not None and 0 <= account_index < len(config.get("accounts", [])):
            target_distribution = config["accounts"][account_index]["config"].get("target_resource_distribution", {
                "农田": 9,
                "森林": 0,
                "草原": 0,
                "山丘": 0,
                "沼泽": 0
            })
        else:
            # 如果没有提供账号索引或索引无效，使用全局配置
            target_distribution = config.get("target_resource_distribution", {
                "农田": 9,
                "森林": 0,
                "草原": 0,
                "山丘": 0,
                "沼泽": 0
            })
    except Exception as e:
        # 如果配置文件不存在或格式错误，使用默认值
        print_and_flush(f"⚠️ 读取配置文件失败: {e}，使用默认配置")
        target_distribution = {
            "农田": 9,
            "森林": 0,
            "草原": 0,
            "山丘": 0,
            "沼泽": 0
        }
    
    # 1. 获取当前已占用的资源数量和类型分布
    occupy_resource_list = get_occupy_resource_list(session, token)

    # 统计当前各类型资源的占用情况
    current_distribution = {"农田": 0, "森林": 0, "草原": 0, "山丘": 0, "沼泽": 0}
    if occupy_resource_list:
        for res in occupy_resource_list:
            status_format = res.get("statusFormat", "")
            # 只统计非"返回"状态的资源
            if status_format != "返回":
                resource_name = res.get("brName", "未知资源")
                if resource_name in current_distribution:
                    current_distribution[resource_name] += 1

    print_and_flush(f"📊 当前资源分布: 农田{current_distribution['农田']}/9, 森林{current_distribution['森林']}/0, 草原{current_distribution['草原']}/0, 山丘{current_distribution['山丘']}/0, 沼泽{current_distribution['沼泽']}/0")

    # 计算还需要占领的各类资源数量
    needed_distribution = {}
    total_needed = 0
    for resource_type, target_count in target_distribution.items():
        needed_count = max(0, target_count - current_distribution[resource_type])
        needed_distribution[resource_type] = needed_count
        total_needed += needed_count
    
    if total_needed <= 0:
        print_and_flush("✅ 已达到目标资源配比，无需继续占领")
        return
    
    print_and_flush(f"🎯 需要占领: 农田{needed_distribution['农田']}块, 森林{needed_distribution['森林']}块, 草原{needed_distribution['草原']}块, 山丘{needed_distribution['山丘']}块, 沼泽{needed_distribution['沼泽']}块")
    
    # 2. 获取空闲武将（只获取一次，在整个流程中使用同一个武将）
    free_generals = get_free_generals(session, token)
    
    # 检查是否有空闲武将
    if not free_generals:
        print_and_flush("🔚 没有空闲武将，流程结束")
        return
        
    if not isinstance(free_generals, list) or len(free_generals) == 0:
        print_and_flush("🔚 没有可用的空闲武将，流程结束")
        return
    
    # 3. 选择第一个武将
    selected_general = free_generals[0]
    if not isinstance(selected_general, dict):
        print_and_flush("❌ 无法获取有效的武将信息，流程结束")
        return
        
    general_id = selected_general.get("mugId")
    general_name = selected_general.get("name", "无名武将")  # 修正字段名
    general_rank = selected_general.get("rank", 0)
    
    # 检查必要信息是否存在
    if not general_id:
        print_and_flush("❌ 无法获取武将ID，流程结束")
        return
    
    # 如果第一个武将rank为1，则结束整个流程
    if general_rank == 1:
        print_and_flush(f"⚠️  第一个武将 {general_name} 等级为1，结束自动占领流程")
        return
    
    print_and_flush(f"🎯 选择武将: {general_name} (ID: {general_id}, 等级: {general_rank})")
    
    # 4. 逐个用户ID检查，发现空闲资源立即占领
    occupied_count = 0
    user_id = 1
    
    # 新增变量：记录是否遇到"超出资源占领上限"错误
    exceeded_limit = False
    
    while user_id <= 100 and total_needed > 0 and not exceeded_limit:
        try:
            # 检查当前用户ID是否有空闲资源
            url = "https://q-jiang.myprint.top/api/mid-user-resource/reList"
            headers = {"Token": token}
            data = {"userId": user_id}
            
            response = session.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("success") and result.get("code") == "200":
                resource_list = result["data"].get("resourceList", [])
                
                # 筛选等级为9的资源，并且只保留农田、森林、草原、山丘、沼泽
                target_resources = ["农田", "森林", "草原", "山丘", "沼泽"]
                level_9_resources = [
                    res for res in resource_list 
                    if res.get("murRank") == 9 and res.get("name") in target_resources
                ]
                
                # 检查是否有符合需求的空闲资源
                for res in level_9_resources:
                    resource_name = res.get("name", "未知资源")
                    
                    # 检查是否还需要这种类型的资源
                    if needed_distribution.get(resource_name, 0) <= 0:
                        continue
                    
                    # 检查是否空闲（没有被占领且不是正在被占领状态）
                    if not res.get("generalDesc") and res.get("status") != 3:
                        # 发现空闲资源，立即尝试占领
                        mur_id = res.get("murId")
                        
                        # 确保murId存在
                        if not mur_id:
                            print_and_flush(f"  ⚠️ 资源缺少ID，跳过该资源")
                            continue
                        
                        print_and_flush(f"\n📍 发现空闲资源: {resource_name} (用户ID: {user_id})")
                        
                        # 获取详细信息
                        detail = get_resource_detail(session, token, mur_id, user_id)
                        
                        # 如果返回"under_attack"，表示有行军，跳过该资源
                        if detail == "under_attack":
                            print_and_flush("  ⚠️ 资源点有行军，跳过该资源")
                            continue
                        
                        if not detail:
                            print_and_flush("  ⚠️ 无法获取详细信息，跳过该资源")
                            continue
                        
                        # 尝试占领
                        occupy_result = occupy_resource(session, token, mur_id, general_id)
                        if occupy_result is True:
                            occupied_count += 1
                            needed_distribution[resource_name] -= 1
                            total_needed -= 1
                            print_and_flush(f"  ✅ 成功占领，还需占领: 农田{needed_distribution['农田']}块, 森林{needed_distribution['森林']}块, 草原{needed_distribution['草原']}块, 山丘{needed_distribution['山丘']}块, 沼泽{needed_distribution['沼泽']}块")
                            
                            # 检查是否已达到目标
                            if total_needed <= 0:
                                print_and_flush("✅ 已达到目标资源配比")
                                print_and_flush(f"🏁 逐个占领流程结束，共成功占领 {occupied_count} 个资源")
                                return
                        elif occupy_result == "超出资源占领上限":
                            # 遇到"超出资源占领上限"错误，设置标志并跳出循环
                            print_and_flush("🚫 超出资源占领上限，停止继续占领")
                            exceeded_limit = True
                            break
                        else:
                            print_and_flush("  ❌ 占领失败，继续查找下一个资源")
            
            # 添加延迟避免请求过于频繁
            time.sleep(0.5)
            
        except Exception as e:
            # 忽略单个用户请求失败，继续检查下一个
            print_and_flush(f"  ⚠️ 检查用户 {user_id} 时出错: {e}")
            pass
        
        user_id += 1
    
    if exceeded_limit:
        print_and_flush("🏁 由于超出资源占领上限，提前结束占领流程")
    else:
        print_and_flush(f"🏁 逐个占领流程结束，共成功占领 {occupied_count} 个资源")
# ... existing code ...