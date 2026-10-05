import plotly.express as px
import plotly.graph_objects as go

from dashboard.utils.theme import get_colors


COLORS = get_colors()


def clean_chart(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            family="DM Sans",
            color=COLORS["text"],
        ),

        margin=dict(
            l=10,
            r=10,
            t=45,
            b=10,
        ),

        hoverlabel=dict(
            bgcolor=COLORS["surface"],
            font_size=13,
            font_family="DM Sans",
        ),

        legend=dict(
            title_text="",
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor=COLORS["border"],
        zeroline=False,
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLORS["border"],
        zeroline=False,
    )

    return fig


def global_score_evolution_chart(df):
    fig = px.line(
        df,
        x="session_date",
        y="mean_score",
        markers=True,
        labels={
            "session_date": "Date",
            "mean_score": "Score moyen",
        },
    )

    fig.update_traces(
        line=dict(
            color=COLORS["score"],
            width=4,
        ),
        marker=dict(
            color=COLORS["pink"],
            size=9,
            line=dict(
                color=COLORS["score"],
                width=2,
            ),
        ),
    )

    return clean_chart(fig)


def global_progression_chart(df):
    fig = px.line(
        df,
        x="session_date",
        y="mean_progression",
        markers=True,
        labels={
            "session_date": "Date",
            "mean_progression": "Progression moyenne (%)",
        },
    )

    fig.update_traces(
        line=dict(
            color=COLORS["progression"],
            width=4,
        ),
        marker=dict(
            color=COLORS["turquoise"],
            size=8,
        ),
    )

    return clean_chart(fig)


def success_distribution_chart(df):
    fig = px.bar(
        df,
        x="range",
        y="count",
        labels={
            "range": "Taux de réussite",
            "count": "Séances",
        },
    )

    fig.update_traces(
        marker_color=COLORS["turquoise"],
        marker_line_width=0,
        opacity=0.9,
    )

    return clean_chart(fig)


def game_performance_chart(df):
    fig = px.bar(
        df,
        x="name_game",
        y="mean_success_rate",
        labels={
            "name_game": "Jeu",
            "mean_success_rate": "Réussite moyenne (%)",
        },
    )

    fig.update_traces(
        marker_color=[
            COLORS["pink"],
            COLORS["turquoise"],
            COLORS["yellow"],
        ][:len(df)],
        marker_line_width=0,
    )

    return clean_chart(fig)


def score_evolution_chart(df):
    fig = px.line(
        df.sort_values("session_date"),
        x="session_date",
        y="score",
        markers=True,
        labels={
            "session_date": "Séance",
            "score": "Score",
        },
    )

    fig.update_traces(
        line=dict(
            color=COLORS["score"],
            width=4,
        ),
        marker=dict(
            color=COLORS["pink"],
            size=9,
        ),
    )

    return clean_chart(fig)


def success_rate_chart(df):
    fig = px.line(
        df.sort_values("session_date"),
        x="session_date",
        y="success_rate",
        markers=True,
        labels={
            "session_date": "Séance",
            "success_rate": "Réussite (%)",
        },
    )

    fig.update_traces(
        line=dict(
            color=COLORS["turquoise_dark"],
            width=4,
        ),
        marker=dict(
            color=COLORS["turquoise"],
            size=9,
        ),
    )

    return clean_chart(fig)


def progression_chart(df):
    fig = go.Figure()

    values = df.sort_values("session_date")

    fig.add_trace(
        go.Bar(
            x=values["session_date"],
            y=values["progression"],
            marker_color=[
                COLORS["turquoise"]
                if value >= 0
                else COLORS["pink"]
                for value in values["progression"].fillna(0)
            ],
            hovertemplate=(
                "Date : %{x}<br>"
                "Progression : %{y:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        yaxis_title="Progression (%)",
        xaxis_title="Séance",
    )

    return clean_chart(fig)