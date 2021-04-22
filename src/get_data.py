import requests
from bs4 import BeautifulSoup
from bs4 import Comment
from tqdm import tqdm
import pandas as pd
from functools import reduce
from config import (COLUMNS_KEY as md, 
                    NUMERIC_COLUMNS as numeric_cols, 
                    URLS_DICT as player_urls_dict
                    )

def save_dataframe():
	""" Function to run weekly to save dataframe as data.csv"""

	dflist = []
	for key, url in tqdm(player_urls_dict.items(), desc="Collecting tables"):
		r = requests.get(url)
		soup = BeautifulSoup(r.content, "lxml")
		comments = soup.find_all(string=lambda text: isinstance(text, Comment))

		comm_table = sorted(comments, key=len)[-1]
		df = pd.read_html(comm_table)[0]
		df.columns = [x+'_'+y if 'Unnamed' not in x else y for x,y in df.columns]
		df = df.drop_duplicates(subset=['Player']).reset_index(drop=True) ##dropping players who've played for two teams
		df = df.drop(columns = ["Rk"])
		dflist.append(df)
	    
	df = reduce(lambda df1,df2: pd.merge(df1,df2,on=['Player', 'Nation', 'Pos', 'Squad', 'Age']), dflist)
	df = df.query("Player != 'Player'").reset_index(drop=True)

	columns_to_keep = [col for col in df.columns if col in md.keys()]
	df = df[columns_to_keep]  

	df.columns = [md[col] for col in df.columns]
	df = df.loc[:,~df.columns.duplicated()]
	num_cols = [col for col in df.columns if col in numeric_cols]
	df[num_cols] = df[num_cols].astype(float)
	df.loc[:, num_cols].fillna(0, inplace=True)

	df['Turnovers'] = df['Times Misplaced'] + df['Times Dispossessed']
	df['Open-play Shot-creating Actions'] = df['Shot-creating Actions'].astype(float) - df['Dead-ball Shot-creating Actions'].astype(float)
	df['Non-penalty Goals'] = df['Goals'] - df['Penalties Scored']

	df.to_csv('../data/data.csv', index=False)

