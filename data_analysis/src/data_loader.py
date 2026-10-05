import os
import pandas as pd


def load_csv(file_path):
    """
    Charge un fichier CSV.

    Parameters
    ----------
    file_path : str
        Chemin vers le fichier CSV.

    Returns
    -------
    pandas.DataFrame
        Données chargées.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Fichier introuvable : {file_path}"
        )

    return pd.read_csv(file_path)


def load_all_data(data_path):
    """
    Charge tous les fichiers CSV du projet.

    Parameters
    ----------
    data_path : str
        Chemin vers le dossier contenant les CSV.

    Returns
    -------
    dict
        Dictionnaire contenant tous les DataFrames.
    """

    files = {
        "patients": "patients.csv",
        "games": "games.csv",
        "exercises": "exercises.csv",
        "exercise_levels": "exercise_levels.csv",
        "patient_exercises": "patient_exercises.csv",
        "level_changes": "level_changes.csv",
        "sessions": "sessions.csv",
        "results": "results.csv"
    }

    datasets = {}

    for name, filename in files.items():

        file_path = os.path.join(data_path, filename)

        datasets[name] = load_csv(file_path)

    return datasets