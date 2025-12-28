# pack.py
import requests
import sys

def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

def compose_general_card_fragments(session, token, mpg_id):
    """
    合成将卡碎片
    """
    url = "https://q-jiang.myprint.top/api/mid-user-pack/composeGoods"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }
    
    payload = {
        "mpgId": mpg_id
    }
    
    try:
        response = session.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success") and result.get("code") == "200":
            return True, result.get("msg", "合成成功")
        else:
            return False, result.get("msg", "合成失败")
    except Exception as e:
        return False, f"请求失败: {e}"

def use_item(session, token, mpg_id, goods_id, num):
    """
    使用物品接口
    """
    url = "https://q-jiang.myprint.top/api/mid-user-pack/splitGoods"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }
    
    payload = {
        "mpgId": mpg_id,
        "goodsId": goods_id,
        "num": num
    }
    
    try:
        response = session.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success") and result.get("code") == "200":
            return True, result.get("msg", "使用成功")
        else:
            return False, result.get("msg", "使用失败")
    except Exception as e:
        return False, f"请求失败: {e}"

# 在 pack.py 中添加以下函数（放在其他函数定义之后）
def auto_use_battle_card(session, token, items):
    """
    自动使用一个闯关卡
    """
    battle_cards = []
    for item in items:
        name = item.get("name", "")
        if "闯关卡" in name:
            battle_cards.append(item)
    
    if battle_cards:
        # 使用第一个找到的闯关卡
        card = battle_cards[0]
        name = card.get("name", "")
        mpg_id = card.get("mpgId", "")
        goods_id = card.get("goodsId", "")
        num = card.get("num", 0)
        
        if num > 0:
            print_and_flush(f"\n🎮 检测到 {name}，正在使用1个...")
            success, msg = use_item(session, token, mpg_id, goods_id, 1)  # 只使用1个
            if success:
                print_and_flush(f"✅ {name} 使用成功")
                return True
            else:
                print_and_flush(f"❌ {name} 使用失败: {msg}")
                return False
        else:
            print_and_flush(f"\n🎮 {name} 数量为0，无法使用")
            return False
    else:
        print_and_flush("\n🎮 未检测到闯关卡")
        return False

# 注意：不要在 get_pack_info 函数中调用 auto_use_battle_card
# 保持 get_pack_info 函数的纯净性，让它只负责获取背包信息
def auto_use_resource_packages(session, token, items):
    """
    自动使用资源包（银票包、铜钱包、军粮包、元宝包）
    """
    # 定义需要自动使用的资源包类型
    resource_packages = ["银票包", "铜钱包", "军粮包", "元宝包"]
    package_sizes = {"小": 1, "中": 2, "大": 3}
    
    # 筛选出需要自动使用的资源包
    packages_to_use = []
    for item in items:
        name = item.get("name", "")
        for package_type in resource_packages:
            if package_type in name:
                # 提取包的大小
                size = None
                for size_name in package_sizes:
                    if size_name in name:
                        size = size_name
                        break
                
                if size:
                    packages_to_use.append({
                        "item": item,
                        "type": package_type,
                        "size": size,
                        "priority": package_sizes[size]  # 大包优先使用
                    })
    
    # 按照包的大小排序，大包优先使用
    packages_to_use.sort(key=lambda x: x["priority"], reverse=True)
    
    # 自动使用这些资源包
    if packages_to_use:
        print_and_flush("\n💰 检测到资源包，尝试自动使用...")
        for package in packages_to_use:
            item = package["item"]
            name = item.get("name", "")
            mpg_id = item.get("mpgId", "")
            goods_id = item.get("goodsId", "")
            num = item.get("num", 0)
            
            print_and_flush(f"  正在使用 {name} (数量: {num})...")
            success, msg = use_item(session, token, mpg_id, goods_id, num)
            if success:
                print_and_flush(f"    ✅ {name} 使用成功")
            else:
                print_and_flush(f"    ❌ {name} 使用失败: {msg}")
    else:
        print_and_flush("\n💰 未检测到可自动使用的资源包")

def get_pack_info(session, token):
    """
    获取背包信息
    """
    url = "https://q-jiang.myprint.top/api/mid-user-pack/pack"
    headers = {
        "Token": token,
        "Content-Type": "application/json",
        "Origin": "https://q-jiang.myprint.top",
        "Referer": "https://q-jiang.myprint.top/"
    }

    try:
        print_and_flush("🔍 正在获取背包信息...")
        response = session.post(url, headers=headers, json={})
        response.raise_for_status()

        result = response.json()

        if result.get("success") and result.get("code") == "200":
            data = result.get("data", {})
            
            print_and_flush("✅ 背包信息获取成功！")
            print_and_flush("=" * 40)
            
            # 显示背包基本信息
            capacity = data.get("capacity", "未知")
            items = data.get("packGoodsVos", [])
            item_count = len(items)
            
            print_and_flush(f"背包容量: {capacity}")
            print_and_flush(f"物品种类数: {item_count}")
            
            # 显示物品列表 - 合并相同物品
            if items:
                # 收集将卡碎片用于合成
                card_fragments = []
                
                # 自动使用资源包
                auto_use_resource_packages(session, token, items)
                
                # 合并相同名称的物品
                merged_items = {}
                for item in items:
                    name = item.get("name", "未知物品")
                    count = item.get("num", 0)
                    quality = item.get("quality", 0)
                    
                    # 收集将卡碎片
                    if "将卡碎片" in name:
                        card_fragments.append(item)
                    
                    if name in merged_items:
                        merged_items[name]["num"] += count
                    else:
                        merged_items[name] = {
                            "name": name,
                            "num": count,
                            "quality": quality
                        }
                
                # 自动合成将卡碎片 - 仅当数量满足要求时才合成
                if card_fragments:
                    print_and_flush("\n🔄 检测到将卡碎片，尝试自动合成...")
                    for fragment in card_fragments:
                        fragment_name = fragment.get("name", "")
                        fragment_count = fragment.get("num", 0)
                        mpg_id = fragment.get("mpgId", "")
                        
                        if fragment_count >= 4:  # 仅当数量满足4个时才合成
                            synthesis_count = fragment_count // 4
                            print_and_flush(f"  尝试合成 {fragment_name}: {synthesis_count}次")
                            success, msg = compose_general_card_fragments(session, token, mpg_id)
                            if success:
                                print_and_flush(f"    ✅ {fragment_name} 合成成功")
                            else:
                                print_and_flush(f"    ❌ {fragment_name} 合成失败: {msg}")
                        else:
                            print_and_flush(f"  {fragment_name}: 数量不足(需要4个，当前{fragment_count}个)")
                
                # 分类物品
                equipment_fragments = []  # 装备碎片
                forge_blueprints = []     # 锻造图纸
                skills = []               # 技能
                general_cards = []        # 将卡/将卡碎片
                general_souls = []        # 将魂
                materials = []            # 材料
                event_materials = []      # 活动材料
                others = []               # 其他
                
                for item_data in merged_items.values():
                    name = item_data["name"]
                    # 根据名称特征分类
                    if "碎片" in name:
                        if "将卡碎片" in name:
                            general_cards.append(item_data)
                        else:
                            equipment_fragments.append(item_data)
                    elif "图" in name and len(name) in [4, 5]:  # XXXX图或XXXX图纸
                        forge_blueprints.append(item_data)
                    elif len(name) in [4, 5] and not ("图" in name):  # 四个字的技能
                        skills.append(item_data)
                    elif "冬之魂" in name:  # 冬之魂归属活动材料（调整顺序，优先判断）
                        event_materials.append(item_data)
                    elif "将卡" in name or ("【" in name and "】" in name and ("卡" in name or any(char in name for char in "山林风火水金"))):
                        # 将卡包括：直接包含"将卡"的，或者包含【】且有特定后缀的（如花荣【山】等）
                        general_cards.append(item_data)
                    elif "武魂" in name:  # 将魂
                        general_souls.append(item_data)
                    elif name in ["绢布", "木材", "石材", "陶土", "铁矿", "金刚石", "玄铁", "玛瑙", "红宝石"]:
                        materials.append(item_data)
                    else:
                        others.append(item_data)
                
                # 显示分类物品列表
                print_and_flush("\n🎒 背包物品列表:")
                
                # 按品质排序的函数
                def sort_by_quality(items):
                    return sorted(items, key=lambda x: x.get("quality", 0) or 0, reverse=True)
                
                # 显示各类物品
                if equipment_fragments:
                    print_and_flush("\n🟡 装备碎片:")
                    for i, item in enumerate(sort_by_quality(equipment_fragments), 1):
                        quality = item.get("quality", 0) or 0
                        quality_colors = {
                            0: "", 1: "🟢", 2: "🔵", 3: "🟣", 4: "🟠", 
                            5: "🔴", 6: "🟡", 7: "🌈"
                        }
                        color_icon = quality_colors.get(quality, "")
                        print_and_flush(f"  {i:2d}. {color_icon} {item['name']}: {item['num']}个")
                
                if forge_blueprints:
                    print_and_flush("\n🔨 锻造图纸:")
                    for i, item in enumerate(sort_by_quality(forge_blueprints), 1):
                        quality = item.get("quality", 0) or 0
                        quality_colors = {
                            0: "", 1: "🟢", 2: "🔵", 3: "🟣", 4: "🟠", 
                            5: "🔴", 6: "🟡", 7: "🌈"
                        }
                        color_icon = quality_colors.get(quality, "")
                        print_and_flush(f"  {i:2d}. {color_icon} {item['name']}: {item['num']}个")
                
                if skills:
                    print_and_flush("\n⚔️ 技能:")
                    for i, item in enumerate(sort_by_quality(skills), 1):
                        quality = item.get("quality", 0) or 0
                        quality_colors = {
                            0: "", 1: "🟢", 2: "🔵", 3: "🟣", 4: "🟠", 
                            5: "🔴", 6: "🟡", 7: "🌈"
                        }
                        color_icon = quality_colors.get(quality, "")
                        print_and_flush(f"  {i:2d}. {color_icon} {item['name']}: {item['num']}个")
                
                if general_cards:
                    print_and_flush("\n👤 将卡/将卡碎片:")
                    for i, item in enumerate(sort_by_quality(general_cards), 1):
                        quality = item.get("quality", 0) or 0
                        quality_colors = {
                            0: "", 1: "🟢", 2: "🔵", 3: "🟣", 4: "🟠", 
                            5: "🔴", 6: "🟡", 7: "🌈"
                        }
                        color_icon = quality_colors.get(quality, "")
                        print_and_flush(f"  {i:2d}. {color_icon} {item['name']}: {item['num']}个")
                
                if general_souls:
                    print_and_flush("\n👻 将魂:")
                    for i, item in enumerate(sort_by_quality(general_souls), 1):
                        quality = item.get("quality", 0) or 0
                        quality_colors = {
                            0: "", 1: "🟢", 2: "🔵", 3: "🟣", 4: "🟠", 
                            5: "🔴", 6: "🟡", 7: "🌈"
                        }
                        color_icon = quality_colors.get(quality, "")
                        print_and_flush(f"  {i:2d}. {color_icon} {item['name']}: {item['num']}个")
                
                if event_materials:
                    print_and_flush("\n🎉 活动材料:")
                    for i, item in enumerate(sort_by_quality(event_materials), 1):
                        quality = item.get("quality", 0) or 0
                        quality_colors = {
                            0: "", 1: "🟢", 2: "🔵", 3: "🟣", 4: "🟠", 
                            5: "🔴", 6: "🟡", 7: "🌈"
                        }
                        color_icon = quality_colors.get(quality, "")
                        print_and_flush(f"  {i:2d}. {color_icon} {item['name']}: {item['num']}个")
                
                if materials:
                    print_and_flush("\n🪨 材料:")
                    for i, item in enumerate(sort_by_quality(materials), 1):
                        quality = item.get("quality", 0) or 0
                        quality_colors = {
                            0: "", 1: "🟢", 2: "🔵", 3: "🟣", 4: "🟠", 
                            5: "🔴", 6: "🟡", 7: "🌈"
                        }
                        color_icon = quality_colors.get(quality, "")
                        print_and_flush(f"  {i:2d}. {color_icon} {item['name']}: {item['num']}个")
                
                if others:
                    print_and_flush("\n📦 其他:")
                    for i, item in enumerate(sort_by_quality(others), 1):
                        quality = item.get("quality", 0) or 0
                        quality_colors = {
                            0: "", 1: "🟢", 2: "🔵", 3: "🟣", 4: "🟠", 
                            5: "🔴", 6: "🟡", 7: "🌈"
                        }
                        color_icon = quality_colors.get(quality, "")
                        print_and_flush(f"  {i:2d}. {color_icon} {item['name']}: {item['num']}个")
                
            else:
                print_and_flush("\n🎒 背包为空")
            
            print_and_flush("=" * 40)
            return data

        else:
            msg = result.get("msg", "未知错误")
            print_and_flush(f"❌ 接口返回失败: {msg}")
            return None

    except Exception as e:
        print_and_flush(f"❌ 请求背包信息失败: {e}")
        return None