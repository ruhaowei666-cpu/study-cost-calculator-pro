"""
配置文件

存储应用配置信息
"""

# 免费用户限制
FREE_MONTHLY_LIMIT = 3

# 订阅计划
SUBSCRIPTION_PLANS = {
    'free': {
        'name': '免费版',
        'price': 0,
        'monthly_limit': 3
    },
    'pro_monthly': {
        'name': '专业版（月付）',
        'price': 29,
        'period': 'month',
        'duration_days': 30
    },
    'pro_yearly': {
        'name': '专业版（年付）',
        'price': 299,
        'period': 'year',
        'duration_days': 365,
        'original_price': 348,
        'discount': '14%'
    }
}

# 数据库配置
DATABASE_PATH = "app.db"

# 支付配置（需要时配置）
# STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
# STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')


