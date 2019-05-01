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


    def get_subset(self, team_name, home_away_both, before_date, n_games):
        filtered = self.matchstats[self.matchstats.Date < before_date]
        if home_away_both == 'home':
            filtered = filtered[filtered.HomeTeam == team_name] 
        elif home_away_both == 'away':
            filtered = filtered[filtered.AwayTeam == team_name]
        elif home_away_both == 'both':
            filtered = filtered[(filtered.HomeTeam == team_name) | (filtered.AwayTeam == team_name)]
        else:
            raise ValueError('Variable ''home_away_both'' must be ''home'', ''away'' or ''both''.')
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
    
    def __init__(self, ha_team, feat_type, n_games, home_away_both_games):
        self.ha_team = ha_team
        self.home_away_both_games = home_away_both_games
        self.feat_type = feat_type
        self.n_games = n_games
        
    def get_value(self, msd, match):
        team_name = match.get_home_or_away_team(self.ha_team)
        df = msd.get_subset(team_name, self.home_away_both_games, match.date, self.n_games)
        if df.shape[0] < self.n_games:#== 0:
            return math.nan
        
        df_home_games = df[df.HomeTeam == team_name]
        df_away_games = df[df.AwayTeam == team_name]
        
        if self.feat_type == 'prcwin':
            nb_home_wins = self.get_number_of_wins(df_home_games, 'H')
            nb_away_wins = self.get_number_of_wins(df_away_games, 'A')
            return (nb_home_wins + nb_away_wins)/df.shape[0]
        
        if self.feat_type == 'goalsscored':
            return df_home_games['FTHG'].sum() + df_away_games['FTAG'].sum()
        
        if self.feat_type == 'goalsagainst':
            return df_home_games['FTAG'].sum() + df_away_games['FTHG'].sum()
        
        if self.feat_type == 'goalsscoredewma':
            return self.calc_goalsscored_ewma(df, team_name, 0.2)
            
        else:
            return math.nan
            print('Feature type: ' + self.feat_type + ' is not implemented')
          
    def get_number_of_wins(self, df, result):
        result_count = df['FTR'].value_counts()
        if result in result_count.index:
            return result_count[result]
        else:
            return 0
    
    def calc_goalsscored_ewma(self, df, team_name, com):
        ewma = 0
        for i, row in df.iterrows():
            column = 'FTHG' if row.HomeTeam == team_name else 'FTAG'
            ewma += row[column]*com
        return ewma
            
#
#path ='C:/Users/olind/machinelearning-predicting-football-results/Data/'
#df = pd.read_csv(path+'CH1718.csv')
#ds = MatchStatsDataset(df, 300)
#dct_features = {
#            'ht_goalsscoredewma_prev20_games':Feature('H', 'goalsscoredewma', 10, 'both'),
#            }
#features = ds.get_features_and_matchdata(dct_features)

