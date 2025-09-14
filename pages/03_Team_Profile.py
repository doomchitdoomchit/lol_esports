import streamlit as st
import pandas as pd
from pathlib import Path
from pages.esports import load_csv, find_column, map_win_to_numeric


st.title("팀 프로필")




csv_file = Path("lck.csv")
with st.spinner("데이터 로딩 중..."):
    try:
        df = load_csv(csv_file)
    except Exception as e:
        st.error(f"CSV 로드 오류: {e}")
        st.stop()


team_col = find_column(df, ["team", "teamname", "team_name"])  
opp_team_col = find_column(df, ["opponent", "oppteam", "opponent_team", "enemy", "opponentname"])  
patch_col = find_column(df, ["patch", "patchno", "patch_number"])  
gameid_col = find_column(df, ["gameid", "game_id"])  
win_col = find_column(df, ["win", "result"])  
kill_col = find_column(df, ["kills", "kill"])  
death_col = find_column(df, ["deaths", "death"])  
assist_col = find_column(df, ["assists", "assist"])  
gold_col = find_column(df, ["gold", "goldearned", "earnedgold"])  


if team_col is None:
    st.warning("팀 컬럼을 찾지 못했습니다. 원본 데이터를 표시합니다.")
    st.dataframe(df.head(50), width='stretch')
    st.stop()

filters = st.sidebar
filters.subheader("필터")

if patch_col is not None:
    patches = ["(전체)"] + list(pd.unique(df[patch_col]))
    sel_patch = filters.selectbox("패치", patches)
    if sel_patch != "(전체)":
        df = df[df[patch_col] == sel_patch]

teams = ["(전체)"] + sorted(df[team_col].dropna().unique().tolist())
sel_team = filters.selectbox("팀 선택", teams)
if sel_team == "(전체)":
    st.info("팀을 선택해주세요.")
    st.stop()

work_df = df[df[team_col] == sel_team].copy()


st.subheader(f"{sel_team} 요약")

unique_per_game = st.checkbox("게임당 1행으로 중복 제거", value=False)
if unique_per_game and gameid_col is not None:
    work_df = work_df.drop_duplicates(subset=[gameid_col, team_col])

# 승률 계산
win_rate = None
if win_col is not None:
    win_series = map_win_to_numeric(work_df[win_col])
    win_rate = win_series.mean() * 100

cols = st.columns(3)
with cols[0]:
    st.metric("경기 수", len(work_df))
with cols[1]:
    if win_rate is not None:
        st.metric("승률", f"{win_rate:.1f}%")
with cols[2]:
    if gold_col:
        st.metric("평균 골드", f"{work_df[gold_col].mean():.0f}")


st.subheader("상대팀 상대 전적")
if opp_team_col is not None and win_col is not None:
    opp_group = work_df.copy()
    opp_group["win_num"] = map_win_to_numeric(opp_group[win_col])
    table = opp_group.groupby(opp_team_col).agg(
        경기수=(win_col, "count"),
        승리=("win_num", "sum"),
    ).reset_index()
    table["패배"] = table["경기수"] - table["승리"]
    table["승률"] = (table["승리"] / table["경기수"]).round(3)
    table = table.rename(columns={opp_team_col: "상대팀"}).sort_values(["승률", "경기수"], ascending=[False, False])
    st.dataframe(table, width='stretch')
else:
    st.info("상대팀/승패 컬럼을 찾지 못해 상대 전적 테이블을 생략했습니다.")


st.subheader("경기별 기록")
show_cols = []
for c in [patch_col, team_col, opp_team_col, kill_col, death_col, assist_col, gold_col, win_col]:
    if c and c in work_df.columns:
        show_cols.append(c)
st.dataframe(work_df[show_cols].head(200), width='stretch')


