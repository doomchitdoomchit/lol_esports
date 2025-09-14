import streamlit as st
import pandas as pd
from pathlib import Path
from pages.esports import load_csv, find_column, map_win_to_numeric, pca_data
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


st.title("선수 지표 비교")
st.set_page_config(layout="wide")
col_cat_name = {'1': '성장', '2': '공격', '3': '격차', '4': '수비/죽음', '5': '시야', '6': '협동'}


csv_file = Path("lck.csv")
cluster_file = Path("cluster.csv")

with st.spinner("데이터 로딩 중..."):
    try:
        df = load_csv(csv_file)
        cluster_df = load_csv(cluster_file)
        pca_12_df, pca_35_df = pca_data(df, cluster_df, col_cat_name)
    except Exception as e:
        st.error(f"CSV 로드 오류: {e}")
        st.stop()

st.sidebar.subheader("필터 설정")
# 세부 내용 설명
side_col1, side_col2 = st.sidebar.columns([1, 1])
with side_col1:
    button_explain = st.button("사용방법")
with side_col2:
    button_value = st.button("지표설명")


@st.dialog("사용 방법", width='large')
def tutorial():
    dia_col1, dia_col2, dia_col3 = st.columns([1, 1, 1])
    with dia_col1:
        st.subheader(f"1. 포지션 전체 비교")
        st.write("- 좌측 사이드바의 포지션을 선택해주세요.")
        st.write('- 크게 보실려면 그래프의 우측 상단에 Fullscreen을 클릭 해주세요.')
        st.write("** 선수 선택을 하시면 선수 지표로 넘어가니 해당 부분을 '선택하세요'로 바꿔주세요**")
        st.write("** Round 1-2와 3-5가 분리되어 있습니다.**")
    with dia_col2:
        st.subheader(f"2. 단일 선수 지표 확인")
        st.write("- 선수A 또는 선수B를 선택해주세요. 좌측 사이드바에서 포시션을 선택하면 찾는 선수를 쉽게 찾을 수 있습니다.")
        st.write('- 크게 보실려면 그래프의 우측 상단에 Fullscreen을 클릭 해주세요.')
        st.write("**선수A와 선수B를 동시에 선택을 하시면 선수 비교로 넘어가니 둘 중 한 부분을 '선택하세요'로 바꿔주세요**")
    with dia_col3:
        st.subheader(f"3. 선수 지표 비교")
        st.write("- 선수A 와 선수B를 선택해주세요. 좌측 사이드바에서 포시션을 선택하면 찾는 선수를 쉽게 찾을 수 있습니다.")
        st.write('- 한 화면에 보실려면 Fullscreen을 클릭 해주세요.')
        st.write('- 위에는 각 선수의 라운드별 지표를, 아래에는 각 라운드의 선수비교 지표입니다..')
        st.write("**선수A와 선수B를 같은 포지션으로 선택해주세요.**")


@st.dialog("지표 설명", width='large')
def variable_explain():
    st.subheader('지표 나눈 기준')
    st.write("데이터의 각 변수들의 분산의 거리에 따라 지표를 clustering.")
    st.write("cluster 간의 거리가 갑자기 증가한 부분을 기점으로 잡았으며,")
    st.write("그 중 팀 지표로 크게 유효하지 않는 그룹을 제외하고 총 6개의 cluster가 아래와 같음.")
    st.subheader('성장')
    st.write("DPM, damage share, gold 관련 지표, cs 관련 지표, xp 관련 지표")
    st.subheader('공격')
    st.write("kill 관련 지표, 퍼블, 타워/억제기")
    st.subheader('격차')
    st.write("시간 때 별 골드/xp/cs 격차")
    st.subheader('수비/죽음')
    st.write("death 관련 지표, 피퍼블, 피assist")
    st.subheader('시야')
    st.write("와드 설치, 와드 제거, 제어 와드 구매")
    st.subheader('협동')
    st.write("assist, 피death 관련 지표")
    st.subheader('atTIME')
    st.write("시간에 따른 라인전 지표 위의 6개의 cluster 원소와 겹침")


if button_explain:
    tutorial()

if button_value:
    variable_explain()

# 포지션 필터
positions = ["(전체)"] + sorted(df['position'].dropna().unique().tolist())
positions = [_ for _ in positions if 'team' != _]
sel_position = st.sidebar.selectbox("포지션 선택", positions)

if sel_position != "(전체)":
    df_filtered = df[df['position'] == sel_position].copy()
    # 포지션별 18경기 이상 선수 재계산
    game_count_per_player = df_filtered.groupby('playername').gameid.count()
    players_18plus_pos = game_count_per_player[game_count_per_player >= 18].index.tolist()
else:
    df_filtered = df.copy()
    game_count_per_player = df_filtered.groupby('playername').gameid.count()
    players_18plus_pos = game_count_per_player[game_count_per_player >= 18].index.tolist()

# 개별 선수 선택
st.subheader("선수 비교")

col1, col2 = st.columns(2)

with col1:
    st.write("**선수 A 선택**")
    player_a = st.selectbox("선수 A", ["선택하세요"] + sorted(game_count_per_player.index.tolist()), key="player_a")

with col2:
    st.write("**선수 B 선택**")
    player_b = st.selectbox("선수 B", ["선택하세요"] + sorted(game_count_per_player.index.tolist()), key="player_b")


# 선수 데이터 처리
def get_player_data(player_name):
    if player_name == "선택하세요":
        return None
    
    player_data = df_filtered[df_filtered['playername'] == player_name].copy()
    
    # 18경기 체크
    game_count = player_data['gameid'].nunique()

    if game_count < 18:
        return "insufficient_games"
    
    return player_data


if sel_position != '(전체)' and player_a == "선택하세요" and player_b == "선택하세요":
    pos_data = pca_12_df[sel_position][pca_12_df[sel_position].playername.apply(lambda x: x in players_18plus_pos)]
    df_melted = pos_data.melt(id_vars=['playername'], var_name='category', value_name='score')
    fig = px.line_polar(
        df_melted,
        r='score',  # 차트의 반지름 (값)
        theta='category',  # 차트의 각 축 이름
        color='playername',  # 그래프를 선수별로 구분
        color_discrete_sequence=px.colors.qualitative.Dark24,
        line_close=True,  # 마지막 점과 첫 점을 연결하여 다각형 생성
        title=f'{sel_position} 선수 Round1-2 능력치 비교'
    )
    fig.update_layout(
        height=1200, width=1600,)
    st.plotly_chart(fig, width='stretch')

    pos_data = pca_35_df[sel_position][pca_35_df[sel_position].playername.apply(lambda x: x in players_18plus_pos)]
    df_melted = pos_data.melt(id_vars=['playername'], var_name='category', value_name='score')
    fig = px.line_polar(
        df_melted,
        r='score',  # 차트의 반지름 (값)
        theta='category',  # 차트의 각 축 이름
        color='playername',  # 그래프를 선수별로 구분
        color_discrete_sequence=px.colors.qualitative.Dark24,
        line_close=True,  # 마지막 점과 첫 점을 연결하여 다각형 생성
        title=f'{sel_position} 선수 Round3-5 능력치 비교'
    )
    fig.update_layout(
        height=1200, width=1600,)
    st.plotly_chart(fig, width='stretch')


if (player_a == "선택하세요") ^ (player_b == "선택하세요"):
    player_pos = df_filtered[df_filtered.playername.apply(lambda x: x in [player_a, player_b])].position.max()
    player_12_df = pca_12_df[player_pos][(pca_12_df[player_pos]['playername'].apply(lambda x: x in [player_a, player_b]))]
    player_35_df = pca_35_df[player_pos][(pca_35_df[player_pos]['playername'].apply(lambda x: x in [player_a, player_b]))]
    player_df = pd.concat([player_12_df, player_35_df])
    if player_12_df.empty:
        player_df['playername'] = ['Round3-5']
    elif player_35_df.empty:
        player_df['playername'] = ['Round1-2']
    else:
        player_df['playername'] = ['Round1-2', 'Round3-5']
    player_df = player_df.rename({'playername': 'Round'}, axis=1)
    df_melted = player_df.melt(id_vars=['Round'], var_name='category', value_name='score')
    fig = px.line_polar(
            df_melted,
            r='score',  # 차트의 반지름 (값)
            theta='category',  # 차트의 각 축 이름
            color='Round',  # 그래프를 선수별로 구분
            color_discrete_sequence=px.colors.qualitative.Dark24,
            line_close=True,  # 마지막 점과 첫 점을 연결하여 다각형 생성
            title=f'Round별 능력치 비교'
        )
    st.plotly_chart(fig, width='stretch')


if (player_a != "선택하세요") & (player_b != "선택하세요"):
    player_pos = df_filtered[df_filtered.playername.apply(lambda x: x in [player_a, player_b])].position
    if player_pos.nunique() > 1:
        st.warning('같은 포지션의 선수를 선택해주세요.')
        st.stop()
    player_pos = player_pos.max()
    player_a_data = get_player_data(player_a)
    player_b_data = get_player_data(player_b)

    # 에러 처리
    if isinstance(player_a_data, str):
        st.warning(f"선수 A ({player_a})가 18경기를 넘지 못해서 제공하지 않습니다.")
        st.stop()

    if isinstance(player_b_data, str):
        st.warning(f"선수 B ({player_b})가 18경기를 넘지 못해서 제공하지 않습니다.")
        st.stop()

    pos_playername = [player_a, player_b, 'Rounds 1-2', 'Rounds 3-5']
    fig = make_subplots(rows=2, cols=2, specs=[[{'type': 'polar'}]*2]*2, subplot_titles=pos_playername)

    player_12_df = pca_12_df[player_pos][(pca_12_df[player_pos]['playername'].apply(lambda x: x in [player_a, player_b]))]
    player_35_df = pca_35_df[player_pos][(pca_35_df[player_pos]['playername'].apply(lambda x: x in [player_a, player_b]))]
    for _split, _spname in zip([player_12_df, player_35_df], ['R1-2', 'R3-5']):
        df_long = pd.melt(_split, id_vars=['playername'], var_name='category', value_name='score')
        df_long = df_long.sort_values(by=['playername', 'category'], ascending=False)
        temp_fig = px.line_polar(
            df_long,
            r='score',
            # r0 = [-10, -5, 0, 5, 10],
            theta='category',
            color='playername',
            color_discrete_sequence=px.colors.qualitative.Dark24,
            # color_discrete_map =color_dict,
            line_close=True,
            markers=True,
            # title='선수별 능력치 비교'
            # range_r =[0, 5]
        )

        for trace in temp_fig.data:
            name = trace.name
            trace.legendgroup = _spname
            if _spname == 'R1-2':
                fig.add_trace(trace, row=2, col=1)
                trace.line['color'] = '#32CD32'
            else:
                fig.add_trace(trace, row=2, col=2)
                trace.line['color'] = '#ab63fa'

            trace.showlegend = False
            # trace.title = name
            # fig_row, fig_col = pos_dict[name]
            fig.add_trace(trace, row=1, col=pos_playername.index(name) + 1)
    fig.update_layout(
        height=1200, width=1600, title_text='초록(Round1-2), 보라(Round3-5)',
        legend=dict(x=1, y=0)
    )
    st.plotly_chart(fig, width='stretch')