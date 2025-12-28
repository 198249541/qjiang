# battle_controller.py
import sys
import requests
import os
import json
import traceback
from typing import Optional, Any
import io
import time
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

def print_and_flush(*args, **kwargs):
    try:
        if sys.stdout and not sys.stdout.closed:
            print(*args, **kwargs, flush=True)
    except (ValueError, OSError):
        # stdout 被关闭时忽略输出
        pass

def traceback_print_and_flush_exc():
    traceback.print_exc()
    sys.stdout.flush()

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

# 尝试导入登录模块
try:
    from login import login
    from customs_battle import customs_battle
except ImportError as e:
    print_and_flush(f"模块导入失败: {e}")
    print_and_flush("请检查所有依赖文件是否存在")
    traceback_print_and_flush_exc()
    exit(1)

def load_token_from_cache(token_file: str):
    """
    从缓存文件中加载token
    """
    try:
        if os.path.exists(token_file):
            with open(token_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                token = data.get("token")
                user_id = data.get("user_id")
                if token:
                    print_and_flush(f"✅ 从缓存加载token成功")
                    return token, user_id
    except Exception as e:
        print_and_flush(f"⚠️ 读取token缓存失败: {e}")
    return None, None

def save_token_to_cache(token_file: str, token: str, user_id: str):
    """
    将token保存到缓存文件
    """
    try:
        with open(token_file, 'w', encoding='utf-8') as f:
            json.dump({
                "token": token,
                "user_id": user_id,
                "timestamp": time.time()
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print_and_flush(f"⚠️ 保存token到缓存失败: {e}")

def ensure_session_token(session: requests.Session, tel: str, pwd: str, token_file: str):
    """
    确保 session 中有有效的 token，并返回 user_id
    """
    # 首先尝试从缓存加载token
    token, user_id = load_token_from_cache(token_file)
    if token:
        print_and_flush("🌐 使用缓存的token")
        return session, token, user_id
    
    # 如果缓存中没有token，则执行登录
    print_and_flush("🔐 正在登录...")
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
                print_and_flush("登录成功但未返回有效 user_id")
                new_user_id = None

            if new_token:
                print_and_flush(f"✅ 登录成功！")
                # 保存token到缓存
                save_token_to_cache(token_file, new_token, new_user_id)
                return session, new_token, new_user_id
            else:
                print_and_flush("❌ 登录未返回有效 token")
        else:
            print_and_flush("❌ 登录失败")
    except Exception as e:
        print_and_flush(f"❌ 登录过程出错: {e}")
        traceback_print_and_flush_exc()

    print_and_flush("❌ 无法获取 token，程序终止。")
    return session, None, None

def get_user_input():
    """
    获取用户输入的战斗配置
    返回: (difficulty, level, times)
    """
    print_and_flush("\n" + "="*50)
    print_and_flush("游戏副本设置")
    print_and_flush("="*50)
    
    # 选择难度
    print_and_flush("\n游戏副本难度选择:")
    for key, value in DIFFICULTY_MAP.items():
        print_and_flush(f"  {key}. {value}")
    
    while True:
        try:
            diff_input = input("请输入难度编号 (0-3): ").strip()
            difficulty = int(diff_input)
            if 0 <= difficulty <= 3:
                break
            else:
                print_and_flush("❌ 请输入有效的难度编号 (0-3)")
        except ValueError:
            print_and_flush("❌ 请输入有效的数字")
    
    # 选择关卡
    print_and_flush("\n游戏副本关卡选择:")
    for key, value in LEVEL_NAMES.items():
        print_and_flush(f"  {key}. {value}")
    
    while True:
        try:
            level_input = input("请输入关卡编号 (1-8): ").strip()
            level = int(level_input)
            if 1 <= level <= 8:
                break
            else:
                print_and_flush("❌ 请输入有效的关卡编号 (1-8)")
        except ValueError:
            print_and_flush("❌ 请输入有效的数字")
    
    # 输入挑战次数
    while True:
        try:
            times_input = input("请输入挑战次数 (1-1000): ").strip()
            times = int(times_input)
            if 1 <= times <= 1000:
                break
            else:
                print_and_flush("❌ 请输入有效的挑战次数 (1-1000)")
        except ValueError:
            print_and_flush("❌ 请输入有效的数字")
    
    return difficulty, level, times

def main():
    print_and_flush("游戏副本挑战控制器")
    
    # 获取用户配置
    difficulty, level, times = get_user_input()
    
    # 显示用户选择
    print_and_flush(f"\n📝 您的选择:")
    print_and_flush(f"   难度: {DIFFICULTY_MAP[difficulty]}")
    print_and_flush(f"   关卡: {LEVEL_NAMES[level]}")
    print_and_flush(f"   次数: {times}")
    
    # 确认开始
    confirm = input("\n确认开始挑战吗？(y/n): ").strip().lower()
    if confirm not in ['y', 'yes', '是']:
        print_and_flush("_challenge cancelled_")
        return
    
    try:
        # 创建一个会话
        session = requests.Session()
        print_and_flush("🌐 网络会话已创建")
        
        # 获取账号信息
        tel = input("请输入手机号: ").strip()
        pwd = input("请输入密码: ").strip()
        
        # 为该账号生成唯一的token文件名
        token_file = f"user_token_custom_{tel[-4:] if len(tel) >= 4 else tel}.json"
        
        # 登录获取token和user_id（优先使用缓存）
        session, token, user_id = ensure_session_token(session, tel, pwd, token_file)
        if not token:
            print_and_flush("❌ 无法获取登录信息，请检查登录状态")
            return
            
        print_and_flush(f"🔑 Token 已加载（前12位）：{str(token)[:12]}...")
        
        # 调用战斗函数
        customs_battle(session, token, user_id, times)
            
    except KeyboardInterrupt:
        print_and_flush("\n\n⚠️ 用户中断了挑战")
    except Exception as e:
        print_and_flush(f"\n❌ 发生错误: {e}")
        traceback_print_and_flush_exc()

if __name__ == "__main__":
    # 设置环境变量表示在Web环境中运行
    os.environ['RUN_IN_WEB'] = 'true'
    main()