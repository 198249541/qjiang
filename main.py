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
import argparse

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

# ========== 配置区 ========== 
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


# 多账号配置 - 从 accounts.json 文件读取
def load_accounts_from_file():
    """从 accounts.json 文件加载账号配置"""
    accounts_file = 'accounts.json'
    try:
        if os.path.exists(accounts_file):
            # 明确使用UTF-8编码读取文件
            with open(accounts_file, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
                # 确保账号格式正确，只保留 tel 和 pwd 字段
                formatted_accounts = []
                for account in accounts:
                    if 'tel' in account and 'pwd' in account:
                        formatted_accounts.append({
                            'tel': str(account['tel']),
                            'pwd': str(account['pwd'])
                        })
                print_and_flush(f" 从 {accounts_file} 加载了 {len(formatted_accounts)} 个账号")
                return formatted_accounts
        else:
            print_and_flush(f" 账号配置文件 {accounts_file} 不存在")
    except Exception as e:
        print_and_flush(f" 读取账号配置文件出错: {e}")
        traceback_print_and_flush_exc()
    
    # 如果文件不存在或读取失败，返回空列表
    print_and_flush(" 使用空的账号配置")
    return []

# 加载账号配置
ACCOUNTS = load_accounts_from_file()

TOKEN_FILES = [f"user_token_{i+1}.json" for i in range(len(ACCOUNTS))]  # 为每个账号创建独立的token文件
GIFT_ITEMS = {47: "绢布", 48: "木材", 49: "石材", 50: "陶土", 51: "铁矿"}
AUTO_MODE = True
DEFAULT_GOODSID = 49
FRIEND_LIST_URL = "https://q-jiang.myprint.top/api/user/friendList"
INPUT_TIMEOUT = 10  # 输入超时时间（秒）
# ===========================

print_and_flush(" 程序初始化中...")  # 添加初始化提示

# 其余代码保持不变...
try:
    print_and_flush(" 正在加载模块...")
    from login import login

    # 修改：导入完整的领地资源函数
    from landResources import get_re_list, get_occupy_resource_list, get_all_land_resources
    
    from generalCard import get_pub_general_list, recruit_general, format_general_info
    
    from summonCard import get_general_list, show_train_slots_and_choose
    
    from market import get_market_info
    
    # 修复：移除 show_my_give_list 的导入
    from gift import ask_gifts_to_all_friends, handle_received_ask_requests, receive_gifts_from_friends
    
    from sign_in import auto_daily_check_in
    
    from home_copper import collect_home_copper
    
    from customs_battle import customs_battle
    
    from daily_tasks import display_daily_tasks, claim_all_available_rewards
    
    from email_manager import display_emails, process_all_customs_emails, get_all_attachments, delete_claimed_and_expired_emails  
    
    # 添加好友相关功能导入
    from friend import auto_accept_friend_requests
    
except ImportError as e:
    print_and_flush(f" 模块导入失败: {e}")
    print_and_flush("请检查所有依赖文件是否存在")
    traceback_print_and_flush_exc()
    exit(1)

def request_user_input(prompt, timeout=INPUT_TIMEOUT):
    """
    请求用户输入的函数，适用于Web环境
    """
    # 生成唯一的请求ID
    request_id = str(time.time())
    
    # 输出特殊标记，前端会识别并显示输入区域
    input_request = {
        'prompt': prompt,
        
        
    }
    
    print_and_flush(f"[INPUT_REQUEST]{json.dumps(input_request, ensure_ascii=False)}")
    
    # 等待用户输入（在Web环境中由后端处理）
    try:
        user_input = input()  # 这将等待后端通过stdin传递输入
        return user_input
    except:
        print_and_flush(f"\n⏱️  输入超时（{timeout}秒），使用默认选项")
        return None

def input_with_timeout(prompt, timeout=INPUT_TIMEOUT):
    """
    带超时的输入函数
    在Web环境中使用request_user_input，在命令行环境中使用原有逻辑
    """
    # 检查是否在Web环境中运行（通过环境变量判断）
    if os.environ.get('RUN_IN_WEB', 'false').lower() == 'true':
        return request_user_input(prompt, timeout)
    
    # 原有的命令行环境逻辑
    result = [None]
    input_thread = None
    
    def get_input():
        try:
            result[0] = input(prompt)
        except:
            pass
    
    input_thread = threading.Thread(target=get_input)
    input_thread.daemon = True
    input_thread.start()
    input_thread.join(timeout)
    
    if input_thread.is_alive():
        print_and_flush(f"\n⏱️  输入超时（{timeout}秒），使用默认选项")
        return None
    else:
        return result[0]

def load_token_from_file(path: str) -> (Optional[str], Optional[Any]):
    """
    从本地文件读取 token 和 user_id
    """
    print_and_flush(f"📂 正在读取token文件: {path}")
    try:
        if os.path.exists(path):
            # 明确使用UTF-8编码读取文件
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                token = data.get("token")
                user_id = data.get("user_id")
                if isinstance(token, str) and token.strip():
                    print_and_flush(" Token文件读取成功")
                    return token, user_id
                else:
                    print_and_flush(" token 文件存在但内容无效")
        else:
            print_and_flush(" token 文件不存在")
    except json.JSONDecodeError as e:
        print_and_flush(f" 读取 token 文件失败（JSON 格式错误）: {e}")
    except Exception as e:
        print_and_flush(f" 读取 token 文件失败: {e}")
    return None, None

def save_token_to_file(token: Any, user_id: Any, path: str):
    """
    保存 token 和 user_id
    """
    print_and_flush(f"💾 正在保存token到文件: {path}")
    try:
        safe_token = str(token) if token is not None else ""
        safe_user_id = user_id if isinstance(user_id, (str, int, type(None))) else str(user_id)

        # 明确使用UTF-8编码写入文件
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"token": safe_token, "user_id": safe_user_id}, f, ensure_ascii=False, indent=2)

        print_and_flush(" Token 已保存到文件")
    except Exception as e:
        print_and_flush(f" 保存 token 失败: {e}")

def is_token_alive(session: requests.Session, token: str) -> bool:
    print_and_flush(" 正在验证token有效性...")
    try:
        response = session.post(FRIEND_LIST_URL, headers={"Token": token}, timeout=8)
        response.raise_for_status()
        result = response.json()
        is_valid = str(result.get("code")) == "200" or result.get("success") in (True, "true", "1", 1, "True")
        print_and_flush(f"{'' if is_valid else ''} Token有效性检查: {'有效' if is_valid else '无效'}")
        return is_valid
    except Exception as e:
        print_and_flush(f" Token验证异常: {e}")
        return False

def ensure_session_token(session: requests.Session, tel: str, pwd: str, token_file: str):
    """
    确保 session 中有有效的 token，并返回 user_id
    """
    print_and_flush(" 正在获取有效token...")
    token, user_id = load_token_from_file(token_file)
    if token and user_id and is_token_alive(session, token):
        print_and_flush(" 本地 token 有效，直接使用")
        return session, token, user_id

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

            if new_token and is_token_alive(session, new_token):
                save_token_to_file(new_token, new_user_id, token_file)
                print_and_flush(f" 登录成功！欢迎 {new_user_id}！")
                return session, new_token, new_user_id
            else:
                print_and_flush(" 登录返回的 token 无效")
        else:
            print_and_flush(" 登录失败，未返回有效结果")
    except Exception as e:
        print_and_flush(f" 登录过程出错: {e}")
        traceback_print_and_flush_exc()

    print_and_flush(" 无法获取有效 token，程序终止。")
    return session, None, None

def do_train_general(session: requests.Session, token: str):
    print_and_flush("\n" + "=" * 50)
    print_and_flush(" 正在准备训练点将台武将...")
    print_and_flush("=" * 50)

    try:
        generals = get_general_list(session, token, debug=False)
    except Exception as e:
        print_and_flush(f" 获取武将列表出错: {e}")
        traceback_print_and_flush_exc()
        generals = []

    if not generals:
        print_and_flush(" 无法获取武将列表，跳过训练。")
        return

    try:
        show_train_slots_and_choose(session, token, generals, auto=False)
    except Exception as e:
        print_and_flush(f" 训练武将出错: {e}")
        traceback_print_and_flush_exc()

def run_account_tasks(account_index: int, tel: str, pwd: str, token_file: str):
    """
    为单个账号运行所有任务
    """
    # print_and_flush(f"\n{'='*60}")
    # print_and_flush(f"📱 账号 {account_index + 1} 任务开始")
    # print_and_flush(f"📱 手机号: {tel}")
    # print_and_flush(f"{'='*60}")
    
    try:
        session = requests.Session()
        print_and_flush("🌐 网络会话已创建")
        session, token, user_id = ensure_session_token(session, tel, pwd, token_file)
        if not token:
            print_and_flush(" 无法获取有效token，跳过此账号")
            return

        print_and_flush(f" Token 已加载（前12位）：{str(token)[:12]}...")
        print_and_flush("-" * 50)

        try:
            pub_list = get_pub_general_list(session, token)
        except Exception as e:
            print_and_flush(f" 获取酒馆列表失败: {e}")
            traceback_print_and_flush_exc()
            pub_list = None

        if pub_list:
            recruits = [(i + 1, g.get("id"), format_general_info(g)) for i, g in enumerate(pub_list) if g.get("id")]
            if recruits:
                user_input = input_with_timeout("招募？(y/n): ", INPUT_TIMEOUT)
                if user_input and user_input.strip().lower() == 'y':
                    for n, _, info in recruits:
                        print_and_flush(f"  {n}. {info}")
                    try:
                        sel_input = input_with_timeout(f"选 (1-{len(recruits)}): ", INPUT_TIMEOUT)
                        if sel_input:
                            sel = int(sel_input) - 1
                            if 0 <= sel < len(recruits):
                                _, mid, info = recruits[sel]
                                print_and_flush(f" 招募：{info}")
                                recruit_general(session, token, mup_id=mid)
                    except Exception:
                        print_and_flush(" 招募输入无效或取消")

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

        do_train_general(session, token)
        time.sleep(1.5)

        print_and_flush("=" * 50)
        print_and_flush(" 每月签到")
        print_and_flush("=" * 50)
        try:
            auto_daily_check_in(session, token)
        except Exception as e:
            print_and_flush(f" 签到失败: {e}")
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
        if AUTO_MODE:
            goodsid = DEFAULT_GOODSID
            print_and_flush(f" 自动选择资源: {GIFT_ITEMS.get(goodsid, '未知资源')}")
        else:
            print_and_flush("可选资源:")
            for gid, gname in GIFT_ITEMS.items():
                print_and_flush(f"  {gid}: {gname}")
            goods_input = input_with_timeout(f"请选择资源编号 (默认为{DEFAULT_GOODSID}): ", INPUT_TIMEOUT)
            if goods_input:
                try:
                    goodsid = int(goods_input)
                except ValueError:
                    goodsid = DEFAULT_GOODSID
                    print_and_flush(f" 输入无效，使用默认资源: {GIFT_ITEMS.get(goodsid, '未知资源')}")
            else:
                goodsid = DEFAULT_GOODSID
                print_and_flush(f"⏱ 超时，使用默认资源: {GIFT_ITEMS.get(goodsid, '未知资源')}")
        
        if goodsid in GIFT_ITEMS:
            try:
                ask_gifts_to_all_friends(session, token, goodsid)
                handle_received_ask_requests(session, token)
                receive_gifts_from_friends(session, token)
                # 不再调用 show_my_give_list
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

        # 修改部分：询问用户是否需要刷关
        print_and_flush("\n" + "=" * 50)
        print_and_flush(" 自定义关卡战斗")
        print_and_flush("=" * 50)
        # 询问用户是否要进行关卡挑战
        battle_input = input_with_timeout("是否进行关卡挑战？(y/n): ", INPUT_TIMEOUT)
        if battle_input and battle_input.strip().lower() == 'y':
            try:
                customs_battle(session, token, user_id)
            except Exception as e:
                print_and_flush(f" 关卡战斗出错: {e}")
                traceback_print_and_flush_exc()
        else:
            print_and_flush("⏭ 已跳过关卡挑战。")

        # 新增：邮件处理
        print_and_flush("\n" + "=" * 50)
        print_and_flush(" 邮件处理")
        print_and_flush("=" * 50)
        try:
            display_emails(session, token)
            print_and_flush("\n 正在处理关卡抽奖邮件...")
            process_all_customs_emails(session, token)
            print_and_flush("\n📎 正在领取普通邮件附件...")
            get_all_attachments(session, token)
            #print_and_flush("\n 正在删除已领取和过期邮件...")
            delete_claimed_and_expired_emails(session, token)
        except Exception as e:
            print_and_flush(f" 处理邮件失败: {e}")
            traceback_print_and_flush_exc()
        time.sleep(1)

        # 新增：显示日常任务并自动领取奖励（移到最后执行）
        print_and_flush("\n" + "=" * 50)
        print_and_flush(" 日常任务")
        print_and_flush("=" * 50)
        try:
            display_daily_tasks(session, token)
            print_and_flush("\n📥 正在自动领取可领取的任务奖励...")
            claim_all_available_rewards(session, token)
        except Exception as e:
            print_and_flush(f" 处理日常任务失败: {e}")
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