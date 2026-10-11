"""Deterministic portfolio risk, fees and drift checks. Not an investment adviser."""
from __future__ import annotations
import math


def _assert_psd(matrix:list[list[float]], eps:float=1e-9) -> None:
    """General semidefinite Cholesky; zero pivot must have zero corresponding residuals."""
    n=len(matrix)
    L=[[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1):
            residual=float(matrix[i][j])-sum(L[i][k]*L[j][k] for k in range(j))
            if i==j:
                if residual<-eps:raise ValueError('covariance is not positive semidefinite')
                L[i][j]=math.sqrt(max(0.0,residual))
            elif L[j][j]>eps:
                L[i][j]=residual/L[j][j]
            elif abs(residual)>eps:
                raise ValueError('covariance is not positive semidefinite')


def portfolio_diagnostics(config: dict, current_weights: dict | None = None) -> dict:
    assets = config.get('assets')
    if not isinstance(assets, list) or not (1 <= len(assets) <= 15):
        raise ValueError('portfolio must contain 1..15 assets')
    names, weights, returns, costs = [], [], [], []
    for row in assets:
        name = row.get('name')
        if not isinstance(name, str) or not name or name in names:
            raise ValueError('asset names must be unique and nonempty')
        w = float(row['weight']); r = float(row['assumed_nominal_return']); c = float(row.get('expense_ratio', 0))
        if any(not math.isfinite(x) for x in (w,r,c)) or not 0 <= w <= 1 or not -0.95 < r < 3 or not 0 <= c < 1:
            raise ValueError('invalid weight/return/fee')
        names.append(name);weights.append(w);returns.append(r);costs.append(c)
    if abs(sum(weights)-1) > 1e-8:
        raise ValueError('target portfolio weights must sum to 1')
    cov = config.get('annual_covariance')
    var = None
    if cov is not None:
        if len(cov) != len(names) or any(len(row)!=len(names) for row in cov):
            raise ValueError('annual covariance must be NxN')
        if any(not math.isfinite(float(v)) for row in cov for v in row):
            raise ValueError('covariance cannot be non-finite')
        for i in range(len(names)):
            if float(cov[i][i]) < 0:
                raise ValueError('negative covariance diagonal')
            for j in range(i+1,len(names)):
                if abs(float(cov[i][j])-float(cov[j][i])) > 1e-10:
                    raise ValueError('covariance must be symmetric')
        var = sum(weights[i]*weights[j]*float(cov[i][j]) for i in range(len(names)) for j in range(len(names)))
        if var < -1e-10:
            raise ValueError('negative portfolio variance')
        _assert_psd(cov)
    mean = sum(w*r for w,r in zip(weights,returns))
    weighted_fee = sum(w*c for w,c in zip(weights,costs))
    drift = []
    if current_weights is not None:
        if set(current_weights)!=set(names) or abs(sum(float(v) for v in current_weights.values())-1)>1e-8:
            raise ValueError('current_weights missing names or do not sum to 1')
        for name, w in zip(names,weights):
            actual=float(current_weights[name])
            if not 0<=actual<=1:
                raise ValueError('current weight invalid')
            drift.append({'name': name, 'target': w, 'actual': actual, 'drift_pp': round((actual-w)*100, 3)})
    return {
        'status': 'RESEARCH_SCENARIO_NOT_OPTIMIZED_OR_PERSONALIZED', 'asset_names': names,
        'assumed_weighted_gross_return': round(mean,8),
        'weighted_expense_ratio_only': round(weighted_fee,8),
        'assumed_net_of_expense_ratio_approximation': round(mean-weighted_fee,8),
        'portfolio_volatility_from_provided_covariance': None if var is None else round(math.sqrt(max(0,var)),8),
        'drift': drift,
        'research_needed': [
            'Expected returns and covariance not inferred from ticker or history',
            'Taxes, market impact, bid-ask spread, FX, transaction costs and fund domicile not modeled',
            'Assets with different liquidity horizons must be analyzed as separate funding buckets',
        ],
    }
