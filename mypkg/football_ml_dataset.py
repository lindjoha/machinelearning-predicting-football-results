# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 20:30:05 2019

@author: olind
"""
import pandas as pd
import math

class MatchStatsDataset:
    matches = []
    
    def __init__(self, df, remove_first_n):
        self.matchstats = df
        self.remove_first_n = remove_first_n
        self.matches = []
        for i, row in self.matchstats.iterrows():
            date = row['Date']
            hometeam = row['HomeTeam']
            awayteam = row['AwayTeam']      
            self.matches.append(Match(date, hometeam, awayteam))

        
    def get_features_and_matchdata(self, dct_features):
        df = pd.DataFrame(columns=dct_features.keys())
        
        ##Calc features
        for match in self.matches:
            df.loc[df.shape[0],:] = match.get_features(self, dct_features)
        
        ##Add additional match data
        #more_columns = ['FTR', 'PSCH', 'PSCD', 'PSCA']
        home_odds = 'B365H'
        draw_odds = 'B365D'
        away_odds = 'B365A'
        
        more_columns = ['FTR', home_odds, draw_odds, away_odds]
        
        for col in more_columns:
            df[col] = self.matchstats[col]

        df['p_home'] = 1/df[home_odds]
        df['p_draw'] = 1/df[draw_odds]
        df['p_away'] = 1/df[away_odds]
            
        ## remove n first columns before returning
        nb_rows = df.shape[0] - self.remove_first_n
        df = df.tail(nb_rows)
        df.index = range(nb_rows)
        return df


    def get_subset(self, team_name, home_or_away, before_date, n_games):
        filtered = self.matchstats[self.matchstats.Date < before_date]
        if home_or_away == 'H':
            filtered = filtered[filtered.HomeTeam == team_name] 
        elif home_or_away == 'A':
            filtered = filtered[filtered.AwayTeam == team_name]
        else:
            print('Parameter ''home_or_away'' must be ''H'' or ''A''')
        return filtered.tail(n_games)


class Match:

    def __init__(self, date, hometeam, awayteam):
        self.date = date
        self.hometeam = hometeam
        self.awayteam = awayteam
        
    def get_features(self, msd, features):
        output = []
        for feat_name in features:
            feature = features[feat_name]
            output.append(feature.get_value(msd, self))
        return output
    
    def get_home_or_away_team(self, home_or_away):
        if home_or_away == 'H':
            return self.hometeam
        elif home_or_away == 'A':
            return self.awayteam
        else:
            print('Parameter ''home_or_away'' must be ''H'' or ''A''') 


class Feature():
    
    def __init__(self, ha_team, feat_type, n_games, ha_games):
        self.ha_team = ha_team
        self.ha_games = ha_games
        self.feat_type = feat_type
        self.n_games = n_games
        
    def get_value(self, msd, match):
        team_name = match.get_home_or_away_team(self.ha_team)
        df = msd.get_subset(team_name, self.ha_games, match.date, self.n_games)
        if df.shape[0] == 0:
            return math.nan
        
        if self.feat_type == 'prcwin':
            result_count = df['FTR'].value_counts()
            if self.ha_games in result_count.index:
                return result_count.loc[self.ha_games]/df.shape[0]
            else:
                return 0
        
        if self.feat_type == 'goalsscored':
            column = 'FT'+self.ha_games+'G'
            return df[column].sum()
        
        if self.feat_type == 'goalsagainst':
            column='FTAG' if self.ha_games == 'H' else 'FTHG'
            return df[column].sum()
        
        if self.feat_type == 'goalsscoredewma':
            column = 'FT'+self.ha_games+'G'
            return df[column].ewm(com=0.5).mean().iloc[-1]
            
        else:
            return math.nan
            print('Feature type: ' + self.feat_type + ' is not implemented')
        

#%% Testcode
#path ='C:/Users/olind/ML/'
#df_PL0506 = pd.read_csv(path+'PL0506.csv')
#ds_PL0506 = MatchStatsDataset(df_PL0506, 300)
#dct_features = {'ht_prcwin_prev5_homegames':Feature('H', 'prcwin', 5, 'H'),
#            'ht_goalsscoredewma_prev20_homegames':Feature('H', 'goalsscoredewma', 20, 'H'),
#            }
#features = ds_PL0506.get_features_and_matchdata(dct_features)
#print(features[list(dct_features.keys())])
