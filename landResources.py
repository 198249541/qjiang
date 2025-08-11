# landResources.py
# 功能：获取并显示领地资源列表（一行一条，简洁格式）
import sys
import datetime
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
            occupy_resource_list.sort(key=lambda x: x.get("occupyTime", ""), reverse=True)

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