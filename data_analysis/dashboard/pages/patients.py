import pandas as pd
import streamlit as st

from dashboard import navigation
from dashboard.components.patient_table import patient_card_html
from dashboard.components.ui import card, empty_state, page_header, render_html
from dashboard.utils import analytics
from dashboard.utils.data import load_dataset

SORTS = {
    "Priority (needs attention first)": (["status_rank", "last_session"], [True, False]),
    "Last session": (["last_session"], [False]),
    "Name": (["last_name", "first_name"], [True, True]),
    "Success (ascending)": (["recent_success"], [True]),
    "Number of sessions": (["sessions"], [False]),
}

COLUMNS_PER_ROW = 3


def show_patients():
    data = load_dataset()
    reference = data.reference_date

    page_header(
        "Therapeutic follow-up",
        "My patients",
        "Find the children you follow, their status and their latest performance.",
        meta=f"{len(data.patients)} patient(s)",
    )

    if data.patients.empty:
        empty_state("👤", "No patients registered", "Create a first profile to start follow-up.")
        if st.button("＋ Add a patient", type="primary"):
            navigation.go("add_patient")
        return

    overview = analytics.patient_overview(data.patients, data.sessions, reference)

    # --------------------------------------------------------
    # FILTRES
    # --------------------------------------------------------
    search_col, status_col, sort_col = st.columns([2, 1.6, 1.3], vertical_alignment="bottom")
    with search_col:
        query = st.text_input(
            "Search", placeholder="🔎  Name or patient code…", key="patients_search"
        )
    with status_col:
        statuses = [s for s in analytics.STATUS_ORDER if s in set(overview["status"])]
        selected_status = st.multiselect(
            "Status", statuses, key="patients_status_filter", placeholder="All statuses"
        )
    with sort_col:
        sort_label = st.selectbox("Sort by", list(SORTS), key="patients_sort")

    filtered = overview
    if query.strip():
        q = query.strip().lower()
        haystack = (
            filtered["full_name"].str.lower() + " " + filtered["patient_code"].astype(str).str.lower()
        )
        filtered = filtered[haystack.str.contains(q, regex=False, na=False)]
    if selected_status:
        filtered = filtered[filtered["status"].isin(selected_status)]
    columns, ascending = SORTS[sort_label]
    filtered = filtered.sort_values(columns, ascending=ascending, na_position="last")

    # Résumé par statut
    counts = overview["status"].value_counts()
    chips = " ".join(
        f"<span class='kk-badge {tone}'>{status} · {counts.get(status, 0)}</span>"
        for status, tone in [("Needs attention", "warning"), ("Improving", "good"),
                             ("Stable", "info"), ("New", "neutral")]
        if counts.get(status, 0)
    )
    render_html(
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"gap:10px;flex-wrap:wrap;margin:6px 0 14px'>"
        f"<div style='display:flex;gap:6px;flex-wrap:wrap'>{chips}</div>"
        f"<div style='font-size:12.5px;color:#667085'>{len(filtered)} result(s)</div></div>"
    )

    if filtered.empty:
        empty_state("🔎", "No matching patients", "Change the search or filters.")
        return

    # --------------------------------------------------------
    # GRILLE DE CARTES
    # --------------------------------------------------------
    rows = list(filtered.itertuples(index=False))
    for start in range(0, len(rows), COLUMNS_PER_ROW):
        columns = st.columns(COLUMNS_PER_ROW, gap="medium")
        for column, row in zip(columns, rows[start:start + COLUMNS_PER_ROW]):
            record = pd.Series(row._asdict())
            with column:
                with card(f"patient-{record['id']}"):
                    render_html(patient_card_html(record, reference))
                    if st.button("View record →", key=f"open_patient_{record['id']}", width="stretch"):
                        navigation.open_patient(record["id"])

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------
    export = filtered[[
        "patient_code", "full_name", "age", "status", "sessions", "last_session",
        "last_score", "recent_success", "trend",
    ]].rename(columns={
        "patient_code": "code", "full_name": "patient", "age": "age", "status": "status",
        "sessions": "sessions", "last_session": "last_session", "last_score": "last_score",
        "recent_success": "recent_success", "trend": "score_trend_per_session",
    })
    st.write("")
    st.download_button(
        "⤓ Export list (CSV)",
        export.to_csv(index=False).encode("utf-8-sig"),
        file_name="sensai_patients.csv",
        mime="text/csv",
    )
