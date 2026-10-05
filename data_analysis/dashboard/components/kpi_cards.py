import streamlit as st

from dashboard.utils.theme import render_html


CARD_STYLES = [
    ("kpi-lavender", "✦"),
    ("kpi-pink", "◉"),
    ("kpi-turquoise", "⌁"),
    ("kpi-yellow", "✧"),
]


def display_kpi(
    title,
    value,
    description="",
    index=0,
):
    style, icon = CARD_STYLES[index % len(CARD_STYLES)]

    render_html(
        f"""
        <div class="kpi-card {style} animate">

            <div class="kpi-icon">
                {icon}
            </div>

            <div class="kpi-label">
                {title}
            </div>

            <div class="kpi-value">
                {value}
            </div>

            <div class="kpi-description">
                {description}
            </div>

        </div>
        """,
    )


def display_kpi_row(kpis):
    columns = st.columns(len(kpis), gap="medium")

    for index, (column, kpi) in enumerate(zip(columns, kpis)):
        with column:
            display_kpi(
                title=kpi["title"],
                value=kpi["value"],
                description=kpi.get("description", ""),
                index=index,
            )