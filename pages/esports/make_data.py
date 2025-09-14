import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


r3_split = {
    'Dplus KIA': 'rise',
    'OKSavingsBank BRION': 'rise',
    'DN Freecs': 'rise',
    'BNK FEARX': 'rise',
    'DRX': 'rise',
    'Gen.G': 'legend',
    'Hanwha Life Esports': 'legend',
    'KT Rolster': 'legend',
    'Nongshim RedForce': 'legend',
    'T1': 'legend',
}


def pca1_score(data, target_col, name):
    with pd.option_context("future.no_silent_downcasting", True):
        data = data.fillna(0).infer_objects(copy=False).reset_index(drop=True)

    x = data.loc[:, target_col].values
    x = StandardScaler().fit_transform(x)

    pca = PCA(n_components=1)
    principal_components = pca.fit_transform(x)

    pca_df = pd.DataFrame(data=principal_components, columns=['PC1'])
    pca_df['playername'] = data['playername']
    # print(data['playername'])
    # pca_df.plot(x='PC1', y='PC2', kind='scatter', figsize=(10, 10), title=name)
    # plt.show()
    pca_df_dsb = pca_df['PC1'].describe()
    score = (10 * (pca_df.groupby('playername').PC1.mean() - pca_df_dsb['mean']) / pca_df_dsb['std'])
    score.name = name
    return score


def pca_data(lck, cluster_results, cluster_names):
    lck_col_10 = [_ for _ in lck.columns if 'at10' in _ and 'opp' not in _]
    lck_col_15 = [_ for _ in lck.columns if 'at15' in _ and 'opp' not in _]
    lck_col_20 = [_ for _ in lck.columns if 'at20' in _ and 'opp' not in _]
    lck_col_25 = [_ for _ in lck.columns if 'at25' in _ and 'opp' not in _]
    lck_all_pos_data = dict()
    lck_12_pos_data = dict()
    lck_35_pos_data = dict()

    lck_35_leg_pos_data = dict()
    lck_35_ris_pos_data = dict()

    for _pos, _pos_data in lck.groupby('position'):
        if _pos == 'team':
            continue
        if _pos not in lck_all_pos_data:
            lck_all_pos_data[_pos] = []
        if _pos not in lck_12_pos_data:
            lck_12_pos_data[_pos] = []
        if _pos not in lck_35_pos_data:
            lck_12_pos_data[_pos] = []
        if _pos not in lck_35_leg_pos_data:
            lck_35_leg_pos_data[_pos] = []
        if _pos not in lck_35_ris_pos_data:
            lck_35_ris_pos_data[_pos] = []

        for _cat, _data in cluster_results.groupby('cluster'):
            if str(_cat) not in cluster_names:
                continue
            _col = _data['variable'].to_list()
            temp_result = pca1_score(_pos_data, _col, cluster_names[str(_cat)])
            lck_all_pos_data[_pos].append(temp_result)

        lck_all_pos_data[_pos] = pd.concat(lck_all_pos_data[_pos], axis=1).reset_index()

        for _sp, _sp_data in _pos_data.groupby('split'):
            _sp_data['r3_split'] = _sp_data.teamname.apply(lambda x: r3_split[x] if x in r3_split else 'none')
            for _cat, _data in cluster_results.groupby('cluster'):
                if str(_cat) not in cluster_names:
                    continue
                _col = _data['variable'].to_list()

                if _sp == 'Rounds 1-2':
                    temp_result = pca1_score(_sp_data, _col, cluster_names[str(_cat)])
                    lck_12_pos_data[_pos].append(temp_result)
                elif _sp == 'Rounds 3-5':
                    for _r3, _r3data in _sp_data.groupby('r3_split'):
                        if _r3 == 'legend':
                            lck_35_leg_pos_data[_pos].append(pca1_score(_r3data, _col, cluster_names[str(_cat)]))
                        else:
                            lck_35_ris_pos_data[_pos].append(pca1_score(_r3data, _col, cluster_names[str(_cat)]))

        for _sp, _sp_data in _pos_data.groupby('split'):
            _sp_data['r3_split'] = _sp_data.teamname.apply(lambda x: r3_split[x] if x in r3_split else 'none')
            for _cat, _data in zip(['at10', 'at15', 'at20', 'at25'], [lck_col_10, lck_col_15, lck_col_20, lck_col_25]):
                # if str(_cat) not in col_cat_name:
                #     continue
                # _col = list(_data['variable'].values)

                if _sp == 'Rounds 1-2':
                    temp_result = pca1_score(_sp_data, _data, _cat)
                    lck_12_pos_data[_pos].append(temp_result)
                elif _sp == 'Rounds 3-5':
                    for _r3, _r3data in _sp_data.groupby('r3_split'):
                        if _r3 == 'legend':
                            lck_35_leg_pos_data[_pos].append(pca1_score(_r3data, _data, _cat))
                        else:
                            lck_35_ris_pos_data[_pos].append(pca1_score(_r3data, _data, _cat))

        lck_12_pos_data[_pos] = pd.concat(lck_12_pos_data[_pos], axis=1).reset_index()
        lck_35_leg_pos_data[_pos] = pd.concat(lck_35_leg_pos_data[_pos], axis=1).reset_index()
        lck_35_ris_pos_data[_pos] = pd.concat(lck_35_ris_pos_data[_pos], axis=1).reset_index()
        lck_35_pos_data[_pos] = pd.concat([lck_35_ris_pos_data[_pos], lck_35_leg_pos_data[_pos]]).reset_index(drop=True)
    return lck_12_pos_data, lck_35_pos_data
