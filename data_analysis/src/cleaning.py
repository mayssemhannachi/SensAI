import pandas as pd


def convert_datetime_columns(datasets):
    """
    Convertit les colonnes de dates des différents DataFrames.
    """

    date_columns = {
        "patients": ["date_of_birth", "created_at"],
        "patient_exercises": ["assigned_at"],
        "level_changes": ["changed_at"],
        "sessions": ["session_date"]
    }

    for dataset_name, columns in date_columns.items():

        if dataset_name not in datasets:
            continue

        df = datasets[dataset_name]

        for column in columns:

            if column in df.columns:
                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

    return datasets


def strip_text_columns(df):
    """
    Supprime les espaces inutiles dans les colonnes texte.
    """

    df = df.copy()

    text_columns = df.select_dtypes(
        include=["object"]
    ).columns

    for column in text_columns:
        df[column] = df[column].str.strip()

    return df


def remove_duplicates(df):
    """
    Supprime les lignes complètement dupliquées.
    """

    df = df.copy()

    return df.drop_duplicates()


def clean_dataframe(df):
    """
    Applique les opérations générales de nettoyage.
    """

    df = df.copy()

    df = strip_text_columns(df)

    df = remove_duplicates(df)

    return df