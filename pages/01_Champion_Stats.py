import streamlit as st
import pandas as pd
from pathlib import Path
from pages.esports import load_csv, find_column, map_win_to_numeric
import plotly.graph_objects as go


st.title("챔피언 통계")


csv_file = Path("lck.csv")

with st.spinner("데이터 로딩 중..."):
    try:
        df = load_csv(csv_file)
    except Exception as e:
        st.error(f"CSV 로드 오류: {e}")
        st.stop()


@st.dialog("챔피언 정보", width='large')
def vote(item):
    st.subheader(f"{item}")
    col1, col2, col3 = st.columns([2, 2, 1])
    selected_df = df[df.champion == item]
    with col1:
        gold = selected_df[['golddiffat10', 'golddiffat15', 'golddiffat20', 'golddiffat25']].agg(['mean', 'std']).T
        xp = selected_df[['xpdiffat10', 'xpdiffat15', 'xpdiffat20', 'xpdiffat25']].agg(['mean', 'std']).T
        cs = selected_df[['csdiffat10', 'csdiffat15', 'csdiffat20', 'csdiffat25']].agg(['mean', 'std']).T
        gold.index = ['10', '15', '20', '25']
        # gold['upper'] = gold['mean'] + gold['std']
        # gold['lower'] = gold['mean'] - gold['std']
        xp.index = ['10', '15', '20', '25']
        # xp['upper'] = xp['mean'] + xp['std']
        # xp['lower'] = xp['mean'] - xp['std']
        cs.index = ['10', '15', '20', '25']
        # cs['upper'] = cs['mean'] + cs['std']
        # cs['lower'] = cs['mean'] - cs['std']

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=gold.index,
            y=gold['mean'],
            mode='lines',
            name='gold',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=xp.index,
            y=xp['mean'],
            mode='lines',
            name='xp',
            line=dict(color='green')
        ))
        fig.add_trace(go.Scatter(
            x=cs.index,
            y=cs['mean'],
            mode='lines',
            name='cs',
            yaxis='y2',
            line=dict(color='orange')
        ))
        fig.update_layout(
            title=f'{item} 5분 단위 gold/xp/cs gap',
            xaxis_title='Time',
            yaxis=dict(
                title='gold/xp',
                zeroline=True,
            ),
            yaxis2=dict(
                title='cs',
                overlaying='y',
                zeroline=True,
                side='right'
            )
        )
        # select_position = selected_df.position.value_counts().to_frame()
        # fig = px.pie(select_position, values='count', names=select_position.index, title=f'Position of {item}')
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader(f"{item}의 상대 챔피언 승률")
        verse_list = []
        for _ in selected_df[['gameid', 'position']].iterrows():
            new_df = df[(df.gameid == _[1].gameid) & (df.position == _[1].position)]
            verse_list.append(new_df)

        verse_df = pd.concat(verse_list)
        verse_df = verse_df[verse_df.champion != item].groupby('champion').apply(lambda g: pd.Series({
            '픽 수': len(g),
            '승리': int(len(g) - g.result.sum()),
            '패배': int(g.result.sum())
        }), include_groups=False
        ).reset_index().rename(columns={'champion': "상대챔피언"})
        verse_df["승률"] = (verse_df["승리"] / verse_df["픽 수"]).round(3)
        verse_df = verse_df.sort_values(["픽 수", "승률"], ascending=[False, False])
        st.dataframe(
            verse_df, width='stretch',
        )

        # if verse_select:
        #     selected_verse_index = verse_select[0]
        #     temp_result_df = verse_df.reset_index(drop=True)
        #     selected_champion = temp_result_df.loc[selected_verse_index[0], '상대챔피언']
        #     if isinstance(selected_champion, str):
        #         rerun_index = result_df[result_df.챔피언 == selected_champion].index[0]
        #         st.session_state.verse_selection['selection']['cells'] = (rerun_index, None)
        #         st.session_state.show_dialog = False
        #         st.rerun()
        #         # st.switch_page('pages/01_Champion_Stats.py')

    with col3:
        st.subheader(f"{item}, 선수별 승률")
        groupby_champion = (selected_df.groupby('playername').result.mean().to_frame()
            .sort_values('result', ascending=False)).reset_index().rename({'result': '승률'})#.style.format("{:.2%}"))
        groupby_champion.result = groupby_champion.result.apply(lambda x: '{:.2f}%'.format(x*100))
        st.dataframe(groupby_champion, width='stretch',
            selection_mode="single-cell", on_select="rerun", hide_index=True, key="player_selection"
        )
        player_select = st.session_state.player_selection['selection']['cells']
        if player_select:
            selected_player_index = player_select[0]
            selected_player = groupby_champion.loc[selected_player_index[0], 'playername']
            st.session_state['selected_player'] = selected_player
            st.switch_page('pages/02_player_Profile.py')



# 컬럼 추론
pick_col = ['pick1', 'pick2', 'pick3', 'pick4', 'pick5']
ban_col = ['ban1', 'ban2', 'ban3', 'ban4', 'ban5']
champ_col = find_column(df, ["champ", "champion", "character"])  # 가능한 후보
win_col = find_column(df, ["win", "result"])  # 1/0 또는 W/L 형태 예상
gameid_col = find_column(df, ["gameid", "game_id", "matchid", "match_id"])  # 중복 제거용
team_col = find_column(df, ["team", "teamname", "team_name"])  
patch_col = find_column(df, ["patch", "patchno", "patch_number"])  


filters = st.sidebar
filters.subheader("필터")

button_explain = st.sidebar.button("사용 방법")


@st.dialog("사용 방법", width='large')
def tutorial():
    st.subheader(f"1. 챔피언 이름 클릭시")
    st.write("- 챔피언 이름 클릭시 5분단위 지표gap, 상대 챔피언별 승률, 선수별 승률이 나옵니다.")
    st.write('')
    st.subheader(f"2. 챔피언 이름 클릭 후 dialog창")
    st.write("- 선수별 승률에서 선수이름 클릭시 선수프로필로 넘어갑니다.")
    st.write('')
    st.write("**기본 정렬은 픽 수 -> 승률 순입니다.**")


if button_explain:
    tutorial()

# 패치 필터 (있는 경우만)
if patch_col is not None:
    patches = ["(전체)"] + list(pd.unique(df[patch_col]))
    sel_patch = filters.selectbox("패치", patches)
    if sel_patch != "(전체)":
        df = df[df[patch_col] == sel_patch]

# 팀 필터 (있는 경우만)
if team_col is not None:
    teams = ["(전체)"] + sorted(df[team_col].dropna().unique().tolist())
    sel_team = filters.selectbox("팀", teams)
    if sel_team != "(전체)":
        df = df[df[team_col] == sel_team]


with (st.container()):
    if champ_col is None:
        st.warning("챔피언 컬럼을 찾지 못했습니다. 원본 데이터 미리보기를 표시합니다.")
        st.dataframe(df.head(50), width='stretch')
        st.stop()

    st.subheader("챔피언별 픽 통계")

    # 중복 게임 기준 제거 옵션
    unique_per_game = st.checkbox("게임당 1행으로 중복 제거 (게임 식별 컬럼 필요)", value=False)
    work_df = df[df.position == 'team'].copy()
    if unique_per_game and gameid_col is not None:
        work_df = work_df.drop_duplicates(subset=[gameid_col, champ_col])

    # 기본 집계: 픽 수
    pick_counts = work_df[pick_col].stack().value_counts().rename_axis("챔피언").reset_index(name="픽 수")
    ban_counts = work_df[ban_col].stack().value_counts().rename_axis("챔피언").reset_index(name="밴 수")

    # 승률/승패 계산 (가능할 때만)
    if win_col is not None:
        # win_numeric = map_win_to_numeric(work_df[win_col])
        team_picks = work_df[pick_col+['result']]
        melt_team_picks = team_picks.melt(
            id_vars=['result'],
            var_name='도시',
            value_name='챔피언'
        )
        agg = melt_team_picks.groupby('챔피언').apply(
            lambda g: pd.Series({
                "픽 수": len(g),
                "승리": int(g.result.sum()),
                "패배": int(len(g) - g.result.sum()),
            }), include_groups=False
        ).reset_index()#.rename(columns={'온도': "챔피언"})

        agg["승률"] = (agg["승리"] / agg["픽 수"]).round(3)
        agg = pd.merge(agg, ban_counts, on='챔피언', how='outer').fillna(0)
        result_df = agg.sort_values(["픽 수", "승률"], ascending=[False, False])

    else:
        result_df = pick_counts.sort_values("픽 수", ascending=False)

    st.dataframe(
        result_df, width='stretch',
        selection_mode="single-cell", on_select="rerun", hide_index=True, key="df_selection"
    )
    selection = st.session_state.df_selection['selection']['cells']

    if selection:
        selected_sell_index = selection[0]
        temp_result_df = result_df.reset_index(drop=True)
        selected_champion = temp_result_df.loc[selected_sell_index[0], '챔피언']
        if isinstance(selected_champion, str):
            vote(selected_champion)
            # selected_df = df[df.champion == selected_champion]
            # groupby_champion = selected_df.groupby('playername').result.mean().to_frame().sort_values('result', ascending=False).style.format("{:.2%}")
            # st.dataframe(groupby_champion, width='stretch')
    # else:
    #     st.write("챔피언 이름 선택시 선수별 승률을 볼 수 있습니다.")


