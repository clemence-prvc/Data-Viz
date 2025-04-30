import streamlit as st
st.set_page_config(page_title="Dashboard Energy Europe", layout="wide", page_icon="🌍")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.patches import FancyArrowPatch
import numpy as np

# Remplacez tous les chemins locaux par :
price_france = pd.read_csv("day_ahead_price_france.csv", sep=",")
price_belgium = pd.read_csv("day_ahead_price_belgium.csv", sep=",")
price_espagne = pd.read_csv("day_ahead_price_espagne.csv", sep=",")
price_italy = pd.read_csv("day_ahead_price_italy.csv", sep=",")
price_paysbas = pd.read_csv("day_ahead_price_paysbas.csv", sep=",")
price_portugal = pd.read_csv("day_ahead_price_portugal.csv", sep=",")
price_suisse = pd.read_csv("day_ahead_price_suisse.csv", sep=",")
price_irlande = pd.read_csv("day_ahead_price_irlande.csv", sep=",")
price_allemagne = pd.read_csv("day_ahead_price_allemagne.csv", sep=",")

def nettoyer_prix(df):
    df = df.drop(columns=['Intraday Price (EUR/MWh)', 'Sequence', 'Area', 'Intraday Period (CET/CEST)'])
    df = df.rename(columns={
        'MTU (CET/CEST)': 'Intervalle temps',
        'Day-ahead Price (EUR/MWh)': 'Day ahead price'
    })
    
    return df

price_france = nettoyer_prix(price_france)
price_belgium = nettoyer_prix(price_belgium)
price_espagne = nettoyer_prix(price_espagne)
price_italy = nettoyer_prix(price_italy)
price_paysbas = nettoyer_prix(price_paysbas)
price_portugal = nettoyer_prix(price_portugal)
price_suisse = nettoyer_prix(price_suisse)
price_irlande = nettoyer_prix(price_irlande)
price_allemagne = nettoyer_prix(price_allemagne)

price_france['Country'] = 'France'
price_belgium['Country'] = 'Belgium'
price_espagne['Country'] = 'Spain'
price_italy['Country'] = 'Italy'
price_paysbas['Country'] = 'Netherlands'
price_portugal['Country'] = 'Portugal'
price_suisse['Country'] = 'Switzerland'
price_irlande['Country'] = 'Ireland'
price_allemagne['Country'] = 'Germany'

price_allemagne['Intervalle temps'] = pd.to_datetime(price_allemagne['Intervalle temps'].str.split(' - ').str[0], format='%d/%m/%Y %H:%M:%S', errors='coerce')
price_allemagne.set_index('Intervalle temps', inplace=True)
price_allemagne_numeric = price_allemagne.select_dtypes(include='number')
price_allemagne_hourly = price_allemagne_numeric.resample('H').mean()
price_allemagne_hourly.reset_index(inplace=True)

price_allemagne_hourly['Country'] = 'Germany'

def split_intervalle_temps(df):
    df[['Date début', 'Date fin']] = df['Intervalle temps'].str.split(' - ', expand=True)
    df['Date'] = df['Date début'].str.extract(r'(\d{2}/\d{2}/\d{4})')[0]
    df['Heure début'] = df['Date début'].str.extract(r'(\d{2}:\d{2}:\d{2})')[0]
    df['Heure fin'] = df['Date fin'].str.extract(r'(\d{2}:\d{2}:\d{2})')[0]
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y').dt.date
    df = df.drop(columns=['Intervalle temps', 'Date début', 'Date fin'])
    return df

df_france = split_intervalle_temps(price_france)
df_belgium = split_intervalle_temps(price_belgium)
df_espagne = split_intervalle_temps(price_espagne)
df_italy = split_intervalle_temps(price_italy)
df_paysbas = split_intervalle_temps(price_paysbas)
df_portugal = split_intervalle_temps(price_portugal)
df_suisse = split_intervalle_temps(price_suisse)
df_irlande = split_intervalle_temps(price_irlande)

price_allemagne_hourly[['Date', 'Heure début']] = price_allemagne_hourly['Intervalle temps'].astype(str).str.split(' ', expand=True)
price_allemagne_hourly['Heure fin'] = (pd.to_datetime(price_allemagne_hourly['Heure début'].astype(str)) + pd.Timedelta(hours=1)).dt.time
price_allemagne_hourly.drop(columns=['Intervalle temps'], inplace=True)

price_allemagne_hourly['Day ahead price'] = round(price_allemagne_hourly['Day ahead price'], 2)
price_allemagne_hourly['Day ahead price'] = price_allemagne_hourly['Day ahead price'].astype(float)

def fusionner_prix_par_pays(df_list, pays_list):
    def standardiser_temps(df):
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df['Heure début'] = pd.to_datetime(df['Heure début'], format='%H:%M:%S').dt.strftime('%H:%M:%S')
        df['Heure fin'] = pd.to_datetime(df['Heure fin'], format='%H:%M:%S').dt.strftime('%H:%M:%S')
        return df
    
    dfs_standardises = []
    for df, pays in zip(df_list, pays_list):
        df = df.copy()
        df = standardiser_temps(df)
        df = df.rename(columns={'Day ahead price': f'Day_ahead_{pays}'})
        dfs_standardises.append(df[['Date', 'Heure début', 'Heure fin', f'Day_ahead_{pays}']])
    
    df_final = dfs_standardises[0]
    for df in dfs_standardises[1:]:
        df_final = pd.merge(
            df_final,
            df,
            on=['Date', 'Heure début', 'Heure fin'],
            how='outer'
        )
    
    return df_final.sort_values(['Date', 'Heure début'])

df_list = [price_france, price_belgium, price_espagne, price_italy, 
           price_paysbas, price_portugal, price_suisse, price_irlande, 
           price_allemagne_hourly]
pays_list = ['France', 'Belgium', 'Spain', 'Italy', 'Netherlands', 
             'Portugal', 'Switzerland', 'Ireland', 'Germany']

df_merged = fusionner_prix_par_pays(df_list, pays_list)

df_ecart_par_jour = df_merged.groupby('Date')[[
    'Day_ahead_France',
    'Day_ahead_Belgium',
    'Day_ahead_Spain',
    'Day_ahead_Italy',
    'Day_ahead_Netherlands',
    'Day_ahead_Portugal',
    'Day_ahead_Switzerland',
    'Day_ahead_Ireland',
    'Day_ahead_Germany'
]].agg(lambda x: x.max() - x.min()).round(2).reset_index()
df_ecart_par_jour.head()

df_ecart_long = df_ecart_par_jour.melt(
    id_vars='Date',
    value_vars=['Day_ahead_France', 'Day_ahead_Belgium', 'Day_ahead_Spain',
                'Day_ahead_Italy', 'Day_ahead_Netherlands', 'Day_ahead_Portugal',
                'Day_ahead_Switzerland', 'Day_ahead_Ireland', 'Day_ahead_Germany'],
    var_name='Pays',
    value_name='Ecart Max'
)

df_ecart_long['Pays'] = df_ecart_long['Pays'].str.replace('Day_ahead_', '')

coords = {
    'Belgium': (4.4699, 50.5039),
    'France': (2.2137, 46.2276),
    'Switzerland': (8.2275, 46.8182),
    'Germany': (8.6821, 50.1109),
    'Spain': (-3.7492, 40.4637),
    'Great Britain': (-3.4360, 55.3781),
    'Italy': (9.1905, 45.4668)
}

import pandas as pd
df = pd.DataFrame({
    "Flux": [
        "Belgium → France", "Switzerland → France", "Germany → France",
        "Spain → France", "France → Belgium", "France → Switzerland",
        "France → Germany", "France → Spain", "France → Great Britain",
        "France → Italy"
    ],
    "Somme": [
        1988681.51, 834827.25, 586285.32, 6308178.92, 14543220.35,
        13242337.3, 20360504.13, 9251828.93, 20666253.75, 14977206.25
    ]
})
df[['Source', 'Target']] = df['Flux'].str.split(' → ', expand=True)

df_merged['Année'] = pd.to_datetime(df_merged['Date']).dt.year
df_merged['Heure'] = pd.to_datetime(df_merged['Heure début'], format='%H:%M:%S').dt.hour

df_melted = df_merged.melt(
    id_vars=['Année', 'Heure', 'Date'],
    value_vars=['Day_ahead_France', 'Day_ahead_Belgium', 'Day_ahead_Spain', 'Day_ahead_Italy', 'Day_ahead_Netherlands', 'Day_ahead_Portugal', 'Day_ahead_Switzerland', 'Day_ahead_Ireland', 'Day_ahead_Germany'],
    var_name='Pays',
    value_name='Prix Day Ahead'
)

df_melted['Pays'] = df_melted['Pays'].str.replace('Day_ahead_', '')

df_adam=df_merged.copy()

type(df_adam.groupby('Date')['Day_ahead_France'].max())
df_adam.groupby('Date')['Day_ahead_France'].min()
df_adam_spread=df_adam.groupby('Date')['Day_ahead_France'].max() - df_adam.groupby('Date')['Day_ahead_France'].min()
df_adam_spread=pd.DataFrame(df_adam_spread)
for i in df_adam.columns[3:12]:
    df_adam_spread[i] = df_adam.groupby('Date')[i].max() - df_adam.groupby('Date')[i].min()

df_adam_spread_somme=pd.DataFrame(df_adam_spread.sum(axis=0))
df_adam_spread_somme.columns=['Somme']
df_adam_spread_somme = df_adam_spread_somme.reset_index()

df_adam_spread_somme.columns = ['Pays', 'Somme']

df_adam_spread_somme['Pays'] = df_adam_spread_somme['Pays'].str.replace('Day_ahead_', '')

df_adam_spread_somme.transpose()

st.title("🌍 Analysis of energy prices in Europe (2024)")

# Section 1
st.header("🗺️ Map of day-ahead prices by country by day and time in 2024")

df_melted['Jour_Heure'] = df_melted['Date'].astype(str) + ' ' + df_melted['Heure'].astype(str) + ':00:00'

fig3 = px.choropleth(
    df_melted,
    locations='Pays',
    locationmode='country names',
    color='Prix Day Ahead',
    hover_name='Pays',
    animation_frame='Jour_Heure',
    animation_group='Pays',
    color_continuous_scale='Viridis',
    scope='europe'
)

fig3.update_layout(
    width=800,
    height=500,
    updatemenus=[dict(
        type='buttons',
        showactive=False,
        buttons=[dict(
            label='Play',
            method='animate',
            args=[None, dict(frame=dict(duration=500, redraw=True), fromcurrent=True)]
        )]
    )]
)

st.plotly_chart(fig3, use_container_width=True)

# Section 2
st.header("🔌 Cross-border electricity flows in Europe")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    fig2 = plt.figure(figsize=(4, 4))
    ax = plt.axes(projection=ccrs.Mercator())
    ax.add_feature(cfeature.LAND.with_scale('50m'), facecolor='lightgrey')
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.COASTLINE)
    ax.set_extent([-10, 20, 35, 60])  # Europe

    def curved_arrow(ax, lon1, lat1, lon2, lat2, width=1, color='red', alpha=0.5, curvature=0.2):
        arrow = FancyArrowPatch(
            (lon1, lat1), (lon2, lat2),
            connectionstyle=f"arc3,rad={curvature}",
            arrowstyle='->,head_length=0.5,head_width=0.8',
            mutation_scale=10,
            shrinkA=3,
            shrinkB=3,
            color=color,
            linewidth=width,
            alpha=alpha,
            transform=ccrs.PlateCarree()
        )
        ax.add_patch(arrow)

    for _, row in df.iterrows():
        lon1, lat1 = coords[row['Source']]
        lon2, lat2 = coords[row['Target']]
        color = 'olive' if 'France →' in row['Flux'] else 'navy'
        width = row['Somme'] / 5e6
        alpha = 0.2 + 0.8 * (row['Somme'] / df['Somme'].max())
        curved_arrow(ax, lon1, lat1, lon2, lat2, width=width, color=color, alpha=alpha)

    label_positions = {
        'Belgium': (0, 0.8), 
        'France': (0, -1.0),
        'Switzerland': (1.5, 0.8),
        'Germany': (0, 0.8),
        'Spain': (0, -0.8),
        'Great Britain': (2.8, 0.5),
        'Italy': (1.5, -0.3)
    }

    for name, (lon, lat) in coords.items():
        ax.plot(lon, lat, 'ko', markersize=4, transform=ccrs.PlateCarree())
        dx, dy = label_positions[name]
        ax.text(lon + dx, lat + dy, name.replace('-', '-\n'),
                fontsize=4,
                ha='center',
                va='center',
                transform=ccrs.PlateCarree(),
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

    st.pyplot(fig2, use_container_width=False) 

# Section 3
st.header("📈 Maximum day-ahead price spread by country and day")

fig1 = px.choropleth(
    df_ecart_long,
    locations='Pays',
    locationmode='country names',
    color='Ecart Max',
    hover_name='Pays',
    animation_frame='Date',
    animation_group='Pays',
    color_continuous_scale='Inferno',
    scope='europe'
)

fig1.update_layout(
    width=800,
    height=500,
    updatemenus=[dict(
        type='buttons',
        showactive=False,
        buttons=[dict(
            label='Play',
            method='animate',
            args=[None, dict(frame=dict(duration=500, redraw=True), fromcurrent=True)]
        )]
    )]
)

st.plotly_chart(fig1, use_container_width=True)

# Section 4
st.header("📊 Sum of daily spreads of day-ahead prices")

df_adam_spread_somme = pd.DataFrame(df_adam_spread.sum(axis=0), columns=['Somme'])
df_adam_spread_somme = df_adam_spread_somme.reset_index()
df_adam_spread_somme.columns = ['Pays', 'Somme']
df_adam_spread_somme['Pays'] = df_adam_spread_somme['Pays'].str.replace('Day_ahead_', '')

fig4 = px.choropleth(
    df_adam_spread_somme,
    locations='Pays',
    locationmode='country names',
    color='Somme',
    hover_name='Pays',
    color_continuous_scale='Viridis',
    labels={'Somme': 'Somme des écarts (€)'},
    scope='europe'
)

fig4.update_layout(
    width=800,
    height=500,
    geo=dict(showframe=False, showcoastlines=True),
    margin=dict(l=0, r=0, t=40, b=0)
)

st.plotly_chart(fig4, use_container_width=True)

# Section 5
st.header("💰 Profitability analysis of investment project")

investissement_initial = 15
benefice_annuel = 4
annees = np.arange(0, 21)

flux_cumules = -investissement_initial + benefice_annuel * annees
point_equilibre = investissement_initial / benefice_annuel

fig5 = go.Figure()

fig5.add_trace(go.Scatter(
    x=annees,
    y=flux_cumules,
    mode='lines+markers',
    name='Bénéfice cumulé',
    line=dict(color='green', width=3),
    marker=dict(size=8),
    hovertemplate='Année %{x}<br>%{y} M€<extra></extra>'
))

fig5.add_trace(go.Scatter(
    x=[point_equilibre],
    y=[0],
    mode='markers',
    name='Point d\'équilibre',
    marker=dict(color='red', size=12),
    hovertemplate=f'Équilibre: {point_equilibre:.1f} ans<extra></extra>'
))

fig5.add_hline(y=0, line_dash="dash", line_color="gray")

fig5.update_layout(
    title='<b>Rentabilité du projet sur 20 ans</b><br><sup>Investissement initial: 15M€ | Bénéfice annuel: 4M€</sup>',
    xaxis_title='Années',
    yaxis_title='Cumul (M€)',
    hovermode='x unified',
    template='plotly_white',
    annotations=[
        dict(
            x=point_equilibre,
            y=0,
            xref="x",
            yref="y",
            text=f"Équilibre: {point_equilibre:.1f} ans",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40
        ),
        dict(
            x=20,
            y=flux_cumules[-1],
            text=f"{flux_cumules[-1]} M€ après 20 ans",
            bgcolor="white",
            bordercolor="black",
            showarrow=False
        )
    ],
    margin=dict(l=0, r=0, t=80, b=0)
)

st.plotly_chart(fig5, use_container_width=True)
