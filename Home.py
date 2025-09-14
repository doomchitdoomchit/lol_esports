import streamlit as st
import pandas as pd
from pathlib import Path


st.set_page_config(page_title="LOL Esports - Home", layout="wide")
st.title("LOL Esports Dashboard - Home")


@st.cache_data(show_spinner=False)
def load_lck_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
    df = pd.read_csv(csv_path, index_col=0)
    return df


csv_file = Path("lck.csv")

with st.spinner("lck.csv 로딩 중..."):
    try:
        lck_df = load_lck_csv(csv_file)
        st.success("lck.csv 로드 완료")
        st.subheader("미리보기")
        st.dataframe(lck_df.head(50), width='stretch')
        st.caption(f"행 수: {len(lck_df):,}")
    except FileNotFoundError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"CSV 로드 중 오류가 발생했습니다: {e}")


st.title("메인 토픽")
st.write("이 페이지는 상위 개념을 다룹니다.")