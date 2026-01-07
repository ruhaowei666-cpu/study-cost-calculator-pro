"""
用户认证模块

提供用户注册、登录、密码管理等功能
"""

import hashlib
import streamlit as st
from database import Database
from datetime import datetime
from typing import Optional


def hash_password(password: str) -> str:
    """
    对密码进行哈希处理
    
    参数:
        password: 原始密码
        
    返回:
        密码哈希值
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """
    验证密码
    
    参数:
        password: 原始密码
        password_hash: 密码哈希值
        
    返回:
        是否匹配
    """
    return hash_password(password) == password_hash


def is_logged_in() -> bool:
    """检查用户是否已登录"""
    return 'user_id' in st.session_state and st.session_state['user_id'] is not None


def get_current_user_id() -> Optional[int]:
    """获取当前登录用户ID"""
    return st.session_state.get('user_id')


def get_current_user_email() -> Optional[str]:
    """获取当前登录用户邮箱"""
    return st.session_state.get('user_email')


def login_user(user_id: int, email: str):
    """
    登录用户
    
    参数:
        user_id: 用户ID
        email: 用户邮箱
    """
    st.session_state['user_id'] = user_id
    st.session_state['user_email'] = email
    
    # 更新最后登录时间
    db = Database()
    db.update_user_login(user_id)


def logout_user():
    """登出用户"""
    if 'user_id' in st.session_state:
        del st.session_state['user_id']
    if 'user_email' in st.session_state:
        del st.session_state['user_email']
    if 'user_subscription' in st.session_state:
        del st.session_state['user_subscription']


def register_user(email: str, password: str) -> tuple[bool, str]:
    """
    注册新用户
    
    参数:
        email: 邮箱
        password: 密码
        
    返回:
        (是否成功, 错误信息)
    """
    # 验证输入
    if not email or '@' not in email:
        return False, "请输入有效的邮箱地址"
    
    if len(password) < 6:
        return False, "密码长度至少6位"
    
    # 创建用户
    db = Database()
    password_hash = hash_password(password)
    user_id = db.create_user(email, password_hash)
    
    if user_id:
        return True, "注册成功！"
    else:
        return False, "该邮箱已被注册"


def authenticate_user(email: str, password: str) -> tuple[bool, Optional[int], str]:
    """
    验证用户登录
    
    参数:
        email: 邮箱
        password: 密码
        
    返回:
        (是否成功, 用户ID, 错误信息)
    """
    db = Database()
    user = db.get_user_by_email(email)
    
    if not user:
        return False, None, "邮箱或密码错误"
    
    if verify_password(password, user['password_hash']):
        return True, user['id'], "登录成功"
    else:
        return False, None, "邮箱或密码错误"


def show_login_form():
    """显示登录表单"""
    with st.form("login_form"):
        st.subheader("🔐 登录")
        email = st.text_input("邮箱", key="login_email")
        password = st.text_input("密码", type="password", key="login_password")
        submit = st.form_submit_button("登录", use_container_width=True)
        
        if submit:
            if email and password:
                success, user_id, message = authenticate_user(email, password)
                if success:
                    login_user(user_id, email)
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("请填写邮箱和密码")
    
    # 注册链接
    if st.button("还没有账号？立即注册"):
        st.session_state['show_register'] = True
        st.rerun()


def show_register_form():
    """显示注册表单"""
    with st.form("register_form"):
        st.subheader("📝 注册")
        email = st.text_input("邮箱", key="register_email")
        password = st.text_input("密码", type="password", key="register_password")
        password_confirm = st.text_input("确认密码", type="password", key="register_password_confirm")
        submit = st.form_submit_button("注册", use_container_width=True)
        
        if submit:
            if not email or not password:
                st.warning("请填写所有字段")
            elif password != password_confirm:
                st.error("两次输入的密码不一致")
            else:
                success, message = register_user(email, password)
                if success:
                    st.success(message)
                    st.info("请使用您的账号登录")
                    st.session_state['show_register'] = False
                    st.rerun()
                else:
                    st.error(message)
    
    # 返回登录
    if st.button("已有账号？返回登录"):
        st.session_state['show_register'] = False
        st.rerun()


