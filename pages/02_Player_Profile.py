import streamlit as st
import pandas as pd
from pathlib import Path
from pages.esports import load_csv, find_column, map_win_to_numeric


st.title("선수 프로필")





csv_file = Path("lck.csv")
with st.spinner("데이터 로딩 중..."):
    try:
        df = load_csv(csv_file)
    except Exception as e:
        st.error(f"CSV 로드 오류: {e}")
        st.stop()


player_col = find_column(df, ["player", "playername", "handle", "summoner", "name"])  
team_col = find_column(df, ["team", "teamname", "team_name"])  
pos_col = find_column(df, ["position", "role", "pos"])  
patch_col = find_column(df, ["patch", "patchno", "patch_number"])  
kill_col = find_column(df, ["kills", "kill"])  
death_col = find_column(df, ["deaths", "death"])  
assist_col = find_column(df, ["assists", "assist"])  
cs_col = find_column(df, ["cs", "creeps", "cs_total"])  
gold_col = find_column(df, ["gold", "goldearned", "earnedgold"])  
gameid_col = find_column(df, ["gameid", "game_id"])  
win_col = find_column(df, ["win", "result"])  


filters = st.sidebar
filters.subheader("필터")

if patch_col is not None:
    patches = ["(전체)"] + list(pd.unique(df[patch_col]))
    sel_patch = filters.selectbox("패치", patches)
    if sel_patch != "(전체)":
        df = df[df[patch_col] == sel_patch]

if team_col is not None:
    teams = ["(전체)"] + sorted(df[team_col].dropna().unique().tolist())
    sel_team = filters.selectbox("팀", teams)
    if sel_team != "(전체)":
        df = df[df[team_col] == sel_team]

if pos_col is not None:
    positions = ["(전체)"] + sorted(df[pos_col].dropna().unique().tolist())
    sel_pos = filters.selectbox("포지션", positions)
    if sel_pos != "(전체)":
        df = df[df[pos_col] == sel_pos]


if player_col is None:
    st.warning("선수 컬럼을 찾지 못했습니다. 원본 데이터 미리보기를 표시합니다.")
    st.dataframe(df.head(50), width='stretch')
    st.stop()

players = sorted(df[player_col].dropna().unique().tolist())
if 'selected_player' not in st.session_state:
    sel_player = st.selectbox("선수 선택", players, index=0 if players else None)
else:
    selected_player = st.session_state['selected_player']
    sel_player = st.selectbox('선수 선택', players, index=players.index(selected_player) if players else None)


if not players:
    st.info("선수 데이터가 없습니다.")
    st.stop()

work_df = df[df[player_col] == sel_player].copy()

st.subheader(f"{sel_player}")

# KDA 및 기본 지표
if kill_col and death_col and assist_col:
    kills = work_df[kill_col].fillna(0)
    deaths = work_df[death_col].fillna(0)
    assists = work_df[assist_col].fillna(0)
    kda = (kills + assists) / deaths.replace(0, pd.NA)
else:
    kda = pd.Series(dtype=float)

cols = st.columns(4)
with cols[0]:
    st.metric("경기 수", len(work_df))
with cols[1]:
    st.metric('사용한 챔피언 수', work_df.champion.nunique())

with cols[2]:
    if not kda.empty:
        st.metric("평균 KDA", f"{kda.mean():.2f}")
with cols[3]:
    if win_col:
        win_series = map_win_to_numeric(work_df[win_col])
        win_rate = win_series.mean() * 100
        st.metric("승률", f"{win_rate:.1f}%")

st.subheader("챔피언 요약")
st.write("픽,승률 상위 7개 챔피언")

champion_df = work_df.groupby('champion').apply(
    lambda x: pd.Series({
        '픽 수': len(x),
        '승률': f'{x.result.mean()*100:.1f}%',
        'kill': f'{x.kills.mean():.2f}',
        'death': f'{x.deaths.mean():.2f}',
        'assist': f'{x.assists.mean():.2f}',
        '10분골드차': f'{x.golddiffat10.mean():.2f}',
        '15분골드차': f'{x.golddiffat15.mean():.2f}',
        '20분골드차': f'{x.golddiffat20.mean():.2f}',
        '25분골드차': f'{x.golddiffat25.mean():.2f}',
    }), include_groups=False
).sort_values(['픽 수', '승률'], ascending=[False, False])
st.dataframe(champion_df.head(7), width='stretch')


st.subheader("경기별 기록")
show_cols = []
for c in [patch_col, team_col, pos_col, kill_col, death_col, assist_col, cs_col, gold_col, win_col]:
    if c and c in work_df.columns:
        show_cols.append(c)
if player_col in work_df.columns:
    show_cols = [player_col] + show_cols

st.dataframe(work_df[show_cols].head(200), width='stretch')


