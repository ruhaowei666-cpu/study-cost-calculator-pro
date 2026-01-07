"""
数据库修复补丁 - 统一PostgreSQL和SQLite语法
"""

# 这个文件包含需要修复的数据库方法
# 主要修复点：
# 1. 所有SQL语句需要根据db_type使用不同的占位符（%s vs ?）
# 2. 所有查询结果需要统一处理
# 3. 所有事务操作需要统一处理

# 由于文件较大，建议逐个方法修复
# 关键修复点：
# - update_user_login: 需要支持两种占位符
# - update_subscription: 需要支持两种占位符
# - save_calculation: 需要支持两种占位符和ON CONFLICT语法
# - get_user_calculations: 需要支持两种占位符
# - get_monthly_usage: 需要支持两种占位符
# - delete_calculation: 需要支持两种占位符


