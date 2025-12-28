# simple_daily.py
# 简化版每日任务 - 仅保留邮件、领地、守家、好友功能

import os
import time
import json
import requests
import traceback
import sys
import io


# 设置环境变量以确保UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONLEGACYWINDOWSFSENCODING'] = 'utf-8'

# 强制设置标准输入输出编码
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 如果在Windows上，设置控制台代码页
if os.name == 'nt':
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)  # UTF-8 code page
        ctypes.windll.kernel32.SetConsoleCP(65001)        # UTF-8 code page
    except:
        pass

def traceback_print_and_flush_exc():
    traceback.print_exc()
    sys.stdout.flush()

def print_and_flush(*args, **kwargs):
    try:
        if sys.stdout and not sys.stdout.closed:
            print(*args, **kwargs, flush=True)
    except (ValueError, OSError):
        # stdout 被关闭时忽略输出 
        pass

def is_token_valid(session: requests.Session, token: str) -> bool:
    """
    检查token是否有效
    通过访问一个需要认证的接口来判断
    """
    if not token:
        return False
        
    url = "https://q-jiang.myprint.top/api/mid-user-resource/reList"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }
    
    try:
        response = session.post(url, headers=headers, json={}, timeout=10)
        result = response.json()
        
        # 如果返回code为200且success为True，则token有效
        if result.get("success") and str(result.get("code")) == "200":
            return True
        # 如果返回需要重新登录的错误码或消息
        elif str(result.get("code")) in ["401", "403"] or "登录" in str(result.get("msg", "")):
            return False
        # 其他情况认为token有效
        return True
    except Exception as e:
        # 网络异常等情况下，默认认为token可能无效
        return False

# ========== 配置区 ========== 
def load_config():
    """
    加载配置文件
    """
    config_file = "config.json"
    
    if not os.path.exists(config_file):
        # 未检测到config.json文件
        print_and_flush(f"❌ 未检测到 config.json 配置文件")
        print_and_flush("📝 请使用 account_config.py 生成配置文件")
        print_and_flush("运行命令: python account_config.py")
        sys.exit(1)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        print_and_flush(f"❌ 配置文件格式错误: {e}")
        sys.exit(1)
    except Exception as e:
        print_and_flush(f"❌ 读取配置文件失败: {e}")
        sys.exit(1)

config = load_config()
ACCOUNTS = config["accounts"]
TOKEN_FILES = [f"user_token_{i+1}.json" for i in range(len(ACCOUNTS))]  # 为每个账号创建独立的token文件
GIFT_ITEMS = config["gift_items"]
DEFAULT_GOODSID = config["default_goodsid"]
# ===========================

print_and_flush(" 程序初始化中...")

# 导入必要的模块
try:
    print_and_flush(" 正在加载模块...")
    from login import login
    # 领地资源相关功能
    from landResources import get_all_land_resources, auto_occupy_resources_gradually
    # 邮件管理相关功能
    from email_manager import display_emails, process_all_customs_emails, get_all_attachments, delete_claimed_and_expired_emails  
    # 好友相关功能
    from friend import auto_accept_friend_requests
    # 守家铜币相关功能
    from home_copper import collect_home_copper
    # 好友资源互赠相关功能
    from gift import ask_gifts_to_all_friends, handle_received_ask_requests, receive_gifts_from_friends
    #武将训练相关功能
    from summonCard import get_general_list, auto_train_generals
    # 市场自动征收功能
    from market import get_market_info, auto_change_silver_ticket
    # 日常任务奖励领取功能
    from daily_tasks import claim_all_available_rewards
    #背包模块
    from pack import get_pack_info
    # 擂台功能
    from arena import get_arena_rank_list, get_arena_award_list, exchange_arena_goods, auto_exchange_arena_goods, get_arena_info
except ImportError as e:
    print_and_flush(f" 模块导入失败: {e}")
    print_and_flush("请检查所有依赖文件是否存在")
    traceback_print_and_flush_exc()
    exit(1)

def ensure_session_token(session: requests.Session, tel: str, pwd: str, token_file: str):
    """
    确保 session 中有有效的 token，并返回 user_id
    添加了token有效性检查，避免重复登录
    """
    token = None
    user_id = None
    
    # 首先尝试从文件读取保存的token
    try:
        if os.path.exists(token_file):
            with open(token_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
                token = token_data.get("token")
                user_id = token_data.get("user_id")
                print_and_flush(f" 从文件加载token: {token_file}")
    except Exception as e:
        print_and_flush(f" 读取token文件失败: {e}")
    
    # 检查token是否有效
    if token and is_token_valid(session, token):
        print_and_flush(" 检测到有效token，无需重新登录")
        return session, token, user_id
    else:
        print_and_flush(" Token无效或不存在，正在登录...")
    
    # 如果token无效或不存在，则重新登录
    print_and_flush(" 正在登录...")
    try:
        login_result = login(tel, pwd)
        if login_result:
            new_token = None
            new_user_id = None

            if isinstance(login_result, dict):
                new_token = login_result.get("token") or (login_result.get("data") or {}).get("token")
                new_user_id = login_result.get("user_id") or (login_result.get("data") or {}).get("user_id")
            elif isinstance(login_result, (list, tuple)) and len(login_result) > 0:
                new_token = login_result[0]
                if len(login_result) > 1:
                    new_user_id = login_result[1]
            elif isinstance(login_result, str):
                new_token = login_result

            if not isinstance(new_user_id, (str, int)) or not str(new_user_id).strip():
                print_and_flush(" 登录成功但未返回有效 user_id")
                new_user_id = None

            if new_token:
                print_and_flush(f" 登录成功！")
                # 保存token到文件
                try:
                    token_data = {
                        "token": new_token,
                        "user_id": new_user_id,
                        "tel": tel,
                        "timestamp": time.time()
                    }
                    with open(token_file, 'w', encoding='utf-8') as f:
                        json.dump(token_data, f, ensure_ascii=False, indent=2)
                    print_and_flush(f" Token已保存到: {token_file}")
                except Exception as e:
                    print_and_flush(f" 保存token失败: {e}")
                return session, new_token, new_user_id
            else:
                print_and_flush(" 登录未返回有效 token")
        else:
            print_and_flush(" 登录失败")
    except Exception as e:
        print_and_flush(f" 登录过程出错: {e}")
        traceback_print_and_flush_exc()

    print_and_flush(" 无法获取 token，程序终止。")
    return session, None, None

def run_account_tasks(account_index: int, tel: str, pwd: str, token_file: str):
    """
    为单个账号运行保留的任务（邮件、领地、守家、好友）
    """
    try:
        session = requests.Session()
        print_and_flush("🌐 网络会话已创建")
        session, token, user_id = ensure_session_token(session, tel, pwd, token_file)
        if not token:
            print_and_flush(" 无法获取有效token，跳过此账号")
            return

        print_and_flush(f" Token 已加载（前12位）：{str(token)[:12]}...")
        print_and_flush("-" * 50)

        # ========== 擂台功能 ==========
        print_and_flush("\n" + "=" * 50)
        print_and_flush("🏟️ 擂台功能")
        print_and_flush("=" * 50)
        try:
            # 查看擂台排行榜
            get_arena_rank_list(session, token)
            
            # 自动兑换积分物品
            auto_exchange_arena_goods(session, token)
        except Exception as e:
            print_and_flush(f" 擂台功能执行失败: {e}")
            traceback_print_and_flush_exc()

        # ========== 市场自动征收功能 ==========
        print_and_flush("\n" + "=" * 50)
        print_and_flush("💰 市场自动征收")
        print_and_flush("=" * 50)
        try:
            get_market_info(session, token)
        except Exception as e:
            print_and_flush(f" 市场信息获取失败: {e}")
            traceback_print_and_flush_exc()

        # ========== 银票自动兑换功能 ==========
        print_and_flush("\n" + "=" * 50)
        print_and_flush("💵 银票自动兑换")
        print_and_flush("=" * 50)
        try:
            auto_change_silver_ticket(session, token)
        except Exception as e:
            print_and_flush(f" 银票自动兑换失败: {e}")
            traceback_print_and_flush_exc()

        # ========== 武将自动训练功能 ==========
        print_and_flush("\n" + "=" * 50)
        print_and_flush("⚔️ 武将自动训练")
        print_and_flush("=" * 50)
        try:
            generals = get_general_list(session, token)
            if generals:
                auto_train_generals(session, token, generals, max_trains=config.get("max_train_slots", 2))
            else:
                print_and_flush("⚠️ 未能获取武将列表，跳过自动训练")
        except Exception as e:
            print_and_flush(f" 武将自动训练失败: {e}")
            traceback_print_and_flush_exc()

        # ========== 领地资源功能 ==========
        print_and_flush("\n" + "=" * 50)
        print_and_flush("🌍 领地资源管理")
        print_and_flush("=" * 50)
        try:
            # 获取所有领地资源并自动召回
            get_all_land_resources(session, token)
            
            # 逐个占领资源（按固定配比）
            auto_occupy_resources_gradually(session, token)
        except Exception as e:
            print_and_flush(f" 领地资源管理失败: {e}")
            traceback_print_and_flush_exc()

        # ========== 守家铜币功能 ==========
        print_and_flush("\n" + "=" * 50)
        print_and_flush("🏠 领取守家铜币")
        print_and_flush("=" * 50)
        if isinstance(user_id, (int, str)) and str(user_id).strip():
            try:
                collect_home_copper(session, token, user_id)
            except Exception as e:
                print_and_flush(f" 领取守家铜币失败: {e}")
                traceback_print_and_flush_exc()
        else:
            print_and_flush(f" 跳过领取守家铜币：user_id 无效 ({user_id})")

        # ========== 好友功能 ==========
        print_and_flush("\n" + "=" * 50)
        print_and_flush("🤝 好友功能")
        print_and_flush("=" * 50)
        
        # 自动同意好友申请
        try:
            auto_accept_friend_requests(session, token)
        except Exception as e:
            print_and_flush(f" 处理好友申请出错: {e}")
            traceback_print_and_flush_exc()
        
        # 好友资源互赠
        try:
            goodsid = DEFAULT_GOODSID
            print_and_flush(f" 自动选择资源: {GIFT_ITEMS.get(str(goodsid), '未知资源')}")
            
            if str(goodsid) in GIFT_ITEMS:
                ask_gifts_to_all_friends(session, token, goodsid)
                handle_received_ask_requests(session, token)
                receive_gifts_from_friends(session, token)
            else:
                print_and_flush(" 无效的资源ID，跳过好友互赠")
        except Exception as e:
            print_and_flush(f" 好友互赠流程出错: {e}")
            traceback_print_and_flush_exc()

        # ========== 邮件功能 ==========
        print_and_flush("\n" + "=" * 50)
        print_and_flush("📧 邮件处理")
        print_and_flush("=" * 50)
        try:
            display_emails(session, token)
            print_and_flush("\n 正在处理关卡抽奖邮件...")
            process_all_customs_emails(session, token)
            print_and_flush("\n📎 正在领取普通邮件附件...")
            get_all_attachments(session, token)
            delete_claimed_and_expired_emails(session, token)
        except Exception as e:
            print_and_flush(f" 处理邮件失败: {e}")
            traceback_print_and_flush_exc()

        # ========== 日常任务奖励自动领取 ==========
        print_and_flush("\n" + "=" * 50)
        print_and_flush("🎁 日常任务奖励自动领取")
        print_and_flush("=" * 50)
        try:
            claim_all_available_rewards(session, token)
        except Exception as e:
            print_and_flush(f" 领取日常任务奖励失败: {e}")
            traceback_print_and_flush_exc()
        pack_data = get_pack_info(session, token)

        print_and_flush(f"\n 账号 {account_index + 1} 核心功能任务完成")
        
    except KeyboardInterrupt:
        print_and_flush(f"\n 用户中断账号 {account_index + 1} 程序执行")
    except Exception as e:
        print_and_flush(f"\n 账号 {account_index + 1} 程序运行过程中出现未处理的异常: {e}")
        traceback_print_and_flush_exc()

def main():
    print_and_flush(" 开始执行核心功能任务...")
    print_and_flush(f" {time.strftime('%Y年%m月%d日 %H:%M:%S')}")
    print_and_flush(f"👥 共 {len(ACCOUNTS)} 个账号")
    print_and_flush("-" * 50)
    
    # 如果没有账号配置，直接退出
    if not ACCOUNTS:
        print_and_flush(" 没有配置任何账号，程序退出")
        return

    # 为每个账号运行任务
    for i, account in enumerate(ACCOUNTS):
        tel = account["tel"]
        pwd = account["pwd"]
        token_file = TOKEN_FILES[i] if i < len(TOKEN_FILES) else f"user_token_{i+1}.json"
        
        try:
            run_account_tasks(i, tel, pwd, token_file)
        except Exception as e:
            print_and_flush(f" 账号 {i+1} 执行出错: {e}")
            traceback_print_and_flush_exc()
        
        # 账号间间隔时间
        if i < len(ACCOUNTS) - 1:  # 不是最后一个账号
            print_and_flush(f"\n⏳ 等待 5 秒后执行下一个账号...")
            time.sleep(5)

    print_and_flush(f"\n{'='*60}")
    print_and_flush("🎉 核心功能任务执行完毕")
    print_and_flush(f"{'='*60}")

if __name__ == "__main__":
    # 设置环境变量表示在Web环境中运行
    os.environ['RUN_IN_WEB'] = 'true'
    main()