# friend.py
import requests
import time
import sys
def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()
def get_friend_list(session, token):
    """
    获取基础好友列表
    """
    url = "https://q-jiang.myprint.top/api/user/friendList"
    headers = {"Token": token}

    try:
        response = session.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result.get("success") and str(result.get("code")) == "200":
            return [
                {
                    "userId": item["friendId"],
                    "userName": item["userName"],
                    "askIs": item["askIs"]  # 1=今天已索要，0=今天未索要
                }
                for item in result.get("data", [])
            ]
        else:
            print_and_flush(f"❌ 获取好友列表失败: {result.get('msg', '未知错误')}")
            return []
    except Exception as e:
        print_and_flush(f"⚠️ 请求异常: {e}")
        return []


def get_friend_give_status(session, token):
    """
    获取好友赠送状态（别人向我索要的情况）
    """
    friends = get_friend_list(session, token)
    if not friends:
        return []

    try:
        # 获取别人向我索要的记录
        ask_url = "https://q-jiang.myprint.top/api/user/askGiftList"
        headers = {"Token": token}
        response = session.post(ask_url, headers=headers)
        response.raise_for_status()
        result = response.json()

        if not (result.get("success") and str(result.get("code")) == "200"):
            print_and_flush(f"⚠️ 获取 askGiftList 失败: {result.get('msg', '未知错误')}")
            for f in friends:
                f["giveIs"] = None
                f["askId"] = None
                f["goodsId"] = None
                f["receiveIs"] = None
            return friends

        # 移除 debug 输出
        # print_and_flush("🔍 debug: askGiftList 返回数据 =", data_list[:3])  # 查看真实结构

        data_list = result.get("data", [])
        
        # 构建 userId -> 状态映射 (别人向我索要)
        ask_map = {}
        for item in data_list:
            # userId 是向我索要的人的ID
            ask_map[item["userId"]] = {
                "askId": item["id"],                    # 索要记录ID
                "goodsId": item["askGiftGoodsId"],      # 索要的资源ID
                "giveIs": item.get("giveIs"),           # 我是否已赠送？（1=已赠送，0=未赠送）
                "receiveIs": item.get("receiveIs")      # 我是否已领取？（这个字段在这里可能不相关）
            }

        # 合并到好友列表
        for friend in friends:
            fid = friend["userId"]
            
            # 处理别人是否向我索要
            if fid in ask_map:
                friend.update(ask_map[fid])
            else:
                friend.update({
                    "askId": None,
                    "goodsId": None,
                    "giveIs": None,  # None 表示没人向我索要
                    "receiveIs": None
                })

        return friends

    except Exception as e:
        print_and_flush(f"⚠️ 获取赠送状态异常: {e}")
        for f in friends:
            f["giveIs"] = None
            f["askId"] = None
            f["goodsId"] = None
            f["receiveIs"] = None
        return friends


def get_my_ask_status(session, token):
    """
    获取我向别人索要的状态
    通过 friendList 中的 askIs 字段判断
    """
    return get_friend_list(session, token)


def get_my_give_list(session, token):
    """
    获取我向好友赠送的列表
    """
    url = "https://q-jiang.myprint.top/api/user/giveGiftList"
    headers = {"Token": token}

    try:
        response = session.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result.get("success") and str(result.get("code")) == "200":
            return result.get("data", [])
        else:
            print_and_flush(f"❌ 获取赠送列表失败: {result.get('msg', '未知错误')}")
            return []
    except Exception as e:
        print_and_flush(f"⚠️ 请求赠送列表异常: {e}")
        return []


def get_friend_requests(session, token):
    """
    获取好友申请列表
    """
    url = "https://q-jiang.myprint.top/api/user/askFriendList"
    headers = {"Token": token}

    try:
        response = session.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result.get("success") and str(result.get("code")) == "200":
            return result.get("data", [])
        else:
            print_and_flush(f"❌ 获取好友申请列表失败: {result.get('msg', '未知错误')}")
            return []
    except Exception as e:
        print_and_flush(f"⚠️ 请求好友申请列表异常: {e}")
        return []


def accept_friend_request(session, token, friend_id, requester_name):
    """
    同意好友申请
    根据接口信息，需要传入 friendId 而不是 id
    """
    url = "https://q-jiang.myprint.top/api/user/agreeFriend"
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    data = {"friendId": friend_id}  # 根据你提供的信息，这里应该是 friendId
    
    try:
        print_and_flush(f"🤝 正在同意 {requester_name} 的好友申请...")
        response = session.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success") and str(result.get("code")) == "200":
            print_and_flush(f"✅ 成功添加 {requester_name} 为好友")
            return True
        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 同意好友申请失败: {msg}")
            return False
    except Exception as e:
        print_and_flush(f"❌ 同意好友申请异常: {str(e)}")
        return False


def auto_accept_friend_requests(session, token):
    """
    自动同意所有好友申请
    """
    print_and_flush("\n🤝 开始处理好友申请...")
    requests_list = get_friend_requests(session, token)
    
    if not requests_list:
        print_and_flush("📭 暂无好友申请")
        return

    print_and_flush(f"📌 共收到 {len(requests_list)} 条好友申请")
    
    success_count = 0
    fail_count = 0
    
    for req in requests_list:
        # 根据返回数据，userId 是申请者ID，friendId 是我的ID
        friend_id = req.get("userId")  # 申请者的用户ID
        requester_name = req.get("userName", "未知用户")
        
        if accept_friend_request(session, token, friend_id, requester_name):
            success_count += 1
        else:
            fail_count += 1
            
        time.sleep(1)  # 避免请求过快
    
    print_and_flush(f"\n🎉 好友申请处理完成！成功 {success_count} 人，失败 {fail_count} 人")