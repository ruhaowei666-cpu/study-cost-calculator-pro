"""
功能测试脚本

测试所有商业化功能
"""

import sys
from database import Database
from auth import hash_password, verify_password, register_user, authenticate_user
from subscription import SubscriptionManager
from stats import StatsManager

def test_database():
    """测试数据库功能"""
    print("=" * 50)
    print("测试数据库功能")
    print("=" * 50)
    
    db = Database()
    print(f"✅ 数据库类型: {db.db_type}")
    print(f"✅ 数据库初始化成功")
    
    # 测试创建用户
    test_email = "test@example.com"
    password_hash = hash_password("test123")
    user_id = db.create_user(test_email, password_hash)
    
    if user_id:
        print(f"✅ 创建用户成功: ID={user_id}")
    else:
        print("⚠️ 用户可能已存在")
        user = db.get_user_by_email(test_email)
        if user:
            user_id = user['id']
            print(f"✅ 获取现有用户: ID={user_id}")
    
    # 测试获取用户
    user = db.get_user_by_id(user_id)
    if user:
        print(f"✅ 获取用户成功: {user['email']}")
    
    # 测试保存计算记录
    inputs = {"country": "葡萄牙", "city": "里斯本"}
    results = {"balance": 1000.0}
    calc_id = db.save_calculation(user_id, "葡萄牙", "里斯本", inputs, results)
    print(f"✅ 保存计算记录成功: ID={calc_id}")
    
    # 测试获取计算历史
    calculations = db.get_user_calculations(user_id, limit=10)
    print(f"✅ 获取计算历史成功: {len(calculations)} 条记录")
    
    # 测试使用统计
    usage = db.get_monthly_usage(user_id)
    print(f"✅ 获取月度使用统计: {usage} 次")
    
    print("\n✅ 数据库测试完成\n")
    return user_id

def test_auth():
    """测试认证功能"""
    print("=" * 50)
    print("测试认证功能")
    print("=" * 50)
    
    # 测试密码哈希
    password = "test123"
    password_hash = hash_password(password)
    print(f"✅ 密码哈希生成成功: {password_hash[:20]}...")
    
    # 测试密码验证
    is_valid = verify_password(password, password_hash)
    print(f"✅ 密码验证: {'成功' if is_valid else '失败'}")
    
    # 测试注册（如果用户不存在）
    success, message = register_user("newuser@example.com", "password123")
    print(f"✅ 注册测试: {message}")
    
    # 测试登录
    success, user_id, message = authenticate_user("newuser@example.com", "password123")
    print(f"✅ 登录测试: {message}, User ID: {user_id if success else 'N/A'}")
    
    print("\n✅ 认证测试完成\n")

def test_subscription():
    """测试订阅功能"""
    print("=" * 50)
    print("测试订阅功能")
    print("=" * 50)
    
    manager = SubscriptionManager()
    
    # 创建测试用户
    db = Database()
    test_email = "subtest@example.com"
    password_hash = hash_password("test123")
    user_id = db.create_user(test_email, password_hash)
    
    if not user_id:
        user = db.get_user_by_email(test_email)
        user_id = user['id'] if user else None
    
    if user_id:
        # 测试订阅检查
        subscription = manager.get_subscription_type(user_id)
        print(f"✅ 当前订阅类型: {subscription}")
        
        # 测试使用限制
        can_calc, message = manager.can_calculate(user_id)
        print(f"✅ 使用限制检查: {can_calc}, {message}")
        
        # 测试升级
        manager.upgrade_subscription(user_id, 'pro_monthly', 30)
        subscription = manager.get_subscription_type(user_id)
        print(f"✅ 升级后订阅类型: {subscription}")
        
        # 测试使用信息
        usage_info = manager.get_usage_info(user_id)
        print(f"✅ 使用信息: {usage_info}")
    
    print("\n✅ 订阅测试完成\n")

def test_stats():
    """测试统计功能"""
    print("=" * 50)
    print("测试统计功能")
    print("=" * 50)
    
    manager = StatsManager()
    
    # 创建测试用户
    db = Database()
    test_email = "statstest@example.com"
    password_hash = hash_password("test123")
    user_id = db.create_user(test_email, password_hash)
    
    if not user_id:
        user = db.get_user_by_email(test_email)
        user_id = user['id'] if user else None
    
    if user_id:
        # 保存一些测试数据
        for i in range(3):
            inputs = {"country": "葡萄牙", "city": "里斯本"}
            results = {"balance": 1000.0 + i}
            db.save_calculation(user_id, "葡萄牙", "里斯本", inputs, results)
        
        # 测试用户统计
        stats = manager.get_user_stats(user_id)
        print(f"✅ 用户统计:")
        print(f"   - 总计算次数: {stats['total_calculations']}")
        print(f"   - 本月使用: {stats['monthly_usage']}")
        print(f"   - 最近7天: {stats['recent_7days']}")
        
        # 测试全局统计
        global_stats = manager.get_global_stats()
        print(f"✅ 全局统计:")
        print(f"   - 总用户数: {global_stats['total_users']}")
        print(f"   - 总计算次数: {global_stats['total_calculations']}")
        print(f"   - 付费用户: {global_stats['paid_users']}")
    
    print("\n✅ 统计测试完成\n")

def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("开始功能测试")
    print("=" * 50 + "\n")
    
    try:
        # 测试数据库
        user_id = test_database()
        
        # 测试认证
        test_auth()
        
        # 测试订阅
        test_subscription()
        
        # 测试统计
        test_stats()
        
        print("=" * 50)
        print("✅ 所有测试完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


