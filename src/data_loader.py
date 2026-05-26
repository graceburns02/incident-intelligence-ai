from __future__ import annotations

import pandas as pd


def load_incidents_csv(file) -> pd.DataFrame:
    return pd.read_csv(file)


def load_sample_dataset(path: str = "sample_data/incidents.csv") -> pd.DataFrame:
    return pd.read_csv(path)
