# main.py
import os
import time
import json
import requests
import traceback
from typing import Optional, Any
import threading
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
AUTO_MODE = config["auto_mode"]
INPUT_TIMEOUT = config["input_timeout"]
# ===========================

print_and_flush(" 程序初始化中...")  # 添加初始化提示

# 其余代码保持不变...
try:
    print_and_flush(" 正在加载模块...")
    from login import login
    from landResources import get_re_list, get_occupy_resource_list, get_all_land_resources
    from generalCard import get_pub_general_list, recruit_general, format_general_info
    from summonCard import get_general_list, train_general
    from market import get_market_info
    from gift import ask_gifts_to_all_friends, handle_received_ask_requests, receive_gifts_from_friends
    from sign_in import auto_daily_check_in, auto_continuous_check_in
    from home_copper import collect_home_copper
    from customs_battle import customs_battle
    from daily_tasks import display_daily_tasks, claim_all_available_rewards
    from email_manager import display_emails, process_all_customs_emails, get_all_attachments, delete_claimed_and_expired_emails  
    from friend import auto_accept_friend_requests
    from pack import get_pack_info, auto_use_battle_card
except ImportError as e:
    print_and_flush(f" 模块导入失败: {e}")
    print_and_flush("请检查所有依赖文件是否存在")
    traceback_print_and_flush_exc()
    exit(1)


def ensure_session_token(session: requests.Session, tel: str, pwd: str, token_file: str):
    """
    确保 session 中有有效的 token，并返回 user_id
    """
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

def perform_training_cycle(session: requests.Session, token: str, pub_list):
    """
    执行一轮完整的招募->训练->提魂流程
    """
    # 步骤1: 获取招募前的武将列表
    generals_before = get_general_list(session, token)
    general_ids_before = set()
    if generals_before:
        general_ids_before = {g.get("mugId") or g.get("id") for g in generals_before if g.get("mugId") or g.get("id")}
    
    # 步骤2: 酒馆招募第一个武将
    mugId = None
    if pub_list:
        recruits = [(i + 1, g.get("id"), format_general_info(g)) for i, g in enumerate(pub_list) if g.get("id")]
        if recruits:
            # 自动选择第一个武将进行招募
            _, mid, info = recruits[0]
            print_and_flush(f" 自动招募：{info}")
            recruited_result = recruit_general(session, token, mup_id=mid)
            
            # 招募成功后，重新获取武将列表来找到新招募的武将
            if recruited_result:
                print_and_flush("🔍 正在获取新招募的武将信息...")
                # 等待一小段时间确保服务器数据同步
                time.sleep(1)
                
                # 获取招募后的武将列表
                generals_after = get_general_list(session, token)
                if generals_after:
                    # 通过比较前后列表找到新增的武将
                    general_ids_after = {g.get("mugId") or g.get("id") for g in generals_after if g.get("mugId") or g.get("id")}
                    new_general_ids = general_ids_after - general_ids_before
                    
                    if new_general_ids:
                        # 找到新招募的武将
                        new_general_id = new_general_ids.pop()
                        mugId = new_general_id
                        # 找到对应的武将详细信息
                        for general in generals_after:
                            if (general.get("mugId") or general.get("id")) == new_general_id:
                                print_and_flush(f"✅ 找到新招募武将，ID: {mugId}")
                                print_and_flush(f"   武将信息: {format_general_info(general)}")
                                break
                    else:
                        # 如果没有找到差异，尝试使用第一个武将
                        if generals_after:
                            mugId = generals_after[0].get("mugId") or generals_after[0].get("id")
                            if mugId:
                                print_and_flush(f"🔄 使用列表中第一个武将作为新招募武将，ID: {mugId}")
    
    # 如果没有成功获取武将ID，返回None
    if not mugId:
        print_and_flush("⚠️ 未成功获取武将ID，跳过本轮训练和提魂")
        return None
    
    # 步骤3: 将武将放入训练槽训练
    print_and_flush(f"\n 将新招募武将放入训练槽训练...") 
    # 获取当前武将列表以确定空闲槽位
    generals = get_general_list(session, token)
    if generals:
        # 寻找空闲槽位
        free_slot_indices = []
        for i, gen in enumerate(generals):
            if gen.get("trainStatus") != 1:  # 不在训练中
                free_slot_indices.append(i)
        
        if free_slot_indices:
            # 使用第一个空闲槽位
            slot_idx = 0 if 0 not in [g.get("trainIndex") for g in generals if g.get("trainStatus") == 1] else 1
            print_and_flush(f" 放入训练槽{slot_idx+1}")
            train_general(session, token, mugId, type=1, index=slot_idx)
    
    # 步骤4: 执行提魂操作
    print_and_flush(f"\n 开始执行提魂...")
    if extract_soul(session, token, mugId):
        print_and_flush("✅ 提魂成功")
    else:
        print_and_flush("❌ 提魂失败")
    
    return mugId


# 修改后的 run_account_tasks 函数中的相关部分

def run_account_tasks(account_index: int, tel: str, pwd: str, token_file: str):
    """
    为单个账号运行所有任务
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
        # 获取背包信息并使用闯关卡（放在闯关之前）
        print_and_flush("\n" + "=" * 50)
        print_and_flush(" 背包信息及闯关卡使用")
        print_and_flush("=" * 50)
        try:
            # 先获取背包信息
            pack_data = get_pack_info(session, token)
            # 如果获取成功，则尝试使用一个闯关卡
            if pack_data and pack_data.get("packGoodsVos"):
                auto_use_battle_card(session, token, pack_data["packGoodsVos"])
        except Exception as e:
            print_and_flush(f" 背包信息获取或闯关卡使用失败: {e}")
            traceback_print_and_flush_exc()
        
        # 闯关10次
        print_and_flush("\n" + "=" * 50)
        print_and_flush(" 开始闯关任务（10次）...")
        print_and_flush("=" * 50)
        try:
            # 从配置中获取闯关设置
            battle_settings = config.get("customs_battle_settings", {"times": 10})
            customs_battle(session, token, user_id, total_times=battle_settings.get("times", 10))
        except Exception as e:
            print_and_flush(f" 关卡战斗出错: {e}")
            traceback_print_and_flush_exc()
        
        # 领取任务奖励
        try:
            print_and_flush("\n" + "=" * 50)
            print_and_flush(" 领取日常任务奖励")
            print_and_flush("=" * 50)
            claim_all_available_rewards(session, token)
        except Exception as e:
            print_and_flush(f" 领取任务奖励失败: {e}")
            traceback_print_and_flush_exc()

        # 其余代码保持不变...
        print_and_flush("🔍 市场")
        try:
            get_market_info(session, token)
        except Exception as e:
            print_and_flush(f" {e}")
            traceback_print_and_flush_exc()
        time.sleep(1)

        # 修改：使用新的函数获取所有领地资源并自动召回
        try:
            get_all_land_resources(session, token)
        except Exception as e:
            print_and_flush(f" 获取领地资源失败: {e}")
            traceback_print_and_flush_exc()

        print_and_flush("=" * 50)
        print_and_flush(" 每月签到")
        print_and_flush("=" * 50)
        try:
            auto_daily_check_in(session, token)
        except Exception as e:
            print_and_flush(f" 签到失败: {e}")
            traceback_print_and_flush_exc()
        time.sleep(1.5)
        
        # 添加周签到功能
        print_and_flush("\n" + "=" * 50)
        print_and_flush(" 每周签到")
        print_and_flush("=" * 50)
        try:
            auto_continuous_check_in(session, token)
        except Exception as e:
            print_and_flush(f" 周签到失败: {e}")
            traceback_print_and_flush_exc()
        time.sleep(1.5)

        # 添加自动同意好友申请功能
        print_and_flush("\n" + "=" * 50)
        print_and_flush("🤝 自动同意好友申请")
        print_and_flush("=" * 50)
        try:
            auto_accept_friend_requests(session, token)
        except Exception as e:
            print_and_flush(f" 处理好友申请出错: {e}")
            traceback_print_and_flush_exc()
        time.sleep(1.5)

        print_and_flush("\n" + "=" * 50)
        print_and_flush("📨 好友资源互赠")
        print_and_flush("=" * 50)
        # 自动选择默认资源进行互赠
        goodsid = DEFAULT_GOODSID
        print_and_flush(f" 自动选择资源: {GIFT_ITEMS.get(str(goodsid), '未知资源')}")
        
        if str(goodsid) in GIFT_ITEMS:
            try:
                ask_gifts_to_all_friends(session, token, goodsid)
                handle_received_ask_requests(session, token)
                receive_gifts_from_friends(session, token)
            except Exception as e:
                print_and_flush(f" 好友互赠流程出错: {e}")
                traceback_print_and_flush_exc()

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

        # 新增：邮件处理
        print_and_flush("\n" + "=" * 50)
        print_and_flush(" 邮件处理")
        print_and_flush("=" * 50)
        try:
            display_emails(session, token)
            print_and_flush("\n📎 正在领取普通邮件附件...")
            get_all_attachments(session, token)
            delete_claimed_and_expired_emails(session, token)
        except Exception as e:
            print_and_flush(f" 处理邮件失败: {e}")
            traceback_print_and_flush_exc()
        time.sleep(1)

        print_and_flush(f"\n 账号 {account_index + 1} 所有任务完成")
        
    except KeyboardInterrupt:
        print_and_flush(f"\n 用户中断账号 {account_index + 1} 程序执行")
    except Exception as e:
        print_and_flush(f"\n 账号 {account_index + 1} 程序运行过程中出现未处理的异常: {e}")
        traceback_print_and_flush_exc()

def main():
    print_and_flush(" 开始执行多账号每日任务...")
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
    print_and_flush("🎉 所有账号任务执行完毕")
    print_and_flush(f"{'='*60}")

if __name__ == "__main__":
    # 设置环境变量表示在Web环境中运行
    os.environ['RUN_IN_WEB'] = 'true'
    main()