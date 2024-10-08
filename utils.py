import pandas as pd
import itertools

def add_missing_heights(df_matches):
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
    
    return df_matches

def merge_rank_info(df_matches, ranks):

    df_matches = df_matches.merge(ranks[['rank','id']], left_on="winner_id", right_on="id").drop(columns="id", axis=1)
    df_matches.rename(columns={"rank":"winner_rank"}, inplace=True)

    df_matches = df_matches.merge(ranks[['rank','id']], left_on="loser_id", right_on="id").drop(columns="id", axis=1)
    df_matches.rename(columns={"rank":"loser_rank"}, inplace=True)

    df_matches = df_matches.reset_index()
    df_matches.rename(columns={"index":"match_id"}, inplace=True)

    return df_matches

def create_player_match_df(df_matches):

    df_players_matches = pd.DataFrame()

    for row in df_matches.iterrows():
        match = row[1]
        winner_data = {'date': match['tourney_date'], 'player_id': match['winner_id'], 'hand': match['winner_hand'], 'ht': match['winner_ht'],
        'ioc': match['winner_ioc'], 'rank': match['winner_rank'], 'ace': match['w_ace'], 'df': match['w_df'], 'svpt': match['w_svpt'], 
        '1stIn': match['w_1stIn'], '1stWon': match['w_1stWon'], '2ndWon': match['w_2ndWon'],
        'SvGms': match['w_SvGms'], 'bpSaved': match['w_bpSaved'], 'bpFaced': match['w_bpFaced'], 
        'surface': match['surface'], 'score': match['score'], 'minutes': match['minutes'], 
        'match_id': match['match_id'], 'winner': 1, 'opponent': match['loser_id']}
        loser_data = {'date': match['tourney_date'], 'player_id': match['loser_id'], 'hand': match['loser_hand'], 'ht': match['loser_ht'],
        'ioc': match['loser_ioc'], 'rank': match['loser_rank'], 'ace': match['l_ace'], 'df': match['l_df'], 'svpt': match['l_svpt'], 
        '1stIn': match['l_1stIn'], '1stWon': match['l_1stWon'], '2ndWon': match['l_2ndWon'],
        'SvGms': match['l_SvGms'], 'bpSaved': match['l_bpSaved'], 'bpFaced': match['l_bpFaced'], 
        'surface': match['surface'], 'score': match['score'], 'minutes': match['minutes'], 
        'match_id': match['match_id'], 'winner': 0, 'opponent': match['winner_id']}
        
        df_players_matches = pd.concat([df_players_matches, pd.DataFrame([winner_data]), pd.DataFrame([loser_data])])
    
    return df_players_matches

def create_player_metrics_df(df_players_matches, player_lst, filter):
    df_players = pd.DataFrame()
    
    metric_cols = ['ace', 'df', 'svpt', '1stIn', '1stWon', '2ndWon', 'SvGms', 'bpSaved', 'bpFaced', 'minutes']


    for player in player_lst:
        player_df = df_players_matches[df_players_matches['player_id']==player]
        for dt in player_df['date'].sort_values().unique():
            player_prev = player_df[player_df['date'] < dt]
            metrics_temp = pd.DataFrame(player_prev.groupby(
                ['player_id', filter])[metric_cols].mean()).reset_index()
            counts_temp = pd.DataFrame(player_prev.groupby(
                ['player_id',filter, 'winner']).size()).reset_index()
            counts_temp = counts_temp.pivot(index=['player_id', filter], columns='winner', values=0).reset_index()
            final_temp = counts_temp.merge(metrics_temp, on=['player_id', filter])
            final_temp['date'] = dt
            df_players = pd.concat([df_players, final_temp])

    df_players.rename(columns={0: 'losses', 1: 'wins'}, inplace=True)

    df_players.drop_duplicates(inplace=True)

    df_players.fillna(value={'wins': 0, 'losses': 0}, inplace=True)
    df_players = df_players.merge(df_players_matches[['player_id', 'hand', 'ht', 'ioc', 'rank']].drop_duplicates().dropna(), on='player_id')

    df_players['num_matches'] = df_players['wins'] + df_players['losses']
    df_players['win_pct'] = df_players['wins'] / df_players['num_matches']

    return df_players

def load_clean_data(all_past=False):
    """
    Load tennis data """
    
    df_matches = pd.read_csv("atp_100_matches2.csv")

    df_matches = add_missing_heights(df_matches)

    feature_cols = ["tourney_date", "surface", "winner_id", "winner_hand", "winner_ht", "winner_ioc", "loser_id", 
    "loser_hand", "loser_ht", "loser_ioc", "best_of", "w_ace", "w_df",
    "w_svpt", "w_1stIn", "w_1stWon", "w_2ndWon", "w_SvGms", "w_bpSaved",
    "w_bpFaced", "l_ace", "l_df", "l_svpt", "l_1stIn", "l_1stWon",
    "l_2ndWon", "l_SvGms", "l_bpSaved", "l_bpFaced", "score", "minutes"]

    df_matches = df_matches[feature_cols]
    df_matches['tourney_date'] = df_matches['tourney_date'].apply(lambda x: pd.to_datetime(str(int(x)), format='%Y%m%d'))

    ranks = pd.read_csv("atp_100_withIDs.csv")

    df_matches = merge_rank_info(df_matches, ranks)

    # Using the dataframe of match statistics, create a dataframe of players, where each row is a row per
    # player per match, with their associated match stats. To be used to caculate overall stats for the player
    
    df_players_matches = create_player_match_df(df_matches)

    player_lst = ranks['id'].values

    df_players = create_player_metrics_df(df_players_matches, player_lst, "surface")

    df_player_opps = create_player_metrics_df(df_players_matches, player_lst, "opponent")

    df_players = df_players.merge(df_player_opps, left_on=['player_id','date'], right_on=['player_id','date'], suffixes=("", "_opp"))

    rename_cols = ['losses', 'wins', 'ace', 'df', 'svpt', '1stIn', '1stWon', '2ndWon', 'SvGms', 'bpSaved',
    'bpFaced', 'minutes', 'hand', 'ht', 'ioc', 'rank', 'win_pct', 'num_matches', 'losses_opp', 'wins_opp',
       'ace_opp', 'df_opp', 'svpt_opp', '1stIn_opp', '1stWon_opp',
       '2ndWon_opp', 'SvGms_opp', 'bpSaved_opp', 'bpFaced_opp', 'minutes_opp',
       'num_matches_opp', 'win_pct_opp']

    df_matches_sm = df_matches[(df_matches['loser_id'].isin(player_lst)) & (df_matches['winner_id'].isin(player_lst))]
    df_matches_sm = df_matches[['match_id', 'tourney_date', 'surface', 'winner_id', 'loser_id']]
    df_matches_sm = df_matches_sm.merge(df_players, left_on=['surface', 'tourney_date', 'winner_id', 'loser_id'], 
                                        right_on=['surface', 'date', 'player_id', 'opponent']).drop(columns='player_id', axis=1)

    for col in rename_cols:
        df_matches_sm.rename(columns={col: "w_{}".format(col)}, inplace=True)

    df_matches_sm = df_matches_sm.merge(df_players, left_on=['surface', 'tourney_date', 'loser_id', 'winner_id'], 
                                        right_on=['surface', 'date', 'player_id', 'opponent']).drop(columns='player_id', axis=1)

    for col in rename_cols:
        df_matches_sm.rename(columns={col: "l_{}".format(col)}, inplace=True)

    #df_matches_sm['lower_won'] = df_matches_sm['w_rank'] > df_matches_sm['l_rank']
    #df_matches_sm['lower_won'] = df_matches_sm['lower_won'].astype(int)

    df_matches_sm['w_hand'] = df_matches_sm['w_hand'].apply(lambda x: 1 if x == 'R' else 0)
    df_matches_sm['l_hand'] = df_matches_sm['l_hand'].apply(lambda x: 1 if x == 'R' else 0)

    return df_matches_sm


def create_future_dataset():
    df_matches = pd.read_csv("atp_100_matches2.csv")

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

    feature_cols = ["tourney_date", "surface", "winner_id", "winner_hand", "winner_ht", "winner_ioc", "loser_id", 
    "loser_hand", "loser_ht", "loser_ioc", "best_of", "w_ace", "w_df",
    "w_svpt", "w_1stIn", "w_1stWon", "w_2ndWon", "w_SvGms", "w_bpSaved",
    "w_bpFaced", "l_ace", "l_df", "l_svpt", "l_1stIn", "l_1stWon",
    "l_2ndWon", "l_SvGms", "l_bpSaved", "l_bpFaced", "score", "minutes"]

    df_matches = df_matches[feature_cols]
    df_matches['tourney_date'] = df_matches['tourney_date'].apply(lambda x: pd.to_datetime(str(int(x)), format='%Y%m%d'))

    ranks = pd.read_csv("atp_100_withIDs.csv")

    df_matches = df_matches.merge(ranks[['rank','id']], left_on="winner_id", right_on="id").drop(columns="id", axis=1)
    df_matches.rename(columns={"rank":"winner_rank"}, inplace=True)
    df_matches = df_matches.merge(ranks[['rank','id']], left_on="loser_id", right_on="id").drop(columns="id", axis=1)
    df_matches.rename(columns={"rank":"loser_rank"}, inplace=True)

    df_matches = df_matches.reset_index()
    df_matches.rename(columns={"index":"match_id"}, inplace=True)

    # Using the dataframe of match statistics, create a dataframe of players, where each row is a row per
    # player per match, with their associated match stats. To be used to caculate overall stats for the player

    df_players_matches = pd.DataFrame()

    for row in df_matches.iterrows():
        match = row[1]
        winner_data = {'date': match['tourney_date'], 'player_id': match['winner_id'], 'hand': match['winner_hand'], 'ht': match['winner_ht'],
        'ioc': match['winner_ioc'], 'rank': match['winner_rank'], 'ace': match['w_ace'], 'df': match['w_df'], 'svpt': match['w_svpt'], 
        '1stIn': match['w_1stIn'], '1stWon': match['w_1stWon'], '2ndWon': match['w_2ndWon'],
        'SvGms': match['w_SvGms'], 'bpSaved': match['w_bpSaved'], 'bpFaced': match['w_bpFaced'], 
        'surface': match['surface'], 'score': match['score'], 'minutes': match['minutes'], 
        'match_id': match['match_id'], 'winner': 1, 'opponent': match['loser_id']}
        loser_data = {'date': match['tourney_date'], 'player_id': match['loser_id'], 'hand': match['loser_hand'], 'ht': match['loser_ht'],
        'ioc': match['loser_ioc'], 'rank': match['loser_rank'], 'ace': match['l_ace'], 'df': match['l_df'], 'svpt': match['l_svpt'], 
        '1stIn': match['l_1stIn'], '1stWon': match['l_1stWon'], '2ndWon': match['l_2ndWon'],
        'SvGms': match['l_SvGms'], 'bpSaved': match['l_bpSaved'], 'bpFaced': match['l_bpFaced'], 
        'surface': match['surface'], 'score': match['score'], 'minutes': match['minutes'], 
        'match_id': match['match_id'], 'winner': 0, 'opponent': match['winner_id']}
        
        df_players_matches = pd.concat([df_players_matches, pd.DataFrame([winner_data]), pd.DataFrame([loser_data])])

    df_players = pd.DataFrame()

    player_lst = df_players_matches.player_id.unique()

    metric_cols = ['ace', 'df', 'svpt', '1stIn', '1stWon', '2ndWon', 'SvGms', 'bpSaved', 'bpFaced', 'minutes']

    for player in player_lst:
        player_df = df_players_matches[df_players_matches['player_id']==player]
        for sur in ["Grass", "Hard", "Clay"]:
            player_sur = player_df[player_df['surface'] == sur]
            if player_sur.empty:
                player_sur = player_df
            metrics_temp = pd.DataFrame(player_sur.groupby(
                ['player_id'])[metric_cols].mean()).reset_index()
            counts_temp = pd.DataFrame(player_sur.groupby(
                ['player_id', 'winner']).size()).reset_index()
            counts_temp = counts_temp.pivot(index=['player_id'], columns='winner', values=0).reset_index()
            final_temp = counts_temp.merge(metrics_temp, on=['player_id'])
            final_temp['surface'] = sur
            df_players = pd.concat([df_players, final_temp])

    df_players.rename(columns={0: 'losses', 1: 'wins'}, inplace=True)

    df_players.drop_duplicates(inplace=True)

    df_players.fillna(value={'wins': 0, 'losses': 0}, inplace=True)
    df_players = df_players.merge(df_players_matches[['player_id', 'hand', 'ht', 'ioc', 'rank']].drop_duplicates().dropna(), on='player_id')

    df_players['num_matches'] = df_players['wins'] + df_players['losses']
    df_players['win_pct'] = df_players['wins'] / df_players['num_matches']

    df_player_opps = pd.DataFrame()
    for player in player_lst:
        player_df = df_players_matches[df_players_matches['player_id']==player]
        for opp in [x for x in player_lst if x != player]:
            player_opp = player_df[player_df['opponent'] == opp]

            if player_opp.empty:
                player_opp = player_df

            metrics_temp = pd.DataFrame(player_opp.groupby(
                ['player_id'])[metric_cols].mean()).reset_index()
            counts_temp = pd.DataFrame(player_opp.groupby(
                ['player_id','winner']).size()).reset_index()
            counts_temp = counts_temp.pivot(index=['player_id'], columns='winner', values=0).reset_index()
            
            final_temp = counts_temp.merge(metrics_temp, on=['player_id'])
            final_temp['opponent'] = opp
            df_player_opps = pd.concat([df_player_opps, final_temp])

    df_player_opps.rename(columns={0: 'losses', 1: 'wins'}, inplace=True)
    df_player_opps.head(10)

    #df_player_opps = df_player_opps.merge(df_players_matches[['player_id', 'hand', 'ht', 'ioc', 'rank']].drop_duplicates().dropna(), on='player_id')
    df_player_opps.fillna(value={'wins': 0, 'losses': 0}, inplace=True)

    df_player_opps['num_matches'] = df_player_opps['wins'] + df_player_opps['losses']
    df_player_opps['win_pct'] = df_player_opps['wins'] / df_player_opps['num_matches']
    df_player_opps.head()

    df_players = df_players.merge(df_player_opps, left_on=['player_id'], right_on=['player_id'], suffixes=("", "_opp"))

    rename_cols = ['losses', 'wins', 'ace', 'df', 'svpt', '1stIn', '1stWon', '2ndWon', 'SvGms', 'bpSaved',
    'bpFaced', 'minutes', 'hand', 'ht', 'ioc', 'rank', 'win_pct', 'num_matches', 'losses_opp', 'wins_opp',
        'ace_opp', 'df_opp', 'svpt_opp', '1stIn_opp', '1stWon_opp',
        '2ndWon_opp', 'SvGms_opp', 'bpSaved_opp', 'bpFaced_opp', 'minutes_opp',
        'num_matches_opp', 'win_pct_opp']
    
    player_ids = ranks['id'].values
    player_pairs = list(itertools.combinations(player_ids, 2))
    surfaces = ['Hard','Grass','Clay']

    future_matches_df = pd.DataFrame(player_pairs).merge(pd.DataFrame(surfaces), how='cross')
    future_matches_df.rename(columns={"0_x": "player1_id", 1: "player2_id", "0_y": "surface"}, inplace = True)
    future_matches_df

    future_matches_df = future_matches_df.merge(df_players, left_on=['surface', 'player1_id', 'player2_id'], 
                                    right_on=['surface', 'player_id', 'opponent']).drop(columns='player_id', axis=1)
    print(len(future_matches_df))

    for col in rename_cols:
        future_matches_df.rename(columns={col: "player1_{}".format(col)}, inplace=True)

    future_matches_df = future_matches_df.merge(df_players, left_on=['surface', 'player2_id', 'player1_id'], 
                                        right_on=['surface', 'player_id', 'opponent']).drop(columns='player_id', axis=1)
    print(len(future_matches_df))
    for col in rename_cols:
        future_matches_df.rename(columns={col: "player2_{}".format(col)}, inplace=True)

    future_matches_df['player1_hand'] = future_matches_df['player1_hand'].apply(lambda x: 1 if x == 'R' else 0)
    future_matches_df['player2_hand'] = future_matches_df['player2_hand'].apply(lambda x: 1 if x == 'R' else 0)
    len(future_matches_df)

    return future_matches_df


