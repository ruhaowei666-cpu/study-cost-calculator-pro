"""
测试示例 - 演示如何使用计算器模块

这个文件展示了如何直接使用calculator.py模块进行计算，
不依赖Streamlit界面，便于测试和调试。
"""

from calculator import StudyCostCalculator
import pandas as pd

def test_example_1():
    """示例1：有打工收入的学生"""
    print("=" * 60)
    print("示例1：有打工收入的学生")
    print("=" * 60)
    
    calculator = StudyCostCalculator(
        city="里斯本",
        rent_type="合租",
        has_job=True,
        weekly_hours=15.0,
        initial_deposit=5000.0,
        tuition_total=5000.0,
        tuition_payment="分期"
    )
    
    summary = calculator.get_summary()
    df = summary["cashflow_df"]
    
    print(f"\n月收入: {summary['monthly_income']:.2f} €")
    print(f"月基础支出: {summary['monthly_expense_base']:.2f} €")
    print(f"学费月分摊: {summary['tuition_monthly']:.2f} €")
    print(f"\n最终余额: {summary['final_balance']:.2f} €")
    print(f"最低余额: {summary['min_balance']:.2f} €")
    
    if summary['critical_months']:
        print(f"\n⚠️ 危险月份: {', '.join(summary['critical_months'])}")
        print(f"💸 需要补钱: {summary['need_support']:.2f} €")
    else:
        print("\n✅ 财务状况良好！")
    
    print("\n12个月现金流明细:")
    print(df.to_string(index=False))
    print()


def test_example_2():
    """示例2：无打工收入的学生"""
    print("=" * 60)
    print("示例2：无打工收入的学生")
    print("=" * 60)
    
    calculator = StudyCostCalculator(
        city="波尔图",
        rent_type="宿舍",
        has_job=False,
        weekly_hours=0.0,
        initial_deposit=10000.0,
        tuition_total=6000.0,
        tuition_payment="一次性"
    )
    
    summary = calculator.get_summary()
    df = summary["cashflow_df"]
    
    print(f"\n月收入: {summary['monthly_income']:.2f} €")
    print(f"月基础支出: {summary['monthly_expense_base']:.2f} €")
    print(f"学费支付方式: 一次性（9月支付）")
    print(f"\n最终余额: {summary['final_balance']:.2f} €")
    print(f"最低余额: {summary['min_balance']:.2f} €")
    
    if summary['critical_months']:
        print(f"\n⚠️ 危险月份: {', '.join(summary['critical_months'])}")
        print(f"💸 需要补钱: {summary['need_support']:.2f} €")
    else:
        print("\n✅ 财务状况良好！")
    
    print("\n12个月现金流明细:")
    print(df.to_string(index=False))
    print()


def test_example_3():
    """示例3：资金不足的情况"""
    print("=" * 60)
    print("示例3：资金不足的情况")
    print("=" * 60)
    
    calculator = StudyCostCalculator(
        city="里斯本",
        rent_type="单间",
        has_job=True,
        weekly_hours=10.0,  # 工作较少
        initial_deposit=2000.0,  # 初始存款较少
        tuition_total=7000.0,
        tuition_payment="分期"
    )
    
    summary = calculator.get_summary()
    df = summary["cashflow_df"]
    
    print(f"\n月收入: {summary['monthly_income']:.2f} €")
    print(f"月基础支出: {summary['monthly_expense_base']:.2f} €")
    print(f"学费月分摊: {summary['tuition_monthly']:.2f} €")
    print(f"\n最终余额: {summary['final_balance']:.2f} €")
    print(f"最低余额: {summary['min_balance']:.2f} €")
    
    if summary['critical_months']:
        print(f"\n⚠️ 危险月份: {', '.join(summary['critical_months'])}")
        print(f"💸 需要补钱: {summary['need_support']:.2f} €")
        print(f"\n建议:")
        print(f"1. 增加初始存款至少 {summary['need_support']:.2f} €")
        print(f"2. 增加工作时间（当前每周 {calculator.weekly_hours} 小时）")
        print(f"3. 考虑更便宜的住宿方式（当前: {calculator.rent_type}）")
    else:
        print("\n✅ 财务状况良好！")
    
    print("\n12个月现金流明细:")
    print(df.to_string(index=False))
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("留学生成本计算器 - 测试示例")
    print("=" * 60 + "\n")
    
    # 运行所有测试示例
    test_example_1()
    test_example_2()
    test_example_3()
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)



