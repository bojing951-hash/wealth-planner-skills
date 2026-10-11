#!/usr/bin/env python3
"""Transparent, stdlib-only personal finance planning calculations.

All values represent hypothetical scenarios, not investment returns or advice.
V0.1: single currency CNY, aggregate debt, no product-specific forecasts.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from typing import Any


class ProfileError(ValueError):
    """Raised when a profile lacks required fields or is inconsistent."""


REQUIRED_FIELDS = (
    "monthly_cash_receipts",
    "monthly_essential_spending",
    "monthly_discretionary_spending",
    "financial_assets",
    "liquid_cash",
    "income_type",
)
OPTIONAL_NONNEGATIVE = (
    "monthly_required_business_cost",
    "monthly_tax_reserve",
    "monthly_debt_payment",
    "outstanding_debt",
    "monthly_essential_spending",
    "monthly_discretionary_spending",
    "monthly_cash_receipts",
    "financial_assets",
    "liquid_cash",
    "target_net_worth",
)
DEFAULTS = {
    "label": "匿名示例用户",
    "currency": "CNY",
    "monthly_required_business_cost": 0,
    "monthly_tax_reserve": 0,
    "monthly_debt_payment": 0,
    "outstanding_debt": 0,
    "debt_annual_rate": 0,
    "emergency_months": None,
    "target_net_worth": None,
    "target_years": 5,
    "annual_investment_return_assumption": 0.05,
    "annual_inflation_assumption": 0.025,
    "income_interruption_months": [],
    "interruption_discretionary_multiplier": 0.0,
    "high_interest_debt_threshold": 0.08,
    "starter_emergency_months": 2,
}
RETURN_SCENARIOS = {"保守（情景，非概率）": -0.02, "基准（情景，非预测）": 0.05, "乐观（情景，非预测）": 0.08}


def clean_number(obj: dict, key: str) -> float:
    value = obj[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ProfileError(f"{key} 必须为有限数字；实际收入必须自行核验")
    return float(value)


def validate(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ProfileError("输入必须为 JSON 对象")
    missing = [key for key in REQUIRED_FIELDS if key not in raw]
    if missing:
        raise ProfileError("缺少必填字段：" + ", ".join(missing))
    profile = {**DEFAULTS, **raw}
    if profile["currency"] != "CNY":
        raise ProfileError("当前版本仅支持人民币 CNY；不要直接混用美元和人民币")
    if profile["income_type"] not in ("stable", "variable", "uncertain"):
        raise ProfileError("income_type 必须是 stable / variable / uncertain")
    for key in OPTIONAL_NONNEGATIVE:
        if profile.get(key) is not None and clean_number(profile, key) < 0:
            raise ProfileError(f"{key} 不可为负数")
    for key in ("debt_annual_rate", "annual_investment_return_assumption", "annual_inflation_assumption", "interruption_discretionary_multiplier", "high_interest_debt_threshold"):
        value = clean_number(profile, key)
        if key == "interruption_discretionary_multiplier" and not (0 <= value <= 1):
            raise ProfileError("收入中断时可选消费系数须在 0 至 1 之间")
        if key in ("debt_annual_rate", "annual_inflation_assumption", "high_interest_debt_threshold") and value < 0:
            raise ProfileError(f"{key} 不可为负数")
        if key == "annual_investment_return_assumption" and value <= -1:
            raise ProfileError("投资收益率不得小于等于 -100%")
    if profile["annual_investment_return_assumption"] > 2.0:
        raise ProfileError("投资收益率假设超过200%，不适合此长期规划简化模型")
    if profile["financial_assets"] < profile["liquid_cash"]:
        raise ProfileError("financial_assets 必须 >= liquid_cash；不要把 PF 名义资金算作个人资产")
    years = clean_number(profile, "target_years")
    if int(years) != years or years < 1 or years > 50:
        raise ProfileError("target_years 应为 1～50 的整数")
    profile["target_years"] = int(years)
    months = profile["emergency_months"]
    if months is None:
        months = 6 if profile["income_type"] == "stable" else 12
    if isinstance(months, bool) or not isinstance(months, int) or months < 1 or months > 36:
        raise ProfileError("emergency_months 应为 1～36 的整数")
    profile["emergency_months"] = months
    starter = profile["starter_emergency_months"]
    if isinstance(starter, bool) or not isinstance(starter, int) or not (1 <= starter <= months):
        raise ProfileError("starter_emergency_months 必须为整数且不超过 emergency_months")
    interrupted = profile["income_interruption_months"]
    if not isinstance(interrupted, list) or not all(isinstance(m, int) and not isinstance(m, bool) and m >= 1 for m in interrupted):
        raise ProfileError("income_interruption_months 必须为正整数月份数组")
    profile["income_interruption_months"] = sorted(set(interrupted))
    if profile["monthly_debt_payment"] > 0 and profile["outstanding_debt"] == 0:
        raise ProfileError("有债务还款额但无债务余额：请提供 outstanding_debt 或将还款额归入其他支出")
    if profile["outstanding_debt"] > 0 and profile["monthly_debt_payment"] <= 0:
        raise ProfileError("有债务余额却未填月供：本版本要求输入 monthly_debt_payment")
    return profile


def annual_to_monthly(annual_rate: float) -> float:
    return (1.0 + annual_rate) ** (1 / 12) - 1.0


def round_money(value: float) -> float:
    return round(value + 0.00000001, 2)


def simulate(
    profile: dict[str, Any],
    months: int,
    annual_return: float | None = None,
    extra_monthly_cashflow: float = 0.0,
) -> dict[str, Any]:
    """Monthly cash/debt/investment simulation, not a probability model.

    Simplifications: all flows at month-end; investment return comes first, no
    portfolio-level risk; existing cash may be hypothetically allocated at t0.
    Tax reserve is conservatively removed from available assets each month.
    """
    if not isinstance(months, int) or months < 0 or months > 600:
        raise ValueError("模拟月份须在 0～600 之间")
    if extra_monthly_cashflow < 0:
        raise ValueError("额外净现金流不得为负")
    rate = profile["annual_investment_return_assumption"] if annual_return is None else annual_return
    if rate <= -1:
        raise ValueError("收益率不得小于等于 -100%")
    monthly_return = annual_to_monthly(rate)
    cash = float(profile["liquid_cash"])
    investment = float(profile["financial_assets"] - profile["liquid_cash"])
    debt = float(profile["outstanding_debt"])
    monthly_basic = float(profile["monthly_essential_spending"] + profile["monthly_required_business_cost"])
    monthly_survival = monthly_basic + (profile["monthly_debt_payment"] if debt > 0 else 0)
    target_reserve = monthly_survival * profile["emergency_months"]
    starter_reserve = monthly_survival * profile["starter_emergency_months"]
    debt_rate = float(profile["debt_annual_rate"])
    high_debt = debt > 0 and debt_rate >= profile["high_interest_debt_threshold"]
    # First, protect a starter reserve. Hypothetical accelerated debt repayment
    # has no penalty and is NOT an instruction to transfer money automatically.
    if high_debt and cash > starter_reserve:
        accelerated = min(cash - starter_reserve, debt)
        cash -= accelerated
        debt -= accelerated
    if cash > target_reserve and (debt <= 0 or not high_debt):
        investment += cash - target_reserve
        cash = target_reserve
    first_shortfall = None
    first_reserve_depletion = None
    total_income = 0.0
    total_consumption = 0.0
    total_interest = 0.0
    total_extra_debt_repayments = 0.0
    checkpoints = {}
    interruption_set = set(profile["income_interruption_months"])
    for month in range(1, months + 1):
        investment *= 1 + monthly_return
        income = float(profile["monthly_cash_receipts"] + extra_monthly_cashflow)
        discretionary = float(profile["monthly_discretionary_spending"])
        if month in interruption_set:
            # An interruption cuts the base receipts, but not the hypothetical
            # added recurring income used by the goal feasibility solver.
            income = extra_monthly_cashflow
            discretionary *= profile["interruption_discretionary_multiplier"]
        interest = debt * debt_rate / 12
        due_debt = debt + interest
        debt_payment = min(float(profile["monthly_debt_payment"]), due_debt)
        debt = max(0.0, due_debt - debt_payment)
        total_interest += interest
        spending = (monthly_basic + discretionary + debt_payment + float(profile["monthly_tax_reserve"]))
        total_income += income
        total_consumption += spending
        net_flow = income - spending
        if net_flow >= 0:
            # Pay off any previously unfunded deficit first.
            if cash < 0:
                payment = min(-cash, net_flow)
                cash += payment
                net_flow -= payment
            if debt > 0 and high_debt:
                buffer = max(0.0, starter_reserve - cash)
                to_buffer = min(buffer, net_flow)
                cash += to_buffer
                net_flow -= to_buffer
                accelerated = min(net_flow, debt)
                debt -= accelerated
                net_flow -= accelerated
                total_extra_debt_repayments += accelerated
            cash_addition = min(net_flow, max(0, target_reserve - cash))
            cash += cash_addition
            net_flow -= cash_addition
            investment += net_flow
        else:
            cash += net_flow
            if cash < 0 and investment > 0:
                liquidated = min(investment, -cash)
                investment -= liquidated
                cash += liquidated
            if cash < -0.005 and first_shortfall is None:
                first_shortfall = month
        if cash < 1e-9 and first_reserve_depletion is None:
            first_reserve_depletion = month
        if month in (12, 36, 60, 120, 240, 360, 600) or month == months:
            checkpoints[str(month)] = {
                "financial_assets": round_money(cash + investment),
                "debt": round_money(debt),
                "net_worth": round_money(cash + investment - debt),
                "cash": round_money(cash),
                "invested": round_money(investment),
            }
    return {
        "months": months,
        "annual_net_investment_return_assumption": rate,
        "emergency_target": round_money(target_reserve),
        "starter_emergency_target": round_money(starter_reserve),
        "ending_cash": round_money(cash),
        "ending_invested": round_money(investment),
        "ending_debt": round_money(debt),
        "ending_net_worth": round_money(cash + investment - debt),
        "first_unfunded_shortfall_month": first_shortfall,
        "first_emergency_reserve_depletion_month": first_reserve_depletion,
        "total_cash_receipts": round_money(total_income),
        "total_spending_and_required_payments": round_money(total_consumption),
        "total_accrued_debt_interest": round_money(total_interest),
        "total_extra_debt_repaid": round_money(total_extra_debt_repayments),
        "checkpoints": checkpoints,
    }


def calculate_required_extra_monthly_surplus(profile: dict[str, Any]) -> float | None:
    target = profile["target_net_worth"]
    if target is None:
        return None
    months = 12 * profile["target_years"]
    baseline = simulate(profile, months)
    if baseline["ending_net_worth"] >= target:
        return 0.0
    low, high = 0.0, max(1000.0, float(target) / months)
    for _ in range(70):
        if simulate(profile, months, extra_monthly_cashflow=high)["ending_net_worth"] >= target:
            break
        high *= 2
    else:
        raise ProfileError("目标超出此试算引擎的安全计算范围")
    for _ in range(45):
        mid = (low + high) / 2
        if simulate(profile, months, extra_monthly_cashflow=mid)["ending_net_worth"] >= target:
            high = mid
        else:
            low = mid
    return round_money(high + 0.005)


def build_report(raw: dict[str, Any]) -> dict[str, Any]:
    p = validate(raw)
    expense = (p["monthly_essential_spending"] + p["monthly_discretionary_spending"]
               + p["monthly_required_business_cost"] + p["monthly_tax_reserve"]
               + (p["monthly_debt_payment"] if p["outstanding_debt"] else 0))
    surplus = p["monthly_cash_receipts"] - expense
    basic = p["monthly_essential_spending"] + p["monthly_required_business_cost"] + (
        p["monthly_debt_payment"] if p["outstanding_debt"] else 0
    )
    reserve_target = basic * p["emergency_months"]
    liquidity_gap = max(0.0, reserve_target - p["liquid_cash"])
    months = p["target_years"] * 12
    base = simulate(p, months)
    base_return = float(p["annual_investment_return_assumption"])
    scenario_return_rates = {
        "保守（情景，非概率）": max(-0.95, base_return - 0.07),
        "基准（情景，非预测）": base_return,
        "乐观（情景，非预测）": base_return + 0.03,
    }
    scenarios = {}
    for name, annual_return in scenario_return_rates.items():
        simulation = simulate(p, months, annual_return=annual_return)
        scenarios[name] = {
            "annual_return_assumption": annual_return,
            "end_net_worth": simulation["ending_net_worth"],
            "end_net_worth_in_today_cny": round_money(simulation["ending_net_worth"] / ((1 + p["annual_inflation_assumption"]) ** p["target_years"])),
            "first_unfunded_shortfall_month": simulation["first_unfunded_shortfall_month"],
        }
    stress_profile = copy.deepcopy(p)
    # Illustrative, not an actual probability estimate: zero receipts in months 7–12.
    stress_profile["income_interruption_months"] = sorted(set(p["income_interruption_months"] + list(range(7, 13))))
    stress = simulate(stress_profile, min(12, months))
    warnings = []
    if surplus < 0:
        warnings.append("每月常规现金流为负：优先修复收支缺口，不应以风险投资填补基本生活费。")
    if liquidity_gap > 0:
        warnings.append("应急储备不足：长期风险资产投入须遵守现金安全约束。")
    if p["income_type"] != "stable":
        warnings.append("非固定收入：模型的每月收入是情景假设，不能代替已证明的长期稳定到账记录。")
    if p["outstanding_debt"] > 0 and p["monthly_debt_payment"] * 12 <= p["outstanding_debt"] * p["debt_annual_rate"]:
        warnings.append("当前债务年还款额可能不足以覆盖按模型计算的利息，债务可能增长。")
    if p["outstanding_debt"] > 0 and p["debt_annual_rate"] >= p["high_interest_debt_threshold"]:
        warnings.append("高利率债务示例阈值被触发：模型假设保留初步缓冲后优先提前还款；请检查实际提前还款条件。")
    if stress["first_unfunded_shortfall_month"] is not None:
        warnings.append("6个月收入中断压力情景出现无法由现有金融资产覆盖的资金缺口。")
    if p["target_net_worth"] is not None and base["ending_net_worth"] < p["target_net_worth"]:
        warnings.append("按基准情景无法达成财富目标；所显示的追加金额为每月额外可用净现金流，不是税前薪资。")
    warnings.append("三个收益场景不是发生概率；用户假设的年化收益不等于市场预测或承诺收益；未包含基金具体费率、投资税费和市场历史路径。")
    return {
        "engine_version": "0.1.0",
        "model_type": "确定性月度情景模拟（不是蒙特卡洛）",
        "profile_label": p["label"],
        "currency": "CNY",
        "data_status": "用户提供的情景输入，未连接银行验证",
        "inputs": {key: p[key] for key in (
            "monthly_cash_receipts", "monthly_essential_spending", "monthly_discretionary_spending",
            "monthly_required_business_cost", "monthly_tax_reserve", "monthly_debt_payment",
            "financial_assets", "liquid_cash", "outstanding_debt", "income_type",
            "emergency_months", "target_net_worth", "target_years", "annual_investment_return_assumption",
            "annual_inflation_assumption")},
        "diagnosis": {
            "initial_net_financial_worth": round_money(p["financial_assets"] - p["outstanding_debt"]),
            "monthly_spending_and_required_payments": round_money(expense),
            "monthly_current_cash_surplus": round_money(surplus),
            "saving_rate_of_receipts": round(surplus / p["monthly_cash_receipts"], 4) if p["monthly_cash_receipts"] else None,
            "emergency_reserve_target": round_money(reserve_target),
            "emergency_reserve_shortfall": round_money(liquidity_gap),
            "months_basic_outgo_covered_by_cash": round(p["liquid_cash"] / basic, 2) if basic > 0 else None,
        },
        "goal": {
            "net_worth_target": p["target_net_worth"],
            "deadline_years": p["target_years"],
            "base_case_ending_net_worth": base["ending_net_worth"],
            "base_case_met": base["ending_net_worth"] >= p["target_net_worth"] if p["target_net_worth"] is not None else None,
            "additional_monthly_net_surplus_needed_base_case": calculate_required_extra_monthly_surplus(p),
        },
        "deterministic_scenarios": scenarios,
        "base_case_simulation": base,
        "stress_6_month_income_interruption": {
            "stress_interruption_months": list(range(7, 13)),
            "end_net_worth_12_months": stress["ending_net_worth"],
            "first_unfunded_shortfall_month": stress["first_unfunded_shortfall_month"],
        },
        "limitations": [
            "仅人民币单币种且假定输入收入为实际到账；不能将模拟利润或账户名义额度计为个人资产。",
            "单一聚合债务、固定月供、按月计息；未覆盖多债务利率、保单、社保养老金、真实税率与跨境合规。",
            "债务利率达到默认8%的启发式阈值时，按假设加速还债；无提前还款违约金建模。",
            "假定投资收益按月平滑发生；收益顺序、税收、实际产品交易费与相关性尚未进入计算。",
            "收入中断压力情景不等于事件概率；收益场景同样不代表目标实现概率。",
            "初始多余现金或部分现金流按模型自动重新配置，仅为测算假设，不发生真实转账或交易。",
        ],
        "warnings": warnings,
        "model_assumptions": {
            "three_scenario_annual_returns": scenario_return_rates,
            "month_end_cash_flows": True,
            "emergency_reserve_rule": "默认稳定收入6个月，非稳定收入12个月，可手动修改；启发式，不是法定标准",
            "base_rate": p["annual_investment_return_assumption"],
            "annual_inflation": p["annual_inflation_assumption"],
            "goal_extra_cashflow": "未计新增收入的额外税金或消费，仅示例缺口",
        },
    }


def markdown_report(report: dict[str, Any]) -> str:
    d, g = report["diagnosis"], report["goal"]
    lines = [
        f"# {report['profile_label']} — 财务规划情景报告",
        "", "**重要说明**：这是用户提供数字下的计算场景，并非收入核验、收益承诺或证券投资建议。", "",
        "## 基本诊断",
        f"- 起始净金融资产：¥{d['initial_net_financial_worth']:,.0f}",
        f"- 每月现金结余：¥{d['monthly_current_cash_surplus']:,.0f}",
        f"- 应急储备目标：¥{d['emergency_reserve_target']:,.0f}；缺口：¥{d['emergency_reserve_shortfall']:,.0f}",
        "", "## 目标可行性",
        f"- {g['deadline_years']}年后基准场景净资产：¥{g['base_case_ending_net_worth']:,.0f}",
    ]
    if g["net_worth_target"] is not None:
        lines += [
            f"- 目标：¥{g['net_worth_target']:,.0f}；基准场景：{'达到' if g['base_case_met'] else '未达到'}",
            f"- 还需每月额外可用净现金流（基准场景）：¥{g['additional_monthly_net_surplus_needed_base_case']:,.0f}",
        ]
    lines += ["", "## 情景对比（均为假设，不是概率）", "| 情景 | 假设年化净收益 | 期末净资产 | 折算当前购买力 |", "|---|---:|---:|---:|"]
    for label, s in report["deterministic_scenarios"].items():
        lines.append(f"| {label} | {s['annual_return_assumption']:.0%} | ¥{s['end_net_worth']:,.0f} | ¥{s['end_net_worth_in_today_cny']:,.0f} |")
    lines += ["", "## 收入中断压力测试（第7～12个月无基本收入）", f"- 第12个月期末净资产：¥{report['stress_6_month_income_interruption']['end_net_worth_12_months']:,.0f}", "", "## 风险提示"]
    lines += [f"- {w}" for w in report["warnings"]]
    lines += ["", "## 模型限制"]
    lines += [f"- {item}" for item in report["limitations"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="个人财务规划：透明、可复算的基础模型")
    parser.add_argument("--profile", required=True, help="JSON输入文件路径")
    parser.add_argument("--format", choices=["json", "md"], default="md")
    parser.add_argument("--out", help="保存报告的路径（默认输出到终端）")
    args = parser.parse_args()
    try:
        raw = json.loads(Path(args.profile).read_text(encoding="utf-8"))
        report = build_report(raw)
        content = json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else markdown_report(report)
    except (ProfileError, ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"输入错误：{exc}\n")
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"报告已保存：{out}")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
