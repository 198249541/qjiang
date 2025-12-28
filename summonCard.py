import re
import time
import json
import requests
from datetime import datetime
import sys
import json, sys, time

def request_input(prompt, timeout=30000):
    """发送输入请求给前端，并等待回填"""
    print(f"[INPUT_REQUEST]{json.dumps({'prompt': prompt, 'timeout': timeout, 'callback': str(time.time())}, ensure_ascii=False)}")
    sys.stdout.flush()
    return input().strip()

BASE_URL = "https://q-jiang.myprint.top/api/bas-generals"
_printed_failed_once = False

def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()
    
def _clean_str(s):
    if s is None:
        return ""
    s = str(s)
    s = s.replace('\ufeff', '')
    s = s.replace('\u200b', '')
    s = s.replace('\u00A0', ' ')
    s = ''.join(ch for ch in s if ord(ch) >= 32 or ch in '\r\n\t')
    return s.strip()


def _parse_time_to_ts(v):
    global _printed_failed_once
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            ts = int(v)
            if ts > 10**12:
                ts //= 1000
            return ts
    except Exception:
        pass
    s = _clean_str(v)
    if not s:
        return None
    if re.fullmatch(r'\d+', s):
        try:
            ts = int(s)
            if len(s) >= 13 or ts > 10**12:
                ts //= 1000
            return ts
        except Exception:
            return None
    m = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}:\d{2})', s)
    if m:
        try:
            dtstr = m.group(1).replace('/', '-')
            dt = datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S")
            return int(dt.timestamp())
        except Exception:
            pass
    s2 = s.replace('T', ' ').replace('Z', '').strip()
    if '.' in s2:
        s2 = s2.split('.')[0]
    fmts = [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s2, fmt)
            return int(dt.timestamp())
        except Exception:
            continue
    try:
        dt = datetime.fromisoformat(s2)
        return int(dt.timestamp())
    except Exception:
        pass
    if not _printed_failed_once:
        _printed_failed_once = True
        try:
            print_and_flush("⚠️ _parse_time_to_ts 无法解析 trainTime:", repr(v), type(v), len(str(v)))
        except Exception:
            print_and_flush("⚠️ _parse_time_to_ts 无法解析 trainTime，且无法打印原始值。")
    return None


def get_max_level(quality, star):
    try:
        q = int(quality)
        s = int(star)
    except Exception:
        q, s = 0, 1
    if q == 5:
        return {1: 80, 2: 90, 3: 100}.get(s, 100)
    return {0: 30, 1: 40, 2: 50, 3: 60, 4: 70}.get(q, 30)


def format_general_info(gen: dict) -> str:
    name = gen.get("name", "未知武将") or "未知武将"
    name = str(name).strip()
    try:
        star = int(gen.get("star", 0))
    except Exception:
        star = 0
    try:
        quality = int(gen.get("quality", 0))
    except Exception:
        quality = 0
    try:
        rank = int(gen.get("rank", 1))
    except Exception:
        rank = 1
    try:
        attack = int(gen.get("attack", 0))
    except Exception:
        attack = 0
    try:
        defense = int(gen.get("defense", 0))
    except Exception:
        defense = 0
    color_map = {0: "白", 1: "绿", 2: "蓝", 3: "紫", 4: "橙", 5: "红"}
    color = color_map.get(quality, "?")
    max_level = get_max_level(quality, star)
    level_text = f"{rank}/{max_level}" + (" [满]" if rank >= max_level else "")
    train_status = gen.get("trainStatus", 0)
    if train_status == 1:
        status = "训练中"
    elif gen.get("mugStatusFormat") == "守家":
        status = "守家"
    else:
        status = "空闲"
    return f"{star}★ {color}《{name}》 Lv.{level_text} 攻:{attack:,} 防:{defense:,} │ {status}"

def extract_soul(session: requests.Session, token: str, mugId: int) -> bool:
    """
    执行提魂操作
    """
    url = "https://q-jiang.myprint.top/api/bas-generals/extractSoul"
    headers = {"Token": token, "Content-Type": "application/json"}
    data = {"mugId": mugId, "code": None}
    
    try:
        response = session.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success") and str(result.get("code")) == "200":
            print_and_flush(f"✅ 提魂成功")
            return True
        else:
            print_and_flush(f"❌ 提魂失败: {result.get('msg', '未知错误')}")
            return False
    except Exception as e:
        print_and_flush(f"❌ 提魂异常: {e}")
        return False
def _extract_generals_from_response(data):
    if data is None:
        return None
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("generalList"), list):
            return data.get("generalList")
        inner = data.get("data")
        if isinstance(inner, dict) and isinstance(inner.get("generalList"), list):
            return inner.get("generalList")
    return None


def get_general_list(session: requests.Session, token: str, debug: bool = False):
    try:
        headers = {"Token": token, "Content-Type": "application/json"}
        resp = session.post(f"{BASE_URL}/index", headers=headers, json={}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if debug:
            print_and_flush(json.dumps(data, ensure_ascii=False, indent=2))
        generals = _extract_generals_from_response(data)
        if generals is None:
            code = data.get("code")
            success = data.get("success")
            if (code is not None and str(code) == "200") or (success in [True, 1, "1", "true", "True"]):
                generals = _extract_generals_from_response(data.get("data"))
        if not generals:
            nested = data.get("data") if isinstance(data, dict) else None
            if isinstance(nested, dict) and isinstance(nested.get("generalList"), list):
                generals = nested.get("generalList")
        if not generals:
            print_and_flush(f"❌ 获取失败: {data.get('msg') or '未知'}")
            return []
        for i, gen in enumerate(generals, 1):
            print_and_flush(f"{i:2d}. {format_general_info(gen)}")
        return generals
    except Exception as e:
        print_and_flush(f"⚠️ 请求/解析异常: {e}")
        return []


def can_train(gen: dict) -> bool:
    if gen.get("trainStatus") == 1:
        return False
    try:
        rank = int(gen.get("rank", 1))
        star = int(gen.get("star", 1))
        quality = int(gen.get("quality", 0))
    except Exception:
        rank, star, quality = 1, 1, 0
    return rank < get_max_level(quality, star)


def train_general(session: requests.Session, token: str, mugId, type=2, index=0):
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"mugId": mugId, "type": type, "index": index}
    for attempt in range(5):
        try:
            resp = session.post(f"{BASE_URL}/trainGeneral", headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if (str(data.get("code")) == "200") or (data.get("success") in [True, 1]):
                print_and_flush("✅ 训练请求成功")
                return True
            msg = data.get("msg", "") or str(data)
            if "系统繁忙" in msg or "请稍后重试" in msg:
                wait = 2 ** attempt
                print_and_flush(f"🔁 系统繁忙，{wait}s 后重试 ({attempt+1}/5)...")
                time.sleep(wait)
                continue
            print_and_flush(f"❌ 训练失败: {msg}")
            return False
        except requests.exceptions.RequestException as e:
            print_and_flush(f"⚠️ 网络异常: {e}，重试中... ({attempt+1}/5)")
            time.sleep(2)
        except Exception as e:
            print_and_flush(f"⚠️ 未知异常: {e}")
            time.sleep(2)
    print_and_flush("❌ 多次重试失败，放弃此次训练请求")
    return False


def finish_train(session: requests.Session, token: str, mugId):
    url = f"{BASE_URL}/finishTrain"
    headers = {"Token": token, "Content-Type": "application/json"}
    payload = {"mugId": mugId}
    try:
        resp = session.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if (str(data.get("code")) == "200") or (data.get("success") in [True, 1]):
            print_and_flush(f"✅ 收获训练成功: {data.get('msg', '')}")
            return True
        else:
            print_and_flush(f"❌ 收获训练失败: {data.get('msg', '') or data}")
    except requests.exceptions.RequestException as e:
        print_and_flush(f"⚠️ 网络异常: {e}")
    except Exception as e:
        print_and_flush(f"⚠️ 未知异常: {e}")
    return False


def show_train_slots(session: requests.Session, token: str, generals: list):
    """显示训练槽状态并自动收获已完成训练的武将"""
    train_slots = [None, None, None]  # 3个槽位
    harvested_mugids = []  # 记录已收获的武将ID
    
    for gen in generals:
        if gen.get("trainStatus") == 1:
            idx = gen.get("trainIndex", -1)
            if idx in (0, 1, 2):  # 支持0, 1, 2三个索引
                train_slots[idx] = gen

    print_and_flush("📋 训练槽状态：")
    now_ts = int(time.time())
    for idx, gen in enumerate(train_slots):
        if gen:
            raw = gen.get("trainTime", None)
            ts = _parse_time_to_ts(raw)
            if ts:
                end_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
                print_and_flush(f"  槽 {idx+1}：{gen.get('name','未知')}（{end_str} 结束）")
                if ts <= now_ts:
                    print_and_flush(f"⏳ 槽 {idx+1} 训练已结束，自动收获...")
                    # 检查是否已经尝试过收获此武将
                    mug_id = gen.get("mugId")
                    if mug_id and mug_id not in harvested_mugids:
                        if finish_train(session, token, mug_id):
                            print_and_flush(f"✅ 收获：{gen.get('name','未知')}")
                            harvested_mugids.append(mug_id)
                            train_slots[idx] = None
                        else:
                            # 收获失败，可能是已经被收获过了
                            print_and_flush(f"⚠️ 收获失败，可能已被收获：{gen.get('name','未知')}")
                            train_slots[idx] = None  # 即使失败也标记为空，避免重复尝试
                    else:
                        print_and_flush(f"⚠️ 跳过重复收获：{gen.get('name','未知')}")
                        train_slots[idx] = None
            else:
                print_and_flush(f"  槽 {idx+1}：{gen.get('name','未知')}（{raw} 结束）")
        else:
            print_and_flush(f"  槽 {idx+1}：🟢 空闲")
            
    return train_slots


def get_trainable_generals(generals: list):
    """获取可训练的武将列表"""
    trainable = []
    for i, gen in enumerate(generals):
        mugId = gen.get("mugId")
        if mugId and can_train(gen):
            trainable.append((len(trainable) + 1, i + 1, mugId, gen))
    return trainable


def auto_train_generals(session: requests.Session, token: str, generals: list, max_trains: int = 3):
    """自动训练武将，最多训练max_trains个"""
    # 显示训练槽状态并收获已完成的
    train_slots = show_train_slots(session, token, generals)
    
    # 如果收获了训练，则需要重新获取武将状态
    harvested_any = any(slot is None for slot in train_slots) if any(slot is not None for slot in train_slots) else False
    
    if harvested_any:
        print_and_flush("🔄 重新获取武将最新状态...")
        updated_generals = get_general_list(session, token)
        if updated_generals:
            generals = updated_generals
        else:
            print_and_flush("⚠️ 重新获取武将列表失败，使用原有数据")
    
    # 重新显示训练槽状态（基于更新后的数据）
    train_slots = show_train_slots(session, token, generals)
    
    # 如果三个槽位都在训练中时跳过
    if all(train_slots):
        print_and_flush("⚠️ 三个槽位均在训练中，跳过自动训练")
        return
    
    # 获取可训练武将
    trainable = get_trainable_generals(generals)
    
    if not trainable:
        print_and_flush("✅ 当前无可训练武将")
        return

    # 自动训练武将填满空闲槽位
    free_slots = sum(1 for slot in train_slots if not slot)
    trains_to_do = min(free_slots, max_trains, len(trainable))
    
    if trains_to_do <= 0:
        return
    
    print_and_flush(f"\n✅ 找到 {len(trainable)} 位可训练武将，将自动训练 {trains_to_do} 位")
    for disp_num, orig_num, mugId, gen in trainable[:trains_to_do]:
        print_and_flush(f"  {disp_num}. 【{orig_num}】{format_general_info(gen)}")
    
    free_slot_indices = [i for i, slot in enumerate(train_slots) if not slot]
    for i in range(trains_to_do):
        mugId = trainable[i][2]
        gen = trainable[i][3]
        slot_idx = free_slot_indices[i]
        print_and_flush(f"\n🔥 开始训练：{format_general_info(gen)}")
        print_and_flush(f"➡️ 放入训练槽{slot_idx+1}")
        train_general(session, token, mugId, type=2, index=slot_idx)