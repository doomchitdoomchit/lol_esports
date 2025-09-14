from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Optional
import streamlit as st


@st.cache_data(show_spinner=False)
def load_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
    df = pd.read_csv(csv_path, index_col=0)
    return df


def find_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    lower_map = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    for c in df.columns:
        lc = c.lower()
        if any(name in lc for name in candidates):
            return c
    return None


def map_win_to_numeric(series: pd.Series) -> pd.Series:
    s = series
    # 우선 문자열 W/L 매핑 시도
    mapped = s.astype(str).str.strip().str.upper().map({"W": 1, "L": 0})
    if mapped.isna().any():
        mapped = pd.to_numeric(s, errors="coerce")
    return mapped.fillna(0).astype(int)


