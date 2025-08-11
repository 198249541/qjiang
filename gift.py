# gift.py
import time
import requests
from friend import get_friend_give_status, get_my_give_list, get_friend_list
import sys

# 🧾 资源ID与名称映射
GIFT_ITEMS = {
    47: "绢布",
    48: "木材",
    49: "石材",
    50: "陶土",
    51: "铁矿"
}

# ==================== 1. 向好友索要资源 ====================
def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()
def ask_gift(session, token, friend_id, friend_name, goodsid):
    """
    向单个好友发起索要请求
    """
    url = "https://q-jiang.myprint.top/api/user/askGift"
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    data = {"friendId": friend_id, "goodsId": goodsid}
    
    # 关闭调试打印
    #print_and_flush(f"  -> 请求URL: {url}")
    #print_and_flush(f"  -> 请求头: Token={token[:10]}..." if token else "  -> 请求头: 无Token")
    #print_and_flush(f"  -> 请求参数: friendId={friend_id}, goodsId={goodsid}")
    
    try:
        print_and_flush(f"🎁 正在向 {friend_name} 索要...")
        response = session.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        # 关闭调试打印
        #print_and_flush(f"  -> 响应结果: {result}")  # 打印响应结果
        if result.get("success") and str(result.get("code")) == "200":
            print_and_flush(f"✅ 索要请求发送成功")
            return True
        else:
            msg = result.get("msg", "未知错误")
            if "已经索要" in msg or "已索要" in msg:
                print_and_flush(f"🟡 已索要")
            elif "不是好友" in msg:
                print_and_flush(f"🚫 非好友")
            elif "无法索要" in msg:
                print_and_flush(f"🚫 无法索要")
            else:
                print_and_flush(f"❌ {msg}")
            return False
    except Exception as e:
        print_and_flush(f"❌ 请求异常: {str(e)}")
        return False


def ask_gifts_to_all_friends(session, token, goodsid):
    """
    批量向所有好友索要指定资源
    """
    if goodsid not in GIFT_ITEMS:
        print_and_flush(f"❌ 无效的资源编号: {goodsid}")
        return
    resource_name = GIFT_ITEMS[goodsid]
    print_and_flush(f"\n📬 开始批量索要【{resource_name}】...")

    # 直接使用好友列表，其中 askIs 字段表示今天是否已索要
    friends = get_friend_list(session, token)
    if not friends:
        print_and_flush("❌ 好友列表为空或获取失败")
        return

    # askIs: 0=未索要, 1=已索要
    can_ask_list = [f for f in friends if f.get("askIs") == 0]
    already_asked = [f for f in friends if f.get("askIs") == 1]
    total = len(friends)
    available = len(can_ask_list)
    already_count = len(already_asked)

    print_and_flush(f"📌 共 {total} 位好友")
    print_and_flush(f"✅ {available} 位可索要")
    if already_count > 0:
        print_and_flush(f"🟡 {already_count} 位已索要（今日）")
    if available == 0:
        print_and_flush("📭 今日已向所有好友索要过")
        return

    print_and_flush(f"📤 正在向 {available} 位好友发送请求...\n")
    success_count = 0
    for friend in can_ask_list:
        if ask_gift(session, token, friend["userId"], friend["userName"], goodsid=goodsid):
            success_count += 1
        time.sleep(1.2)
    print_and_flush(f"\n🎉 批量索要完成！成功向 {success_count} 人发送请求")


# ==================== 2. 自动赠送别人向你索要的资源 ====================
def handle_received_ask_request(session, token, requester_id, goods_id):
    """
    单次处理一个索要请求
    返回: "success" 成功, "already_done" 已处理, "failed" 失败
    """
    url = "https://q-jiang.myprint.top/api/user/giveGift"
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    data = {"friendId": requester_id, "goodsId": goods_id}
    
    # 关闭调试打印
    #print_and_flush(f"  -> 请求URL: {url}")
    #print_and_flush(f"  -> 请求头: Token={token[:10]}..." if token else "  -> 请求头: 无Token")
    #print_and_flush(f"  -> 请求参数: friendId={requester_id}, goodsId={goods_id}")
    
    try:
        response = session.post(url, json=data, headers=headers)
        # 关闭调试打印
        #print_and_flush(f"  -> HTTP状态码: {response.status_code}")  # 打印HTTP状态码
        if response.status_code != 200:
            # 关闭调试打印
            #print_and_flush(f"  -> 响应内容: {response.text}")  # 打印响应内容
            return "failed"
        result = response.json()
        # 关闭调试打印
        #print_and_flush(f"  -> 响应结果: {result}")  # 打印响应结果
        if result.get("success") and str(result.get("code")) == "200":
            return "success"
        else:
            msg = result.get("msg", "未知错误")
            if "已经赠送" in msg or "已经赠过" in msg or "今天已经赠送" in msg:
                return "already_done"
            else:
                print_and_flush(f"❌ 赠送失败: {msg}")
                return "failed"
    except Exception as e:
        print_and_flush(f"❌ 赠送异常: {str(e)}")
        return "failed"


def handle_received_ask_requests(session, token):
    """
    自动处理所有【别人向你】发起的索要请求
    """
    print_and_flush("\n📨 开始处理【别人向你】发起的索要请求...")
    friends = get_friend_give_status(session, token)
    if not friends:
        print_and_flush("📪 无任何索要请求")
        return

    # 有 askId 并且 giveIs != 1 才表示需要处理 (giveIs: 1=已赠送，0=未赠送)
    pending = [f for f in friends if f.get("askId") and f.get("giveIs") != 1]
    already_done = [f for f in friends if f.get("askId") and f.get("giveIs") == 1]
    total_with_ask_id = len([f for f in friends if f.get("askId")])

    print_and_flush(f"📌 共收到 {total_with_ask_id} 条索要记录")
    print_and_flush(f"✅ {len(already_done)} 条你已赠送（跳过）")
    print_and_flush(f"📤 {len(pending)} 条待处理")

    if not pending:
        print_and_flush("✅ 所有请求均已处理")
        return

    print_and_flush(f"⏳ 正在处理 {len(pending)} 条请求...\n")
    success_count = 0
    failed_count = 0
    already_processed_count = 0
    
    for f in pending:
        goods_name = GIFT_ITEMS.get(f["goodsId"], f"未知资源({f['goodsId']})")
        # 关闭调试打印
        #print_and_flush(f"  处理请求: {f['userName']} 索要 {goods_name}")  # 打印正在处理的请求
        result = handle_received_ask_request(session, token, f["userId"], f["goodsId"])
        if result == "success":
            print_and_flush(f"  ✅ 已向 {f['userName']} 赠送 {goods_name}")
            success_count += 1
        elif result == "already_done":
            print_and_flush(f"  🟡 {f['userName']} 的请求已处理")
            already_processed_count += 1
        else:
            print_and_flush(f"  ❌ 向 {f['userName']} 赠送失败")
            failed_count += 1
        time.sleep(1.0)

    print_and_flush(f"\n🎉 赠送处理完成！成功 {success_count} 人，失败 {failed_count} 人，已处理 {already_processed_count} 人")


# ==================== 3. 自动领取好友赠送的资源 ====================
def receive_gift(session, token, giver_id):
    """
    领取单个好友赠送的资源
    """
    # 使用正确的接口 receiveFriendGift
    url = "https://q-jiang.myprint.top/api/user/receiveFriendGift"
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    data = {"friendId": giver_id}
    
    # 关闭调试打印
    #print_and_flush(f"  -> 请求URL: {url}")
    #print_and_flush(f"  -> 请求头: Token={token[:10]}..." if token else "  -> 请求头: 无Token")
    #print_and_flush(f"  -> 请求参数: friendId={giver_id}")
    
    try:
        response = session.post(url, json=data, headers=headers)
        # 关闭调试打印
        #print_and_flush(f"  -> HTTP状态码: {response.status_code}")  # 打印HTTP状态码
        response.raise_for_status()
        result = response.json()
        # 关闭调试打印
        #print_and_flush(f"  -> 响应结果: {result}")  # 打印响应结果
        if result.get("success") and str(result.get("code")) == "200":
            goods_list = result.get("data", [])
            return True, goods_list
        else:
            return False, [result.get("msg", "未知错误")]
    except requests.exceptions.RequestException as e:
        return False, [f"网络请求错误: {str(e)}"]
    except Exception as e:
        return False, [str(e)]


def receive_gifts_from_friends(session, token):
    print_and_flush("\n📥 开始检查并领取好友赠送的资源...")
    
    # 通过 giveGiftList 接口获取我向别人赠送的记录，并检查别人是否已赠送给我
    my_give_list = get_my_give_list(session, token)
    if not my_give_list:
        print_and_flush("📭 无任何赠送记录")
        return

    # receiveIs=0 表示对方已赠送但我未领取
    pending = [item for item in my_give_list if item.get("receiveIs") == 0]
    already_received = [item for item in my_give_list if item.get("receiveIs") == 1]
    total = len(my_give_list)

    print_and_flush(f"📌 共收到 {total} 条赠送记录")
    print_and_flush(f"✅ {len(already_received)} 条已领取（跳过）")
    print_and_flush(f"📤 {len(pending)} 条待领取")

    if not pending:
        print_and_flush("✅ 所有礼物均已领取")
        return

    print_and_flush(f"⏳ 正在领取 {len(pending)} 份礼物...\n")
    success_count = 0
    fail_count = 0
    
    # 创建 userId 到 userName 的映射，用于显示
    user_map = {item["friendId"]: item["userName"] for item in my_give_list}
    
    for i, item in enumerate(pending, 1):
        # 修正：应该使用 userId（赠送者ID）而不是 friendId（你自己的ID）
        giver_id = item["userId"]  # 赠送者ID
        friend_id = item["friendId"]  # 你自己的ID（在列表中是作为friendId出现的）
        goods_name = GIFT_ITEMS.get(item["giveGiftGoodsId"], f"未知资源({item['giveGiftGoodsId']})")
        friend_name = user_map.get(friend_id, f"未知用户({friend_id})")
        
        # 关闭调试打印
        #print_and_flush(f"🎁 [{i}/{len(pending)}] {friend_name} 送你 {goods_name}")
        #print_and_flush(f"  -> 赠送者ID: {giver_id}, 你的ID: {friend_id}")
        #print_and_flush(f"  -> 赠送记录详情: {item}")  # 打印赠送记录详情
        success, goods_list = receive_gift(session, token, giver_id)  # 传入赠送者ID
        if success:
            # 更安全的检查方式
            try:
                if goods_list and isinstance(goods_list, list) and len(goods_list) > 0:
                    gift_item = goods_list[0]
                    name = gift_item.get('name', goods_name) if isinstance(gift_item, dict) else goods_name
                    count = gift_item.get('goodsNum', 1) if isinstance(gift_item, dict) else 1
                    print_and_flush(f"  ✅ 领取成功：{name} ×{count}")
                else:
                    print_and_flush(f"  ✅ 领取成功")
            except Exception as e:
                print_and_flush(f"  ✅ 领取成功（解析明细出错: {e}）")
            success_count += 1
        else:
            # 更安全的错误处理
            try:
                error_msg = goods_list[0] if goods_list and isinstance(goods_list, list) and len(goods_list) > 0 else "未知错误"
                # 移除"不是好友"的特殊处理，让程序继续尝试领取
                print_and_flush(f"  ❌ 领取失败: {error_msg}")
            except Exception as e:
                print_and_flush(f"  ❌ 领取失败: 未知错误 ({e})")
            fail_count += 1
        time.sleep(1.0)

    print_and_flush(f"\n🎉 领取完成！成功 {success_count} 份，失败 {fail_count} 份")


# ==================== 4. 一键执行 ====================
def auto_gift_flow(session, token, ask_goodsid=49):
    print_and_flush("🔄 开始自动资源交互流程...")
    ask_gifts_to_all_friends(session, token, ask_goodsid)
    handle_received_ask_requests(session, token)
    receive_gifts_from_friends(session, token)
    print_and_flush("✅ 自动流程执行完毕")