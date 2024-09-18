import pandas as pd

def load_clean_data():
    df_matches = pd.read_csv("atp_100_matches.csv")

    missing_heights = {"Rinky Hijikata": 178,
                        "Alexander Shevchenko": 185,
                        "Ben Shelton": 193,
                        
                        "Alex Michelsen": 193,
                        "Juncheng Shang": 183,
                        "Adam Walton": 188,
                        "Aleksandar Kovacevic": 183,
                        "Jakub Mensik": 191,
                        "Flavio Cobolli": 183,
                        "Mariano Navone": 170,
                        "Francisco Comesana": 180,
                        "Camilo Ugo Carabelli": 185,
                        "Luciano Darderi": 178,
                        "Giovanni Mpetshi Perricard": 203}

    for row in df_matches[pd.isna(df_matches['loser_ht'])].iterrows():
        if row[1]["winner_name"] in missing_heights.keys():
            df_matches.loc[row[0], "winner_ht"] = missing_heights.get(row[1]["winner_name"])
        if row[1]["loser_name"] in missing_heights.keys():
            df_matches.loc[row[0], "loser_ht"] = missing_heights.get(row[1]["loser_name"])

    feature_cols = ["surface", "winner_id", "winner_hand", "winner_ht", "winner_ioc", "loser_id", 
    "loser_hand", "loser_ht", "loser_ioc", "best_of", "w_ace", "w_df",
    "w_svpt", "w_1stIn", "w_1stWon", "w_2ndWon", "w_SvGms", "w_bpSaved",
    "w_bpFaced", "l_ace", "l_df", "l_svpt", "l_1stIn", "l_1stWon",
    "l_2ndWon", "l_SvGms", "l_bpSaved", "l_bpFaced", "score", "minutes"]

    df_matches = df_matches[feature_cols]

    ranks = pd.read_csv("atp_100_withIDs.csv")
    
    df_matches = df_matches.merge(ranks[['rank','id']], left_on="winner_id", right_on="id").drop(columns="id", axis=1)
    df_matches.rename(columns={"rank":"winner_rank"}, inplace=True)
    df_matches = df_matches.merge(ranks[['rank','id']], left_on="loser_id", right_on="id").drop(columns="id", axis=1)
    df_matches.rename(columns={"rank":"loser_rank"}, inplace=True)

    df_matches = df_matches.reset_index()
    df_matches.rename(columns={"index":"match_id"}, inplace=True)

    df_players_matches = pd.DataFrame()

    for row in df_matches.iterrows():
        match = row[1]
        winner_data = {'player_id': match['winner_id'], 'hand': match['winner_hand'], 'ht': match['winner_ht'],
        'ioc': match['winner_ioc'], 'rank': match['winner_rank'], 'ace': match['w_ace'], 'df': match['w_df'], 'svpt': match['w_svpt'], 
        '1stIn': match['w_1stIn'], '1stWon': match['w_1stWon'], '2ndWon': match['w_2ndWon'],
        'SvGms': match['w_SvGms'], 'bpSaved': match['w_bpSaved'], 'bpFaced': match['w_bpFaced'], 
        'surface': match['surface'], 'score': match['score'], 'minutes': match['minutes'], 
        'match_id': match['match_id'], 'winner': 1}
        loser_data = {'player_id': match['loser_id'], 'hand': match['loser_hand'], 'ht': match['loser_ht'],
        'ioc': match['loser_ioc'], 'rank': match['loser_rank'], 'ace': match['l_ace'], 'df': match['l_df'], 'svpt': match['l_svpt'], 
        '1stIn': match['l_1stIn'], '1stWon': match['l_1stWon'], '2ndWon': match['l_2ndWon'],
        'SvGms': match['l_SvGms'], 'bpSaved': match['l_bpSaved'], 'bpFaced': match['l_bpFaced'], 
        'surface': match['surface'], 'score': match['score'], 'minutes': match['minutes'], 
        'match_id': match['match_id'], 'winner': 0}
        
        df_players_matches = pd.concat([df_players_matches, pd.DataFrame([winner_data]), pd.DataFrame([loser_data])])

    
    df_players = pd.DataFrame()
    player_lst = df_players_matches.player_id.unique()

    metric_cols = ['ace', 'df', 'svpt', '1stIn', '1stWon', '2ndWon', 'SvGms', 'bpSaved', 'bpFaced', 'minutes']

    for player in player_lst:
        metrics_temp = pd.DataFrame(df_players_matches[df_players_matches['player_id']==player].groupby(
            ['player_id','surface'])[metric_cols].mean()).reset_index()
        counts_temp = pd.DataFrame(df_players_matches[df_players_matches['player_id']==player].groupby(
            ['player_id','surface', 'winner']).size()).reset_index()
        counts_temp = counts_temp.pivot(index=['player_id','surface'], columns='winner', values=0).reset_index()

        final_temp = counts_temp.merge(metrics_temp, on=['player_id', 'surface'])
        df_players = pd.concat([df_players, final_temp])


    df_players.rename(columns={0: 'losses', 1: 'wins'}, inplace=True)
    df_players.head(10)

    df_players = df_players.merge(df_players_matches[['player_id', 'hand', 'ht', 'ioc', 'rank']].drop_duplicates().dropna(), on='player_id')
    df_players.fillna(value={'wins': 0, 'losses': 0}, inplace=True)

    df_players['num_matches'] = df_players['wins'] + df_players['losses']
    df_players['win_pct'] = df_players['wins'] / df_players['num_matches']

    rename_cols = ['losses', 'wins', 'ace', 'df', 'svpt', '1stIn', '1stWon', '2ndWon', 'SvGms', 'bpSaved',
        'bpFaced', 'minutes', 'hand', 'ht', 'ioc', 'rank', 'win_pct', 'num_matches']
    df_matches_sm = df_matches[['match_id', 'surface', 'winner_id', 'loser_id']]
    df_matches_sm = df_matches_sm.merge(df_players, left_on=['surface', 'winner_id'], right_on=['surface', 'player_id']).drop(columns='player_id', axis=1)

    for col in rename_cols:
        df_matches_sm.rename(columns={col: "w_{}".format(col)}, inplace=True)

    df_matches_sm = df_matches_sm.merge(df_players, left_on=['surface', 'loser_id'], right_on=['surface', 'player_id']).drop(columns='player_id', axis=1)

    for col in rename_cols:
        df_matches_sm.rename(columns={col: "l_{}".format(col)}, inplace=True)

    df_matches_sm['lower_won'] = df_matches_sm['w_rank'] > df_matches_sm['l_rank']
    df_matches_sm['lower_won'] = df_matches_sm['lower_won'].astype(int)
    #df_matches_sm.drop(columns=['winner_id','loser_id', 'match_id'], axis=1, inplace=True)

    df_matches_sm['w_hand'] = df_matches_sm['w_hand'].apply(lambda x: 1 if x == 'R' else 0)
    df_matches_sm['l_hand'] = df_matches_sm['l_hand'].apply(lambda x: 1 if x == 'R' else 0)

    return df_matches_sm