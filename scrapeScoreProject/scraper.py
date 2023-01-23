import pandas as pd
import requests
from bs4 import BeautifulSoup
import json

import warnings
warnings.filterwarnings('ignore')

# Opening JSON file
with open('teams_demo.json') as json_file:
    team_dict = json.load(json_file)

team_df = pd.DataFrame.from_dict(team_dict)


class demo():
    '''
    Match Webscraping and Analysis.
    Scraping Matches and

    Parameters
    ----------
    agent : string, default= Mozilla/5.0 (Windows NT 10.0; Windows; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36
        a characteristic string that lets servers and network peers identify the application,
        operating system, vendor, and/or version of the requesting user agent.

    '''

    def __init__(self,
                 agent='Mozilla/5.0 (Windows NT 10.0; Windows; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'):
        self.agent = agent

    def last_fixtures(self, team):
        '''
        Obtain last 5 fixtures

        Parameters
        ----------
        team : string,
            name of team

        Returns
        -------
        C : dict
            Returns last 5 fixtures

        '''
        url = team_df[team_df['Team'] == team]['url'].values[0]
        response = requests.get(url, headers={'User-Agent': self.agent})

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find_all('table', class_='matches')
            df = pd.read_html(str(table))[0]
            df.drop(df.columns[-2:], axis=1, inplace=True)
            df.rename(columns={'Outcome': 'Home team', 'Home team': 'Outcome', 'Score/Time': 'Away team',
                               'Competition': 'League'}, inplace=True)

            return df[:5]
        except ImportError:
            return ('incorect teamname, country or both')

    def compare(self, team1, team2):
        '''
        Compare last 5 fixtures of each team and return similar team
        and number of similar team as the score

        Parameters
        ----------
        team1 : string,
            name of team

        team2 : string,
            name of team

        Returns
        -------
        C : dict
            Returns similar team and number of similar team as the score
        '''
        try:
            tab1 = self.last_fixtures(team1)
            tab2 = self.last_fixtures(team2)

            t1_home = tab1['Home team'].values.tolist()
            t2_home = tab2['Home team'].values.tolist()

            t1_away = tab1['Away team'].values.tolist()
            t2_away = tab2['Away team'].values.tolist()

            t1_teams = set(t1_home + t1_away)
            t2_teams = set(t2_home + t2_away)

            t1_teams.remove(team1)
            t2_teams.remove(team2)

            similar_team = list(t1_teams & t2_teams)
            score = len(similar_team)

            result = {
                'team': similar_team,
                'score': score
            }

            return result
        except TypeError:
            return ('incorect teamname, country or both')

    def matches(self, date):
        '''
        Obtain available matches

        Parameters
        ----------
        date : string,
            Format(DD/MM/YYY)

        Returns
        -------
        C : dict
            Returns available matches

        '''

        url = 'https://ng.soccerway.com/'
        response = requests.get(url, headers={'User-Agent': self.agent})
        soup = BeautifulSoup(response.text, 'html.parser')
        h2 = soup.find_all('h2')[:-2]

        # Create Empty dataframe
        df1 = pd.DataFrame({'Time': [],
                            'Country': [],
                            'League': [],
                            'Home team': [],
                            'Score': [],
                            'Away team': []
                            })

        # Run loop for each h2 tag and extract informations
        for tag in h2[:5]:
            try:
                # extract country name
                country = tag.find(class_='area-name').text

                # extract competition name
                competition = tag.find(class_='comp-name').text

                # extract url
                url2 = tag.a.get('href')
                url2 = 'https://ng.soccerway.com/' + url2

                # Get extracted url page
                response2 = requests.get(url2, headers={'User-Agent': self.agent})

                # Using beautiful soup to parse it
                soup2 = BeautifulSoup(response2.text, 'html.parser')
                tag2 = soup2.find('li', class_='current')

                # extract url
                url3 = tag2.a.get('href') + 'matches/'
                url3 = 'https://ng.soccerway.com/' + url3

                response3 = requests.get(url3, headers={'User-Agent': self.agent})

                # Using beautiful soup to parse it
                soup3 = BeautifulSoup(response3.text, 'html.parser')
                table3 = soup3.find_all('table', class_='matches')
                # Check if date is in table
                for idx in range(len(table3)):
                    if date in str(table3[idx]):
                        break

                # convert html tabel to pandas dataframe
                df = pd.read_html(str(table3))[idx]

                # Cleaning dataframe
                start = df[df['Day'].str.endswith(date)].index[0]
                end = df[df['Day'].str.endswith(date)].index[-1]
                df = df.iloc[start + 1:end + 2:2]
                df.reset_index(drop=True, inplace=True)
                df.drop(df.columns[-1:], axis=1, inplace=True)
                df.rename(columns={'Day': 'Time', 'Score/Time': 'Score', 'Competition': 'League'}, inplace=True)
                df['Country'] = country
                df['League'] = competition
                df = df[['Time', 'Country', 'League', 'Home team', 'Score', 'Away team']]
                leagues = team_df.League.unique()
                countries = team_df.Country.unique()
                df = df[df['Country'].isin(countries)]
                df = df[df['League'].isin(leagues)]

                # Concate dataframes
                frames = [df1, df]
                df1 = pd.concat(frames)
            except IndexError:
                pass
        # sort dataframe
        final_df = df1.sort_values(['Time'])
        final_df = final_df.reset_index(drop=True)

        return final_df