"""Carte patient utilisée dans la liste « Patients »."""

from __future__ import annotations

import pandas as pd

from dashboard.components.ui import (
    alert_badges,
    avatar,
    badge,
    days_ago,
    esc,
    fmt_number,
    sparkline,
    status_badge,
)
from dashboard.utils.theme import METRIC_COLORS


def patient_card_html(row: pd.Series, reference: pd.Timestamp) -> str:
    age = f"{int(row['age'])} yrs" if pd.notna(row["age"]) else "Age n/a"
    code = esc(row["patient_code"]) or f"#{row['id']}"
    trend = row["trend"]
    trend_class = "" if trend is None or pd.isna(trend) else ("pos" if trend >= 1 else "neg" if trend <= -1 else "")
    trend_text = fmt_number(trend, 1, signed=True) if trend is not None and pd.notna(trend) else "—"
    return f"""
    <div class="kk-pcard-head">
      {avatar(row['first_name'], row['last_name'], seed=row['id'])}
      <div>
        <div class="kk-pcard-name">{esc(row['full_name'])}</div>
        <div class="kk-pcard-meta">{code} · {age}</div>
      </div>
    </div>
    <div class="kk-alerts" style="margin-top:10px">{status_badge(row['status'])}{alert_badges(row['alerts'])}{'' if row.get('has_account', True) else badge('Account not activated', 'neutral')}</div>
    <div class="kk-pcard-stats">
      <div class="kk-stat"><div class="kk-stat-label">Score</div>
        <div class="kk-stat-value">{fmt_number(row['last_score'])}</div></div>
      <div class="kk-stat"><div class="kk-stat-label">Success</div>
        <div class="kk-stat-value">{fmt_number(row['recent_success'], suffix='%')}</div></div>
      <div class="kk-stat" title="Average score change per session (last 5 sessions)"><div class="kk-stat-label">Trend</div>
        <div class="kk-stat-value {trend_class}">{trend_text}</div></div>
    </div>
    <div class="kk-pcard-foot">
      <span>{row['sessions']} session(s) · {esc(days_ago(row['last_session'], reference))}</span>
      {sparkline(row['scores'], METRIC_COLORS['score'])}
    </div>
    """
