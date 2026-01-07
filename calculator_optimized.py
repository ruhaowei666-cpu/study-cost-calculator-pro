"""
留学生成本计算器 - 核心计算逻辑模块（优化版）

优化内容：
1. 添加输入验证
2. 修复find_critical_months逻辑错误
3. 改进错误处理
4. 添加类型提示
5. 提取配置常量
"""

import pandas as pd
from typing import Dict, Tuple, List, Optional
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalculationError(Exception):
    """自定义计算错误基类"""
    pass


class InvalidInputError(CalculationError):
    """输入无效错误"""
    pass


class StudyCostCalculator:
    """留学生成本计算器核心类（优化版）"""
    
    # 配置常量
    WEEKS_PER_MONTH = 4.33  # 每月周数（52周/12月）
    AVERAGE_HOURLY_WAGE = 8.0  # 平均小时工资（欧元/小时）
    TUITION_PAYMENT_MONTHS = 10  # 分期付款月数
    
    # 城市生活成本数据库（每月，单位：欧元）
    CITY_COSTS = {
        "里斯本": {
            "单间": {"房租": 400, "生活费": 350},
            "合租": {"房租": 250, "生活费": 300},
            "宿舍": {"房租": 300, "生活费": 320}
        },
        "波尔图": {
            "单间": {"房租": 350, "生活费": 320},
            "合租": {"房租": 220, "生活费": 280},
            "宿舍": {"房租": 280, "生活费": 300}
        },
        "其他": {
            "单间": {"房租": 380, "生活费": 330},
            "合租": {"房租": 240, "生活费": 290},
            "宿舍": {"房租": 290, "生活费": 310}
        }
    }
    
    def __init__(self, 
                 city: str,
                 rent_type: str,
                 has_job: bool,
                 weekly_hours: float,
                 initial_deposit: float,
                 tuition_total: float,
                 tuition_payment: str):
        """
        初始化计算器（带输入验证）
        
        参数:
            city: 城市名称
            rent_type: 房租类型（单间/合租/宿舍）
            has_job: 是否打工
            weekly_hours: 每周工作小时数
            initial_deposit: 初始存款（欧元）
            tuition_total: 学费总额（欧元）
            tuition_payment: 学费支付方式（一次性/分期）
            
        异常:
            InvalidInputError: 输入无效时抛出
        """
        # 输入验证
        self._validate_inputs(city, rent_type, weekly_hours, initial_deposit, tuition_total, tuition_payment)
        
        self.city = city
        self.rent_type = rent_type
        self.has_job = has_job
        self.weekly_hours = weekly_hours if has_job else 0.0
        self.initial_deposit = initial_deposit
        self.tuition_total = tuition_total
        self.tuition_payment = tuition_payment
        
        # 获取城市生活成本
        try:
            self.monthly_rent = self.CITY_COSTS[city][rent_type]["房租"]
            self.monthly_living_cost = self.CITY_COSTS[city][rent_type]["生活费"]
        except KeyError as e:
            raise InvalidInputError(f"数据配置错误: 无法找到城市 '{city}' 或房租类型 '{rent_type}' 的配置")
        
        # 计算月收入
        self.monthly_income = self._calculate_monthly_income()
        
        # 计算学费分摊
        self.tuition_monthly = self._calculate_tuition_monthly()
        
        logger.info(f"计算器初始化成功: city={city}, rent_type={rent_type}, has_job={has_job}")
    
    def _validate_inputs(self, city: str, rent_type: str, weekly_hours: float,
                        initial_deposit: float, tuition_total: float, tuition_payment: str) -> None:
        """
        验证输入参数
        
        异常:
            InvalidInputError: 输入无效时抛出
        """
        # 验证城市
        if city not in self.CITY_COSTS:
            available_cities = ", ".join(self.CITY_COSTS.keys())
            raise InvalidInputError(
                f"不支持的城市: '{city}'。支持的城市: {available_cities}"
            )
        
        # 验证房租类型
        if rent_type not in self.CITY_COSTS[city]:
            available_types = ", ".join(self.CITY_COSTS[city].keys())
            raise InvalidInputError(
                f"不支持的房租类型: '{rent_type}'。支持的类型: {available_types}"
            )
        
        # 验证数值输入
        if initial_deposit < 0:
            raise InvalidInputError("初始存款不能为负数")
        
        if tuition_total < 0:
            raise InvalidInputError("学费总额不能为负数")
        
        if weekly_hours < 0:
            raise InvalidInputError("每周工作小时数不能为负数")
        
        if weekly_hours > 40:
            raise InvalidInputError("每周工作小时数不能超过40小时")
        
        # 验证学费支付方式
        if tuition_payment not in ["一次性", "分期"]:
            raise InvalidInputError(f"不支持的学费支付方式: '{tuition_payment}'。支持的方式: 一次性, 分期")
    
    def _calculate_monthly_income(self) -> float:
        """计算月收入"""
        if not self.has_job:
            return 0.0
        
        monthly_hours = self.weekly_hours * self.WEEKS_PER_MONTH
        return round(monthly_hours * self.AVERAGE_HOURLY_WAGE, 2)
    
    def _calculate_tuition_monthly(self) -> float:
        """计算每月学费分摊"""
        if self.tuition_payment == "一次性":
            return 0.0
        elif self.tuition_payment == "分期":
            return round(self.tuition_total / self.TUITION_PAYMENT_MONTHS, 2)
        else:
            return 0.0
    
    def calculate_cashflow(self) -> pd.DataFrame:
        """
        计算12个月的现金流
        
        返回:
            包含月份、收入、支出、余额的DataFrame
            
        异常:
            CalculationError: 计算出错时抛出
        """
        try:
            months = []
            incomes = []
            expenses = []
            balances = []
            cumulative_balance = self.initial_deposit
            
            # 生成12个月的数据（从9月开始，假设是学年开始）
            month_names = ["9月", "10月", "11月", "12月", "1月", "2月", 
                          "3月", "4月", "5月", "6月", "7月", "8月"]
            
            for i, month_name in enumerate(month_names):
                # 月收入
                income = self.monthly_income
                
                # 月支出
                expense = self.monthly_rent + self.monthly_living_cost
                
                # 学费处理
                if self.tuition_payment == "一次性" and i == 0:  # 9月一次性支付
                    expense += self.tuition_total
                elif self.tuition_payment == "分期" and i < self.TUITION_PAYMENT_MONTHS:  # 9月到6月分期支付
                    expense += self.tuition_monthly
                
                # 计算余额
                cumulative_balance = cumulative_balance + income - expense
                
                months.append(month_name)
                incomes.append(round(income, 2))
                expenses.append(round(expense, 2))
                balances.append(round(cumulative_balance, 2))
            
            # 创建DataFrame
            df = pd.DataFrame({
                "月份": months,
                "月收入（€）": incomes,
                "月支出（€）": expenses,
                "累计余额（€）": balances
            })
            
            logger.info("现金流计算完成")
            return df
            
        except Exception as e:
            logger.error(f"现金流计算出错: {e}")
            raise CalculationError(f"计算出错: {str(e)}")
    
    def find_critical_months(self, df: pd.DataFrame) -> Tuple[List[str], float]:
        """
        找出危险月份和需要补钱的金额（修复版）
        
        参数:
            df: 现金流DataFrame
            
        返回:
            (危险月份列表, 需要补钱的总额)
        """
        try:
            min_balance = df["累计余额（€）"].min()
            
            # 找出所有负余额的月份（修复：直接获取所有负余额月份，避免重复）
            negative_months_df = df[df["累计余额（€）"] < 0]
            critical_months = negative_months_df["月份"].tolist() if len(negative_months_df) > 0 else []
            
            # 计算需要补钱的总额（如果最低余额为负）
            need_support = abs(min_balance) if min_balance < 0 else 0.0
            
            if critical_months:
                logger.warning(f"检测到危险月份: {critical_months}, 需要补钱: {need_support:.2f} €")
            
            return critical_months, need_support
            
        except Exception as e:
            logger.error(f"危险月份识别出错: {e}")
            raise CalculationError(f"危险月份识别出错: {str(e)}")
    
    def get_summary(self) -> Dict:
        """
        获取计算摘要信息
        
        返回:
            包含摘要信息的字典
            
        异常:
            CalculationError: 计算出错时抛出
        """
        try:
            df = self.calculate_cashflow()
            critical_months, need_support = self.find_critical_months(df)
            
            summary = {
                "monthly_income": self.monthly_income,
                "monthly_expense_base": self.monthly_rent + self.monthly_living_cost,
                "tuition_monthly": self.tuition_monthly,
                "final_balance": df["累计余额（€）"].iloc[-1],
                "min_balance": df["累计余额（€）"].min(),
                "critical_months": critical_months,
                "need_support": need_support,
                "cashflow_df": df
            }
            
            logger.info("摘要计算完成")
            return summary
            
        except Exception as e:
            logger.error(f"摘要计算出错: {e}")
            raise CalculationError(f"摘要计算出错: {str(e)}")
    
    @classmethod
    def get_available_cities(cls) -> List[str]:
        """获取支持的城市列表"""
        return list(cls.CITY_COSTS.keys())
    
    @classmethod
    def get_available_rent_types(cls, city: str) -> List[str]:
        """获取指定城市支持的房租类型列表"""
        if city not in cls.CITY_COSTS:
            return []
        return list(cls.CITY_COSTS[city].keys())


