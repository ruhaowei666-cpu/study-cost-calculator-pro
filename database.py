"""
数据库模块 - 用户数据和计算记录存储

支持SQLite（开发）和PostgreSQL（生产）
- 用户信息
- 计算历史
- 订阅状态
"""

import os
from datetime import datetime
from typing import Optional, Dict, List
import json

# 尝试导入数据库驱动
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False


class Database:
    """数据库管理类（支持SQLite和PostgreSQL）"""
    
    def __init__(self, db_path: str = "app.db"):
        """
        初始化数据库
        
        参数:
            db_path: SQLite数据库文件路径（如果使用PostgreSQL则忽略）
        """
        self.db_path = db_path
        self.db_type = self._detect_db_type()
        self.init_database()
    
    def _detect_db_type(self) -> str:
        """检测使用的数据库类型"""
        # 检查环境变量中的PostgreSQL连接字符串
        database_url = os.getenv('DATABASE_URL')
        if database_url and 'postgres' in database_url.lower():
            if POSTGRESQL_AVAILABLE:
                return 'postgresql'
            else:
                st.warning("⚠️ 检测到PostgreSQL配置，但psycopg2未安装。使用SQLite。")
                st.info("💡 安装PostgreSQL驱动: pip install psycopg2-binary")
        
        # 默认使用SQLite
        if SQLITE_AVAILABLE:
            return 'sqlite'
        else:
            raise ImportError("需要安装数据库驱动: pip install psycopg2-binary 或使用Python内置sqlite3")
    
    def get_connection(self):
        """获取数据库连接"""
        if self.db_type == 'postgresql':
            database_url = os.getenv('DATABASE_URL')
            conn = psycopg2.connect(database_url)
            return conn
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        c = conn.cursor()
        
        if self.db_type == 'postgresql':
            # PostgreSQL语法
            # 用户表
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    subscription_type VARCHAR(50) DEFAULT 'free',
                    subscription_expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # 计算记录表
            c.execute('''
                CREATE TABLE IF NOT EXISTS calculations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    country VARCHAR(100) NOT NULL,
                    city VARCHAR(100) NOT NULL,
                    inputs TEXT NOT NULL,
                    results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 使用统计表
            c.execute('''
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    calculation_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, year, month)
                )
            ''')
        else:
            # SQLite语法
            # 用户表
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    subscription_type TEXT DEFAULT 'free',
                    subscription_expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # 计算记录表
            c.execute('''
                CREATE TABLE IF NOT EXISTS calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    country TEXT NOT NULL,
                    city TEXT NOT NULL,
                    inputs TEXT NOT NULL,
                    results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 使用统计表
            c.execute('''
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    calculation_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, year, month)
                )
            ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, email: str, password_hash: str) -> Optional[int]:
        """
        创建新用户
        
        参数:
            email: 邮箱
            password_hash: 密码哈希
            
        返回:
            用户ID，如果失败返回None
        """
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            if self.db_type == 'postgresql':
                c.execute('''
                    INSERT INTO users (email, password_hash)
                    VALUES (%s, %s)
                    RETURNING id
                ''', (email, password_hash))
                user_id = c.fetchone()[0]
            else:
                c.execute('''
                    INSERT INTO users (email, password_hash)
                    VALUES (?, ?)
                ''', (email, password_hash))
                user_id = c.lastrowid
            
            conn.commit()
            conn.close()
            return user_id
        except Exception as e:
            # 处理唯一约束错误（邮箱已存在）
            if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                return None
            raise
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        根据邮箱获取用户
        
        参数:
            email: 邮箱
            
        返回:
            用户信息字典，如果不存在返回None
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        if self.db_type == 'postgresql':
            c.execute('SELECT * FROM users WHERE email = %s', (email,))
            row = c.fetchone()
            if row:
                return dict(row)
        else:
            c.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = c.fetchone()
            if row:
                return dict(row)
        
        conn.close()
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        根据ID获取用户
        
        参数:
            user_id: 用户ID
            
        返回:
            用户信息字典
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        if self.db_type == 'postgresql':
            c.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            row = c.fetchone()
            if row:
                return dict(row)
        else:
            c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = c.fetchone()
            if row:
                return dict(row)
        
        conn.close()
        return None
    
    def update_user_login(self, user_id: int):
        """更新用户最后登录时间"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (user_id,))
        conn.commit()
        conn.close()
    
    def update_subscription(self, user_id: int, subscription_type: str, expires_at: Optional[datetime] = None):
        """
        更新用户订阅状态
        
        参数:
            user_id: 用户ID
            subscription_type: 订阅类型（free/pro/monthly/yearly）
            expires_at: 过期时间
        """
        conn = self.get_connection()
        c = conn.cursor()
        expires_str = expires_at.isoformat() if expires_at else None
        if self.db_type == 'postgresql':
            c.execute('''
                UPDATE users 
                SET subscription_type = %s, subscription_expires_at = %s
                WHERE id = %s
            ''', (subscription_type, expires_str, user_id))
        else:
            c.execute('''
                UPDATE users 
                SET subscription_type = ?, subscription_expires_at = ?
                WHERE id = ?
            ''', (subscription_type, expires_str, user_id))
        conn.commit()
        conn.close()
    
    def save_calculation(self, user_id: int, country: str, city: str, 
                        inputs: Dict, results: Dict) -> int:
        """
        保存计算记录
        
        参数:
            user_id: 用户ID
            country: 国家
            city: 城市
            inputs: 输入参数
            results: 计算结果
            
        返回:
            记录ID
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        # 保存计算记录
        inputs_json = json.dumps(inputs, ensure_ascii=False)
        results_json = json.dumps(results, ensure_ascii=False, default=str)
        
        if self.db_type == 'postgresql':
            c.execute('''
                INSERT INTO calculations (user_id, country, city, inputs, results)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (user_id, country, city, inputs_json, results_json))
            record_id = c.fetchone()[0]
        else:
            c.execute('''
                INSERT INTO calculations (user_id, country, city, inputs, results)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, country, city, inputs_json, results_json))
            record_id = c.lastrowid
        
        # 更新使用统计
        now = datetime.now()
        year = now.year
        month = now.month
        
        if self.db_type == 'postgresql':
            c.execute('''
                INSERT INTO usage_stats (user_id, year, month, calculation_count)
                VALUES (%s, %s, %s, 1)
                ON CONFLICT(user_id, year, month) 
                DO UPDATE SET calculation_count = usage_stats.calculation_count + 1
            ''', (user_id, year, month))
        else:
            c.execute('''
                INSERT INTO usage_stats (user_id, year, month, calculation_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id, year, month) 
                DO UPDATE SET calculation_count = calculation_count + 1
            ''', (user_id, year, month))
        
        conn.commit()
        conn.close()
        return record_id
    
    def get_user_calculations(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        获取用户的计算历史
        
        参数:
            user_id: 用户ID
            limit: 返回记录数限制
            
        返回:
            计算记录列表
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        if self.db_type == 'postgresql':
            c.execute('''
                SELECT * FROM calculations 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            ''', (user_id, limit))
        else:
            c.execute('''
                SELECT * FROM calculations 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
        
        rows = c.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            if self.db_type == 'postgresql':
                record = dict(row)
            else:
                record = dict(row)
            # 解析JSON数据
            record['inputs'] = json.loads(record['inputs'])
            record['results'] = json.loads(record['results'])
            records.append(record)
        
        return records
    
    def get_monthly_usage(self, user_id: int, year: Optional[int] = None, 
                          month: Optional[int] = None) -> int:
        """
        获取用户月度使用次数
        
        参数:
            user_id: 用户ID
            year: 年份（默认当前年）
            month: 月份（默认当前月）
            
        返回:
            使用次数
        """
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month
        
        conn = self.get_connection()
        c = conn.cursor()
        
        if self.db_type == 'postgresql':
            c.execute('''
                SELECT calculation_count FROM usage_stats
                WHERE user_id = %s AND year = %s AND month = %s
            ''', (user_id, year, month))
        else:
            c.execute('''
                SELECT calculation_count FROM usage_stats
                WHERE user_id = ? AND year = ? AND month = ?
            ''', (user_id, year, month))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            if self.db_type == 'postgresql':
                return row[0] if isinstance(row, tuple) else row['calculation_count']
            else:
                return row['calculation_count']
        return 0
    
    def delete_calculation(self, user_id: int, calculation_id: int) -> bool:
        """
        删除计算记录
        
        参数:
            user_id: 用户ID
            calculation_id: 记录ID
            
        返回:
            是否成功
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        if self.db_type == 'postgresql':
            c.execute('''
                DELETE FROM calculations 
                WHERE id = %s AND user_id = %s
            ''', (calculation_id, user_id))
        else:
            c.execute('''
                DELETE FROM calculations 
                WHERE id = ? AND user_id = ?
            ''', (calculation_id, user_id))
        
        deleted = c.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

