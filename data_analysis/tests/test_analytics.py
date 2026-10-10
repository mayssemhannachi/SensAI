import pandas as pd

from dashboard.utils import analytics as a


def _history(scores, success=None, start="2026-09-01", step_days=2, game="G"):
    dates = pd.date_range(start, periods=len(scores), freq=f"{step_days}D")
    success = success or [60] * len(scores)
    return pd.DataFrame({
        "patient_id": 1, "session_id": range(len(scores)), "session_date": dates, "score": scores,
        "success_rate": success, "game_name": game, "level": 1, "duration_min": 8.0,
        "progression": None, "patient_name": "A B",
    })


def test_slope_needs_three_points():
    assert a.score_slope(pd.Series([50, 60])) is None
    assert abs(a.score_slope(pd.Series([50, 55, 60])) - 5) < 1e-9


def test_declining_patient_is_flagged():
    history = _history([70, 66, 62, 58, 54])
    alerts = a.patient_alerts(history, history["session_date"].max())
    assert [x.label for x in alerts] == ["Score en baisse"]
    assert a.patient_status(history, alerts) == "À surveiller"


def test_low_success_and_inactivity():
    history = _history([60, 60, 60], success=[50, 45, 30])
    reference = history["session_date"].max() + pd.Timedelta(days=30)
    labels = {x.label for x in a.patient_alerts(history, reference)}
    assert labels == {"Réussite faible", "Inactif"}


def test_progressing_and_new_status():
    history = _history([50, 55, 60, 65])
    assert a.patient_status(history, []) == "En progression"
    assert a.patient_status(history.iloc[0:0], []) == "Nouveau"


def test_period_filters_and_previous_period():
    history = _history(list(range(40)), step_days=1)
    reference = history["session_date"].max()
    assert len(a.filter_period(history, 7, reference)) == 7
    assert len(a.previous_period(history, 7, reference)) == 7
    assert len(a.filter_period(history, None, reference)) == 40


def test_global_kpis_delta():
    cur = _history([60, 70], success=[50, 70])
    prev = _history([50, 50], success=[40, 40])
    k = a.global_kpis(cur, prev)
    assert k["success"]["value"] == 60 and k["success"]["delta"] == 20
    assert a.global_kpis(cur, prev.iloc[0:0])["score"]["delta"] is None


def test_distribution_counts_all_sessions():
    dist = a.success_distribution(_history([1] * 4, success=[10, 45, 80, 100]))
    assert dist["count"].sum() == 4
    assert dist.set_index("range").loc["≥ 80", "count"] == 2


def test_insights_are_generated():
    history = pd.concat([_history([50, 55, 60], game="A"), _history([40, 42, 44], game="B")])
    history = history.sort_values("session_date").reset_index(drop=True)
    insights = a.patient_insights(history, history["session_date"].max())
    assert 3 <= len(insights) <= 4
    import re
    assert not any(re.search(r"\d\.\d", i.text) for i in insights)  # format FR (virgule)


def test_shoulder_abduction_signals():
    """Gardien des Lucioles : progression d'abduction, baisse et compensations."""
    history = _history([60] * 8)
    history["abduction_mean_peak"] = [70, 72, 74, 76, 78, 84, 86, 88]
    history["abduction_max"] = history["abduction_mean_peak"] + 5
    history["compensations"] = [1, 1, 0, 1, 0, 0, 1, 0]
    history["target_angle"] = 80
    reference = history["session_date"].max()
    assert a.patient_alerts(history, reference) == []
    assert a.patient_status(history, []) == "En progression"
    assert any(i.title == "Abduction de l’épaule" for i in a.patient_insights(history, reference))

    history["abduction_mean_peak"] = [90, 90, 90, 90, 90, 80, 80, 80]
    history["compensations"] = [0, 0, 0, 0, 0, 4, 3, 5]
    labels = {x.label for x in a.patient_alerts(history, reference)}
    assert labels == {"Abduction en baisse", "Compensations"}


def test_sequence_memory_signals():
    """Danse des Lucioles : progression de la séquence et erreurs d'ordre."""
    history = _history([60] * 8)
    history["max_sequence"] = [2, 2, 2, 3, 3, 3, 4, 4]
    history["sequence_errors"] = [3, 2, 2, 1, 1, 1, 0, 1]
    history["hints_used"] = [1, 1, 0, 0, 0, 0, 0, 0]
    reference = history["session_date"].max()
    assert a.patient_alerts(history, reference) == []
    assert a.patient_status(history, []) == "En progression"
    assert any(i.title == "Mémoire et coordination" for i in a.patient_insights(history, reference))
    history["sequence_errors"] = [0, 0, 0, 0, 0, 5, 4, 6]
    assert {x.label for x in a.patient_alerts(history, reference)} == {"Erreurs de séquence"}
