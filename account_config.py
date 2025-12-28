# config_generator.py
import json
import os

def print_welcome():
    """打印欢迎信息"""
    print("="*60)
    print("           配置文件生成器")
    print("           Config Generator")
    print("="*60)
    print("这个工具将帮助您创建 config.json 配置文件")
    print("请按照提示输入相应的配置信息")
    print("-"*60)

def get_accounts_config():
    """获取账号配置"""
    print("\n📝 配置账号信息")
    print("请输入账号信息，输入完成后输入 'done' 结束")
    
    accounts = []
    account_num = 1
    
    while True:
        print(f"\n--- 账号 {account_num} ---")
        tel = input("手机号或邮箱 (输入 'done' 结束): ").strip()
        
        if tel.lower() == 'done':
            break
            
        pwd = input("密码: ").strip()
        
        # 询问是否为此账号配置个性化设置
        custom_config = input("是否为此账号配置个性化设置? (y/n): ").strip().lower()
        
        account_config = {
            "tel": tel,
            "pwd": pwd
        }
        
        if custom_config == 'y':
            config = {}
            
            # 默认互赠资源ID
            print("\n资源ID对应表:")
            print("47: 绢布, 48: 木材, 49: 石材, 50: 陶土, 51: 铁矿")
            default_goodsid = input("默认互赠资源ID (47-51, 默认51): ").strip()
            if default_goodsid:
                try:
                    config["default_goodsid"] = int(default_goodsid)
                except ValueError:
                    config["default_goodsid"] = 51
            else:
                config["default_goodsid"] = 51
            
            # 擂台兑换设置
            enable_arena = input("是否开启擂台物品兑换? (y/n, 默认y): ").strip().lower()
            config["enable_arena_exchange"] = enable_arena != 'n'
            
            if config["enable_arena_exchange"]:
                print("\n擂台兑换优先级设置 (输入物品ID)")
                print("擂台兑换物品参考:")
                print("  45: 金刚石 (1000积分)")
                print("  46: 玄铁 (1000积分)")
                print("  54: 附魔石 (15000积分)")
                print("  56: 蓝武魂 (1500积分)")
                print("  57: 紫武魂 (15000积分)")
                print("  65: 紫将卡 (80000积分)")
                print("  67: 传奇卡 (250000积分)")
                
                arena_priority = []
                priority_num = 1
                
                while True:
                    print(f"\n优先级 {priority_num} (输入 'done' 结束):")
                    item_id = input("物品ID: ").strip()
                    if item_id.lower() == 'done':
                        break
                    try:
                        item_id = int(item_id)
                        
                        # 根据物品ID自动填写物品信息
                        item_info = {
                            45: {"name": "金刚石", "points": 1000},
                            46: {"name": "玄铁", "points": 1000},
                            54: {"name": "附魔石", "points": 15000},
                            56: {"name": "蓝武魂", "points": 1500},
                            57: {"name": "紫武魂", "points": 15000},
                            65: {"name": "紫将卡", "points": 80000},
                            67: {"name": "传奇卡", "points": 250000}
                        }
                        
                        if item_id in item_info:
                            item_name = item_info[item_id]["name"]
                            item_points = item_info[item_id]["points"]
                        else:
                            # 如果ID不在预定义列表中，询问用户
                            item_name = input(f"物品名称 (ID {item_id}): ").strip() or f"物品{item_id}"
                            item_points = int(input(f"兑换所需积分: ").strip() or 1500)
                        
                        arena_priority.append({
                            "id": item_id,
                            "name": item_name,
                            "points": item_points
                        })
                        print(f"  已添加: {item_name} (所需积分: {item_points})")
                        priority_num += 1
                    except ValueError:
                        print("输入格式错误，请重新输入")
                        continue
                
                if arena_priority:
                    config["arena_exchange_priority"] = arena_priority
                else:
                    config["arena_exchange_priority"] = [
                        {"id": 56, "name": "蓝武魂", "points": 1500}
                    ]
            
                            # 资源占领目标配比
                print("\n资源占领目标配比设置:")
                print("资源类型说明：")
                print("- 农田：产出军粮")
                print("- 森林：产出木材/金刚石")
                print("- 草原：产出铜钱")
                print("- 山丘：产出武将卡")
                print("- 沼泽：产出宝石")

                # 提示用户关于资源总数限制
                print("\n⚠️  注意：资源总数最大为9个，当任意数之和达到9时将自动跳过后续输入")

                # 显示提示信息，不询问用户
                print("\nℹ️  提示：请输入真实可占领领地数量，否则会导致程序错误")
                农田 = input("农田目标数量 (默认9): ").strip()
                森林 = input("森林目标数量 (默认0): ").strip()
                            
            # 计算已占用资源数
            total_occupied = 0
            if 农田:
                try:
                    total_occupied += int(农田)
                except ValueError:
                    total_occupied = 9  # 默认值
            else:
                total_occupied = 9  # 默认值
                
            if 森林:
                try:
                    total_occupied += int(森林)
                except ValueError:
                    pass  # 默认为0
            else:
                total_occupied += 0  # 默认为0
            
            # 检查是否已达到最大值
            if total_occupied >= 9:
                print(f"⚠️  已占用资源数达到或超过最大值9，草原、山丘、沼泽数量将自动设为0")
                草原 = "0"
                山丘 = "0"
                沼泽 = "0"
            else:
                remaining = 9 - total_occupied
                print(f"📊 剩余可分配资源数: {remaining}")
                草原 = input(f"草原目标数量 (默认0, 最大{remaining}): ").strip()
                
                # 重新计算已占用资源数
                total_occupied = 0
                if 农田:
                    try:
                        total_occupied += int(农田)
                    except ValueError:
                        total_occupied = 9
                else:
                    total_occupied = 9
                    
                if 森林:
                    try:
                        total_occupied += int(森林)
                    except ValueError:
                        pass
                else:
                    total_occupied += 0
                    
                if 草原:
                    try:
                        total_occupied += int(草原)
                    except ValueError:
                        pass
                else:
                    total_occupied += 0
                
                if total_occupied >= 9:
                    print(f"⚠️  已占用资源数达到或超过最大值9，山丘、沼泽数量将自动设为0")
                    山丘 = "0"
                    沼泽 = "0"
                else:
                    remaining = 9 - total_occupied
                    print(f"📊 剩余可分配资源数: {remaining}")
                    山丘 = input(f"山丘目标数量 (默认0, 最大{remaining}): ").strip()
                    
                    # 重新计算已占用资源数
                    total_occupied = 0
                    if 农田:
                        try:
                            total_occupied += int(农田)
                        except ValueError:
                            total_occupied = 9
                    else:
                        total_occupied = 9
                        
                    if 森林:
                        try:
                            total_occupied += int(森林)
                        except ValueError:
                            pass
                    else:
                        total_occupied += 0
                        
                    if 草原:
                        try:
                            total_occupied += int(草原)
                        except ValueError:
                            pass
                    else:
                        total_occupied += 0
                        
                    if 山丘:
                        try:
                            total_occupied += int(山丘)
                        except ValueError:
                            pass
                    else:
                        total_occupied += 0
                    
                    if total_occupied >= 9:
                        print(f"⚠️  已占用资源数达到或超过最大值9，沼泽数量将自动设为0")
                        沼泽 = "0"
                    else:
                        remaining = 9 - total_occupied
                        print(f"📊 剩余可分配资源数: {remaining}")
                        沼泽 = input(f"沼泽目标数量 (默认0, 最大{remaining}): ").strip()
            
            config["target_resource_distribution"] = {
                "农田": int(农田) if 农田 else 9,
                "森林": int(森林) if 森林 else 0,
                "草原": int(草原) if 草原 else 0,
                "山丘": int(山丘) if 山丘 else 0,
                "沼泽": int(沼泽) if 沼泽 else 0
            }
            
            # 最大训练槽位数
            max_train = input("最大训练槽位数 (默认3): ").strip()
            config["max_train_slots"] = int(max_train) if max_train else 3
            
            # 闯关设置
            print("\n闯关设置:")
            difficulty_map = {0: "普通", 1: "英雄", 2: "烈焰", 3: "地狱"}
            print("难度: 0-普通, 1-英雄, 2-烈焰, 3-地狱")
            difficulty = input("难度 (0-3, 默认3地狱): ").strip()
            level_map = {1: "阳谷县", 2: "快活林", 3: "鸳鸯楼", 4: "清风寨", 
                        5: "江州城", 6: "祝家庄", 7: "大名府", 8: "汴梁城"}
            print("关卡: 1-阳谷县, 2-快活林, 3-鸳鸯楼, 4-清风寨, 5-江州城, 6-祝家庄, 7-大名府, 8-汴梁城")
            level = input("关卡 (1-8, 默认8汴梁城): ").strip()
            times = input("挑战次数 (默认10): ").strip()
            
            config["customs_battle_settings"] = {
                "difficulty": int(difficulty) if difficulty else 3,
                "level": int(level) if level else 8,
                "times": int(times) if times else 10
            }
            
            account_config["config"] = config
        
        accounts.append(account_config)
        account_num += 1
    
    return accounts

def get_global_config():
    """获取全局配置"""
    print("\n🌐 配置全局设置")
    
    # 礼物项目
    gift_items = {
        "47": "绢布",
        "48": "木材", 
        "49": "石材",
        "50": "陶土", 
        "51": "铁矿"
    }
    
    # 自动模式
    auto_mode_input = input("是否启用自动模式? (y/n, 默认y): ").strip().lower()
    auto_mode = auto_mode_input != 'n'
    
    # 输入超时时间
    timeout_input = input("输入超时时间（秒，默认10）: ").strip()
    input_timeout = int(timeout_input) if timeout_input else 10
    
    return {
        "gift_items": gift_items,
        "auto_mode": auto_mode,
        "input_timeout": input_timeout
    }

def save_config(config, filename="config.json"):
    """保存配置到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 配置文件已保存到: {filename}")
        return True
    except Exception as e:
        print(f"\n❌ 保存配置文件失败: {e}")
        return False

def main():
    """主函数"""
    print_welcome()
    
    # 获取账号配置
    accounts = get_accounts_config()
    
    if not accounts:
        print("\n❌ 没有配置任何账号，程序退出")
        return
    
    # 提示用户输入完成后按回车
    input("\n账号输入完成，按回车键继续保存配置...")
    
    # 获取全局配置
    global_config = get_global_config()
    
    # 合并配置
    config = {
        "accounts": accounts
    }
    config.update(global_config)
    
    # 显示最终配置（部分）
    print("\n📋 最终配置预览:")
    print(f"账号数量: {len(config['accounts'])}")
    print(f"自动模式: {config['auto_mode']}")
    print(f"输入超时: {config['input_timeout']}秒")
    
    # 直接保存配置，不再询问文件名
    if save_config(config):  # 直接调用，使用默认文件名
        print(f"\n🎉 配置文件生成成功！")
        print(f"文件位置: {os.path.abspath('config.json')}")
    else:
        print("\n❌ 配置文件保存失败")

def save_config(config, filename="config.json"):  # 默认参数已设置为config.json
    """保存配置到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 配置文件已保存到: {filename}")
        return True
    except Exception as e:
        print(f"\n❌ 保存配置文件失败: {e}")
        return False

if __name__ == "__main__":
    main()