from glob import glob

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib.pyplot as plt
from matplotlib import patches as mpatches
from matplotlib import colors
from matplotlib import font_manager

from highlight_text import fig_text
from fuzzy_match import match
import warnings

from config import (TEMPLATES_DICT as templates_dict, 
                    COUNT_STATS as count_stats, 
                    METRICS_TO_INVERT as invertible_metrics, 
                    POSITIONS_DICT as pos_dict, 
                    POSITIONS_FBREF_DICT as fbref_pos_dict,
                    POSITIONS_COLORS_DICT as col_dict, 
                    SEASON)

warnings.filterwarnings("ignore")

TEXT_COLOR = "k"
LINE_COLOR ="k"        
SCATTER_COLOR = "k"
LABEL_FILL_COLOR = "0.7"
MIN_90s = 4 ##for the player comparison pool, not the queried player themself


font_name = 'Source-Sans-Pro'
font_dirs = ['../Source_Sans_Pro/']
font_file = sorted(font_manager.findSystemFonts(fontpaths=font_dirs))[1]
font_list = [font_manager.FontEntry(font_file, name=font_name)]
font_manager.fontManager.ttflist.extend(font_list)

plt.rcParams['font.family'] = font_name
font_prop_italic = font_manager.FontProperties(fname="../Source_Sans_Pro/SourceSansPro-Italic.ttf", size=8)
font_prop_bold = font_manager.FontProperties(fname="../Source_Sans_Pro/SourceSansPro-SemiBold.ttf", size=16)


def plot_sonar(fig, ax , position, df, player_name, minutes, team_name, season, age):
    """Creates the pizza plot for a player """

    # fig, ax = plt.subplots(figsize=(6,8), subplot_kw={"projection":"polar"})
    
    LABEL_COLOR = TEMPLATE_COLOR = col_dict[position]
    cmap = colors.LinearSegmentedColormap.from_list("", ["white",col_dict[position]])

    bottom = 0
    percentiles = []
    thetas = np.linspace(0, 2*np.pi, len(templates_dict[position]), endpoint=False)
    theta_del = thetas[1] - thetas[0]
    for col in templates_dict[position]:
        player_stat = df.query("Player == @player_name")[col].values[0]
        if col in invertible_metrics:
            percentiles.append(100 - stats.percentileofscore(df[col], player_stat))
        else:
            percentiles.append(stats.percentileofscore(df[col], player_stat))
            

    for perc, theta in zip(percentiles, thetas):
        margins = [0] + [20*(i+1) for i in range(int(perc//20))] + [perc]
        
        for p1, p2, color in zip(margins[:-1], margins[1:], cmap([0.6, 0.7, 0.8, 0.9, 1])):
            ax.bar(theta, p2-p1, bottom=p1, color=color, width=2*np.pi/len(templates_dict[position]), 
                ec="white", align="edge", linewidth=2, zorder=10)

    for theta, perc, label in zip(thetas, percentiles, templates_dict[position]):
        label=label if len(label)<21 else label[:20]+"~"+"\n"+"~"+label[20:]
        t = theta+theta_del/2
        if t>np.pi/2 and t<3*np.pi/2:  
            rotation= -1*np.degrees(t)+180
        else:
            rotation=-1*np.degrees(t)
        ax.text(t, int(perc) if perc<95 else int(perc-8), int(perc), zorder=15, ha='center', va='center', color=TEXT_COLOR, size=8, fontweight='bold')
        ax.scatter(t, int(perc) if perc<95 else int(perc-8), marker="h", fc=TEMPLATE_COLOR, ec=SCATTER_COLOR, s=300, zorder=12, lw=1.3)
        ax.text(t, 110, label, zorder=10, ha='center', va='center', color=LABEL_COLOR, rotation=rotation, size=8,fontweight='bold',
            bbox=dict(facecolor="none", edgecolor=LINE_COLOR, boxstyle='round,pad=0.25', linewidth=1.1))
        ax.plot([theta, theta], [bottom, 100], color=LINE_COLOR, lw=0.7, alpha=0.4, zorder=15, linestyle="-.")        

    ax.plot(np.linspace(0, 2*np.pi, 200), np.ones(200)*100, color=LINE_COLOR, lw=4, zorder=20)
    ax.plot(np.linspace(0, 2*np.pi, 200), np.ones(200)*bottom, color=LINE_COLOR, lw=4, alpha=0.4)
        
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set(rlim=(-5, 100), xticks = [], yticks= [], facecolor="none", alpha=0.1)

    fig.text(s=f"{player_name}, {team_name}", va='center', ha='center', fontsize=18, x=0.5, y=0.96, 
             color=TEXT_COLOR, fontproperties=font_prop_bold)
    fig_text(s=f"Season: <{season}> | Age: <{age}> | Minutes: <{minutes}>", va='center', ha='center', 
                fontsize=11, x=0.5, y=0.933, color=TEXT_COLOR, 
                highlight_textprops=[{"color": TEMPLATE_COLOR}, {"color": TEMPLATE_COLOR}, {"color": TEMPLATE_COLOR}])
    lab_pos = pos_dict[position] if pos_dict[position] not in ['Center Backs', 'Fullbacks'] else 'Defenders'
    fig_text(s=f"Compared to other <{lab_pos}>", va='center', ha='center', fontsize=11, x=0.5, y=0.91, 
                color=TEXT_COLOR, highlight_textprops=[{"color": TEMPLATE_COLOR, "fontweight": "bold"}]
            )
    text = fig.text(s=f"*Minimum Minutes to Qualify: {MIN_90s*90}. **All count stats were adjusted to per 90 before calculating percentiles", 
                    x=0.03, y=0.01, color=TEXT_COLOR, fontproperties=font_prop_italic)

    return fig, ax

def get_df(name, selected_df, df): return selected_df if name in selected_df["Player"] else selected_df.append(df.query("Player == @name"))

def run_and_save_sonar(tweet_player_name, tweet_position=None):
    
    df = pd.read_csv('../data/data.csv')
    df[count_stats] = df[count_stats].div(df['90s'], axis=0)

    player_name = tweet_player_name
    matched_name, confidence = match.extractOne(player_name, df["Player"].values)
    presaved_images = [file.split(".png")[0].split("\\")[-1] for file in glob("../output/*.png")]


    played_90s = df.query("Player == @matched_name")['90s'].values[0]
    if played_90s>=MIN_90s:
        df = df[df['90s']>=MIN_90s].reset_index(drop=True)
    else: 
        df = df[df['90s']>=MIN_90s].reset_index(drop=True).append(df.query("Player == @matched_name")).reset_index(drop=True)

    if matched_name in presaved_images:
        return True, matched_name

    else:    
        fbref_pos_dict_rev = {v:k for k,v in fbref_pos_dict.items()}
        if confidence <= 0.4:
            return False, matched_name

        else:    
            position = tweet_position if tweet_position is not None else fbref_pos_dict_rev[df.query("Player==@matched_name")['Pos'].values[0].split(",")[0]]

            selected_df = df[df["Pos"].str.contains(fbref_pos_dict[position])].reset_index(drop=True)
            MINUTES_PLAYED = int(df.query("Player == @matched_name")["90s"].values[0] * 90)
            TEAM_NAME = df.query("Player == @matched_name")["Squad"].values[0]
            AGE = df.query("Player == @matched_name")["Age"].values[0].split("-")[0]

            fig = plt.figure(figsize=(6, 8), dpi=180)
            ax_bg = fig.add_subplot()
            ax_bg.set_position([0, 0, 1, 1])
            ax_bg.set_axis_off()
            ax_bg.imshow(plt.imread(r"../logos/background.png"))

            ax = fig.add_subplot(projection='polar')

            fig, ax = plot_sonar(fig, ax, position, get_df(matched_name, selected_df, df), matched_name, 
                                 minutes=MINUTES_PLAYED, team_name=TEAM_NAME, season=SEASON, age=AGE)
        
            ax_im = fig.add_subplot()
            ax_im.set_position([0.1, -0.325, 0.8, 0.8])
            ax_im.set_axis_off()
            ax_im.imshow(plt.imread(r"../logos/trans_footer.png"))

            fig.savefig(f"../output/{matched_name}")

            image = plt.imread(f"../output/{matched_name}.png")
            image = image[:, 30:-20, :] ##remove the edges of the plot from the background image

            plt.imsave(f"../output/{matched_name}.png", image)
            print(f"Saved image: {matched_name}")

            return True, matched_name  