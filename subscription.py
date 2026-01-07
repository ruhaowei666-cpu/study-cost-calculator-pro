"""
订阅管理模块

管理用户订阅状态、检查订阅权限等
"""

from database import Database
from datetime import datetime, timedelta
from typing import Optional


class SubscriptionManager:
    """订阅管理器"""
    
    # 订阅类型
    FREE = "free"
    PRO_MONTHLY = "pro_monthly"
    PRO_YEARLY = "pro_yearly"
    
    # 免费用户限制
    FREE_MONTHLY_LIMIT = 3
    
    def __init__(self):
        self.db = Database()
    
    def get_subscription_type(self, user_id: int) -> str:
        """
        获取用户订阅类型
        
        参数:
            user_id: 用户ID
            
        返回:
            订阅类型
        """
        user = self.db.get_user_by_id(user_id)
        if not user:
            return self.FREE
        
        subscription_type = user.get('subscription_type', self.FREE)
        expires_at = user.get('subscription_expires_at')
        
        # 检查是否过期
        if expires_at and subscription_type != self.FREE:
            try:
                expires = datetime.fromisoformat(expires_at)
                if datetime.now() > expires:
                    # 订阅已过期，降级为免费用户
                    self.db.update_subscription(user_id, self.FREE)
                    return self.FREE
            except:
                pass
        
        return subscription_type
    
    def is_pro_user(self, user_id: int) -> bool:
        """
        检查用户是否为付费用户
        
        参数:
            user_id: 用户ID
            
        返回:
            是否为付费用户
        """
        subscription = self.get_subscription_type(user_id)
        return subscription in [self.PRO_MONTHLY, self.PRO_YEARLY]
    
    def can_calculate(self, user_id: int) -> tuple[bool, str]:
        """
        检查用户是否可以计算
        
        参数:
            user_id: 用户ID
            
        返回:
            (是否可以, 提示信息)
        """
        subscription = self.get_subscription_type(user_id)
        
        # 付费用户无限制
        if self.is_pro_user(user_id):
            return True, ""
        
        # 免费用户检查使用次数
        usage = self.db.get_monthly_usage(user_id)
        if usage >= self.FREE_MONTHLY_LIMIT:
            return False, f"免费用户每月只能计算{self.FREE_MONTHLY_LIMIT}次，您本月已使用{usage}次。请升级到专业版享受无限计算。"
        
        remaining = self.FREE_MONTHLY_LIMIT - usage
        return True, f"免费用户：本月剩余 {remaining}/{self.FREE_MONTHLY_LIMIT} 次计算"
    
    def get_usage_info(self, user_id: int) -> dict:
        """
        获取用户使用信息
        
        参数:
            user_id: 用户ID
            
        返回:
            使用信息字典
        """
        subscription = self.get_subscription_type(user_id)
        usage = self.db.get_monthly_usage(user_id)
        
        info = {
            'subscription_type': subscription,
            'is_pro': self.is_pro_user(user_id),
            'monthly_usage': usage,
            'monthly_limit': None if self.is_pro_user(user_id) else self.FREE_MONTHLY_LIMIT,
            'remaining': None if self.is_pro_user(user_id) else (self.FREE_MONTHLY_LIMIT - usage)
        }
        
        # 获取订阅过期时间
        user = self.db.get_user_by_id(user_id)
        if user and user.get('subscription_expires_at'):
            try:
                info['expires_at'] = datetime.fromisoformat(user['subscription_expires_at'])
            except:
                pass
        
        return info
    
    def upgrade_subscription(self, user_id: int, subscription_type: str, duration_days: int = 30):
        """
        升级用户订阅
        
        参数:
            user_id: 用户ID
            subscription_type: 订阅类型
            duration_days: 订阅时长（天）
        """
        expires_at = datetime.now() + timedelta(days=duration_days)
        self.db.update_subscription(user_id, subscription_type, expires_at)
    
    def get_subscription_plans(self) -> list:
        """
        获取订阅计划列表
        
        返回:
            订阅计划列表
        """
        return [
            {
                'id': 'free',
                'name': '免费版',
                'price': 0,
                'features': [
                    '每月3次计算',
                    '基础图表',
                    'Excel导出',
                    '基础PDF报告'
                ]
            },
            {
                'id': 'pro_monthly',
                'name': '专业版（月付）',
                'price': 29,
                'period': '月',
                'features': [
                    '无限次计算',
                    '多场景对比（最多5个）',
                    '高级分析报告',
                    '历史记录保存（无限）',
                    '高级PDF报告',
                    '预算优化建议',
                    '无广告'
                ]
            },
            {
                'id': 'pro_yearly',
                'name': '专业版（年付）',
                'price': 299,
                'period': '年',
                'original_price': 348,  # 29 * 12
                'discount': '14%',
                'features': [
                    '无限次计算',
                    '多场景对比（最多5个）',
                    '高级分析报告',
                    '历史记录保存（无限）',
                    '高级PDF报告',
                    '预算优化建议',
                    '无广告',
                    '优先支持'
                ]
            }
        ]


