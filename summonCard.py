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


def train_general(session: requests.Session, token: str, mugId, type=1, index=0):
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


def show_train_slots_and_choose(session: requests.Session, token: str, generals: list, auto: bool = False):
    train_slots = [None, None]
    for gen in generals:
        if gen.get("trainStatus") == 1:
            idx = gen.get("trainIndex", -1)
            if idx in (0, 1):
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
                    if finish_train(session, token, gen.get("mugId")):
                        print_and_flush(f"✅ 收获：{gen.get('name','未知')}")
                        train_slots[idx] = None
            else:
                print_and_flush(f"  槽 {idx+1}：{gen.get('name','未知')}（{raw} 结束）")
        else:
            print_and_flush(f"  槽 {idx+1}：🟢 空闲")

    # 如果两个槽位都在训练中时跳过用户输入
    if all(train_slots):
        print_and_flush("⚠️ 两个槽位均在训练中，跳过用户输入")
        return None  # 直接返回，调用处可根据 None 判断是否跳过

    # 收集可训练武将
    trainable = []
    for i, gen in enumerate(generals):
        mugId = gen.get("mugId")
        if mugId and can_train(gen):
            trainable.append((len(trainable) + 1, i + 1, mugId, gen))

    if not trainable:
        print_and_flush("✅ 当前无可训练武将")
        return

    # 自动模式
    if auto:
        for idx in range(2):
            if not train_slots[idx] and trainable:
                mugId = trainable.pop(0)[2]
                print_and_flush(f"➡️ 自动：将武将放入训练槽{idx+1}")
                train_general(session, token, mugId, type=1, index=idx)
        return

    # 手动模式 - 允许用户连续选择多个武将填满空闲槽位
    free_slots = sum(1 for slot in train_slots if not slot)
    if free_slots == 0:
        return  # 没有空闲槽位
    
    print_and_flush(f"\n✅ 找到 {len(trainable)} 位可训练武将：")
    for disp_num, orig_num, mugId, gen in trainable:
        print_and_flush(f"  {disp_num}. 【{orig_num}】{format_general_info(gen)}")
    
    print_and_flush(f"\n💡 当前有 {free_slots} 个空闲槽位")
    
    selected_generals = []
    for i in range(free_slots):
        while True:
            user_input = request_input(f"\n💡 输入编号 (1~{len(trainable)}) 选择第{i+1}个武将，回车跳过剩余槽位: ")
            if not user_input or user_input.strip() == "":
                print_and_flush("⏭️ 已跳过剩余槽位。")
                break
            
            try:
                sel = int(user_input.strip())
                target = None
                for dnum, onum, mugId, gen in trainable:
                    if dnum == sel:
                        target = (mugId, gen)
                        break
                if not target:
                    print_and_flush(f"❌ 编号 {sel} 无效，请重新输入")
                    continue
                selected_generals.append(target)
                # 从可训练列表中移除已选择的武将，避免重复选择
                trainable = [item for item in trainable if item[2] != target[0]]
                break
            except ValueError:
                print_and_flush("❌ 输入无效，请输入数字")
        
        if not user_input or user_input.strip() == "":  # 用户选择跳过
            break
    
    # 将选中的武将放入空闲槽位
    free_slot_indices = [i for i, slot in enumerate(train_slots) if not slot]
    for i, (mugId, gen) in enumerate(selected_generals):
        if i < len(free_slot_indices):
            slot_idx = free_slot_indices[i]
            print_and_flush(f"\n🔥 开始训练：{format_general_info(gen)}")
            print_and_flush(f"➡️ 放入训练槽{slot_idx+1}")
            train_general(session, token, mugId, type=1, index=slot_idx)