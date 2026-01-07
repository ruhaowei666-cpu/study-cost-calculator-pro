"""
使用统计模块

提供用户使用统计和分析功能
"""

from database import Database
from datetime import datetime, timedelta
from typing import Dict, List
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


class StatsManager:
    """统计管理器"""
    
    def __init__(self):
        self.db = Database()
    
    def get_user_stats(self, user_id: int) -> Dict:
        """
        获取用户统计信息
        
        参数:
            user_id: 用户ID
            
        返回:
            统计信息字典
        """
        conn = self.db.get_connection()
        c = conn.cursor()
        
        # 总计算次数
        if self.db.db_type == 'postgresql':
            c.execute('SELECT COUNT(*) FROM calculations WHERE user_id = %s', (user_id,))
        else:
            c.execute('SELECT COUNT(*) FROM calculations WHERE user_id = ?', (user_id,))
        total_calculations = c.fetchone()[0] or 0
        
        # 本月计算次数
        now = datetime.now()
        year = now.year
        month = now.month
        monthly_usage = self.db.get_monthly_usage(user_id, year, month)
        
        # 最常使用的城市
        if self.db.db_type == 'postgresql':
            c.execute('''
                SELECT city, COUNT(*) as count 
                FROM calculations 
                WHERE user_id = %s 
                GROUP BY city 
                ORDER BY count DESC 
                LIMIT 5
            ''', (user_id,))
        else:
            c.execute('''
                SELECT city, COUNT(*) as count 
                FROM calculations 
                WHERE user_id = ? 
                GROUP BY city 
                ORDER BY count DESC 
                LIMIT 5
            ''', (user_id,))
        top_cities = [dict(row) for row in c.fetchall()] if self.db.db_type == 'postgresql' else [dict(row) for row in c.fetchall()]
        
        # 最近7天的计算次数
        seven_days_ago = now - timedelta(days=7)
        if self.db.db_type == 'postgresql':
            c.execute('''
                SELECT COUNT(*) 
                FROM calculations 
                WHERE user_id = %s AND created_at >= %s
            ''', (user_id, seven_days_ago))
        else:
            c.execute('''
                SELECT COUNT(*) 
                FROM calculations 
                WHERE user_id = ? AND created_at >= ?
            ''', (user_id, seven_days_ago))
        recent_count = c.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_calculations': total_calculations,
            'monthly_usage': monthly_usage,
            'recent_7days': recent_count,
            'top_cities': top_cities
        }
    
    def get_global_stats(self) -> Dict:
        """
        获取全局统计信息（管理员功能）
        
        返回:
            全局统计信息
        """
        conn = self.db.get_connection()
        c = conn.cursor()
        
        # 总用户数
        c.execute('SELECT COUNT(*) FROM users')
        total_users = c.fetchone()[0] or 0
        
        # 总计算次数
        c.execute('SELECT COUNT(*) FROM calculations')
        total_calculations = c.fetchone()[0] or 0
        
        # 付费用户数
        if self.db.db_type == 'postgresql':
            c.execute("SELECT COUNT(*) FROM users WHERE subscription_type != 'free'")
        else:
            c.execute("SELECT COUNT(*) FROM users WHERE subscription_type != 'free'")
        paid_users = c.fetchone()[0] or 0
        
        # 本月新增用户
        now = datetime.now()
        first_day = datetime(now.year, now.month, 1)
        if self.db.db_type == 'postgresql':
            c.execute('SELECT COUNT(*) FROM users WHERE created_at >= %s', (first_day,))
        else:
            c.execute('SELECT COUNT(*) FROM users WHERE created_at >= ?', (first_day,))
        new_users_this_month = c.fetchone()[0] or 0
        
        # 热门城市
        if self.db.db_type == 'postgresql':
            c.execute('''
                SELECT city, COUNT(*) as count 
                FROM calculations 
                GROUP BY city 
                ORDER BY count DESC 
                LIMIT 10
            ''')
        else:
            c.execute('''
                SELECT city, COUNT(*) as count 
                FROM calculations 
                GROUP BY city 
                ORDER BY count DESC 
                LIMIT 10
            ''')
        top_cities = [dict(row) for row in c.fetchall()]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'total_calculations': total_calculations,
            'paid_users': paid_users,
            'free_users': total_users - paid_users,
            'new_users_this_month': new_users_this_month,
            'top_cities': top_cities,
            'conversion_rate': (paid_users / total_users * 100) if total_users > 0 else 0
        }
    
    def get_usage_trend(self, user_id: int, days: int = 30) -> pd.DataFrame:
        """
        获取使用趋势数据
        
        参数:
            user_id: 用户ID
            days: 天数
            
        返回:
            趋势数据DataFrame
        """
        conn = self.db.get_connection()
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        if self.db.db_type == 'postgresql':
            c.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM calculations
                WHERE user_id = %s AND created_at >= %s
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (user_id, start_date))
        else:
            c.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM calculations
                WHERE user_id = ? AND created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (user_id, start_date))
        
        rows = c.fetchall()
        conn.close()
        
        if rows:
            df = pd.DataFrame(rows, columns=['date', 'count'])
            df['date'] = pd.to_datetime(df['date'])
            return df
        else:
            return pd.DataFrame(columns=['date', 'count'])
    
    def show_user_stats_dashboard(self, user_id: int):
        """显示用户统计仪表板"""
        stats = self.get_user_stats(user_id)
        
        st.markdown("### 📊 我的使用统计")
        
        # 关键指标
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总计算次数", stats['total_calculations'])
        with col2:
            st.metric("本月使用", stats['monthly_usage'])
        with col3:
            st.metric("最近7天", stats['recent_7days'])
        
        st.markdown("---")
        
        # 使用趋势图
        st.markdown("#### 📈 使用趋势（最近30天）")
        trend_df = self.get_usage_trend(user_id, 30)
        
        if not trend_df.empty:
            fig = px.line(trend_df, x='date', y='count', 
                         title='每日计算次数',
                         labels={'date': '日期', 'count': '计算次数'})
            fig.update_traces(mode='lines+markers', line=dict(width=2))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无使用数据")
        
        # 热门城市
        if stats['top_cities']:
            st.markdown("#### 🌍 最常使用的城市")
            cities_df = pd.DataFrame(stats['top_cities'])
            fig = px.bar(cities_df, x='city', y='count',
                        title='城市使用频率',
                        labels={'city': '城市', 'count': '使用次数'})
            st.plotly_chart(fig, use_container_width=True)
    
    def show_admin_dashboard(self):
        """显示管理员统计仪表板"""
        stats = self.get_global_stats()
        
        st.markdown("### 📊 全局统计")
        
        # 关键指标
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总用户数", stats['total_users'])
        with col2:
            st.metric("总计算次数", stats['total_calculations'])
        with col3:
            st.metric("付费用户", stats['paid_users'])
        with col4:
            st.metric("转化率", f"{stats['conversion_rate']:.1f}%")
        
        st.markdown("---")
        
        # 用户分布
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 👥 用户分布")
            user_data = {
                '类型': ['免费用户', '付费用户'],
                '数量': [stats['free_users'], stats['paid_users']]
            }
            user_df = pd.DataFrame(user_data)
            fig = px.pie(user_df, values='数量', names='类型', 
                        title='用户类型分布')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 📅 本月新增用户")
            st.metric("新增用户", stats['new_users_this_month'])
        
        # 热门城市
        if stats['top_cities']:
            st.markdown("#### 🌍 热门城市（Top 10）")
            cities_df = pd.DataFrame(stats['top_cities'])
            fig = px.bar(cities_df, x='city', y='count',
                        title='城市使用频率',
                        labels={'city': '城市', 'count': '使用次数'})
            st.plotly_chart(fig, use_container_width=True)


