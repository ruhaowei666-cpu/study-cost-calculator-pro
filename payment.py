"""
支付处理模块

集成Stripe支付平台，处理订阅支付
"""

from typing import Optional
import streamlit as st
from subscription import SubscriptionManager
import os


class PaymentManager:
    """支付管理器"""
    
    def __init__(self):
        # 从环境变量读取Stripe密钥
        self.stripe_secret_key = os.getenv('STRIPE_SECRET_KEY', '')
        self.stripe_public_key = os.getenv('STRIPE_PUBLIC_KEY', '')
        self.stripe_enabled = bool(self.stripe_secret_key and self.stripe_public_key)
        
        # 如果Stripe已配置，导入stripe库
        if self.stripe_enabled:
            try:
                import stripe
                stripe.api_key = self.stripe_secret_key
                self.stripe = stripe
            except ImportError:
                self.stripe_enabled = False
                st.warning("⚠️ Stripe库未安装，请运行: pip install stripe")
    
    def create_checkout_session(self, user_id: int, plan_id: str, price: float, 
                                currency: str = 'cny') -> Optional[str]:
        """
        创建Stripe支付会话
        
        参数:
            user_id: 用户ID
            plan_id: 计划ID
            price: 价格（元）
            currency: 货币代码
            
        返回:
            支付URL或None
        """
        if not self.stripe_enabled:
            return None
        
        try:
            # 获取当前域名（用于回调）
            # 在Streamlit Cloud中，可以使用环境变量
            base_url = os.getenv('BASE_URL', 'http://localhost:8501')
            
            session = self.stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': f'留学生成本计算器 - {plan_id}',
                            'description': '专业版订阅，享受无限计算和高级功能'
                        },
                        'unit_amount': int(price * 100),  # 转换为分
                    },
                    'quantity': 1,
                }],
                mode='subscription' if 'monthly' in plan_id else 'payment',
                success_url=f'{base_url}?payment=success&session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'{base_url}?payment=cancel',
                client_reference_id=str(user_id),
                metadata={
                    'user_id': str(user_id),
                    'plan_id': plan_id
                }
            )
            
            return session.url
        except Exception as e:
            st.error(f"创建支付会话失败: {str(e)}")
            return None
    
    def verify_payment(self, session_id: str) -> Optional[dict]:
        """
        验证支付结果
        
        参数:
            session_id: Stripe会话ID
            
        返回:
            支付信息字典或None
        """
        if not self.stripe_enabled:
            return None
        
        try:
            session = self.stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                return {
                    'user_id': int(session.client_reference_id),
                    'plan_id': session.metadata.get('plan_id'),
                    'amount': session.amount_total / 100,
                    'currency': session.currency
                }
        except Exception as e:
            st.error(f"验证支付失败: {str(e)}")
        
        return None
    
    def handle_payment_success(self, user_id: int, plan_id: str):
        """
        处理支付成功
        
        参数:
            user_id: 用户ID
            plan_id: 计划ID
        """
        from subscription import SubscriptionManager
        
        subscription_manager = SubscriptionManager()
        
        if plan_id == 'pro_monthly':
            subscription_manager.upgrade_subscription(user_id, 'pro_monthly', 30)
        elif plan_id == 'pro_yearly':
            subscription_manager.upgrade_subscription(user_id, 'pro_yearly', 365)
    
    def show_payment_options(self, user_id: int):
        """
        显示支付选项（在Streamlit中）
        
        参数:
            user_id: 用户ID
        """
        from subscription import SubscriptionManager
        
        subscription_manager = SubscriptionManager()
        plans = subscription_manager.get_subscription_plans()
        
        st.markdown("### 💳 选择订阅计划")
        
        # 显示Stripe状态
        if not self.stripe_enabled:
            st.warning("⚠️ Stripe支付未配置。当前为测试模式。")
            st.info("""
            💡 **配置Stripe支付**：
            1. 注册Stripe账号：https://stripe.com
            2. 获取API密钥
            3. 设置环境变量：
               - STRIPE_SECRET_KEY
               - STRIPE_PUBLIC_KEY
            4. 安装stripe库：`pip install stripe`
            """)
        
        # 显示付费计划
        for plan in plans[1:]:  # 跳过免费版
            with st.container():
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"#### {plan['name']}")
                    if 'original_price' in plan:
                        st.markdown(f"~~¥{plan['original_price']}~~ **¥{plan['price']}/{plan['period']}** (节省{plan['discount']})")
                    else:
                        st.markdown(f"**¥{plan['price']}/{plan['period']}**")
                    
                    st.markdown("**功能包括：**")
                    for feature in plan['features']:
                        st.markdown(f"- ✅ {feature}")
                
                with col2:
                    if self.stripe_enabled:
                        # 真实支付
                        if st.button(f"💳 立即订阅", key=f"pay_{plan['id']}", use_container_width=True):
                            price = plan['price']
                            checkout_url = self.create_checkout_session(user_id, plan['id'], price)
                            
                            if checkout_url:
                                st.info("正在跳转到支付页面...")
                                st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">', unsafe_allow_html=True)
                                st.link_button("点击前往支付", checkout_url)
                            else:
                                st.error("创建支付会话失败，请稍后重试")
                    else:
                        # 测试模式
                        if st.button(f"测试：选择 {plan['name']}", key=f"test_{plan['id']}", use_container_width=True):
                            st.info(f"💡 支付功能开发中，当前为测试模式")
                            st.info(f"计划：{plan['name']}，价格：¥{plan['price']}")
                            
                            # 临时：直接升级（用于测试）
                            if st.button(f"测试：直接升级到{plan['name']}", key=f"test_upgrade_{plan['id']}"):
                                subscription_manager.upgrade_subscription(
                                    user_id, 
                                    plan['id'],
                                    30 if 'monthly' in plan['id'] else 365
                                )
                                st.success(f"✅ 已升级到{plan['name']}！")
                                st.rerun()
        
        st.markdown("---")
        
        # 支付说明
        with st.expander("💡 支付说明"):
            st.markdown("""
            **支付方式：**
            - 支持信用卡/借记卡支付
            - 支付安全由Stripe保障
            - 支持全球主要银行卡
            
            **订阅说明：**
            - 月付：每月自动续费，可随时取消
            - 年付：一次性支付，节省14%
            - 订阅后立即生效，享受所有专业版功能
            
            **退款政策：**
            - 7天内无条件退款
            - 如有问题，请联系客服
            """)
