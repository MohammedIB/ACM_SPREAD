# -*- coding: utf-8 -*-
"""
Created on Sun Apr 27 19:07:34 2025

@author: ibrah
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
st.sidebar.image('logo.png')

st.markdown("# Courbe Spread")
st.sidebar.markdown("# Courbe Spread")

Spreads = pd.read_excel('Spreads.xlsx')

Emetteur = st.sidebar.selectbox("Choisir un emetteur", Spreads['Emetteur'].unique())


def Courbe_Spreads(fichier_excel, emetteur):


    # Lecture du fichier
    df = pd.read_excel(fichier_excel)

    # Nettoyage
    df['Emission'] = pd.to_datetime(df['Emission'])
    df['Echeance'] = pd.to_datetime(df['Echeance'])
    
    # Nettoyer la colonne 'Spread' (retirer le %, remplacer la virgule par un point)
    df['Spread'] = df['Spread'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)

    # Harmoniser la maturité (ex: convertir "52 SEM" en années, ici 1 an)
    def convertir_maturite(val):
        if '52 SEM' in val:
            return 1 
        elif '26 SEM' in val:
            return 0.5
        elif '13 SEM' in val:
            return 0.25
        elif '1 MOIS' in val:
            return 0.083
        else:
            return int(val.split()[0])  # prendre le nombre d'années

    df['Maturite_Num'] = df['Maturite'].apply(convertir_maturite)

    # Filtrer sur l'émetteur si besoin
    if emetteur:
        df = df[df['Emetteur'] == emetteur]

    # Trier par maturité et par date d'émission décroissante
    df = df.sort_values(by=['Maturite_Num', 'Emission'], ascending=[True, False])

    # Garder la dernière émission par maturité
    df_latest = df.drop_duplicates(subset=['Maturite_Num'], keep='first')

    # Trier pour la courbe
    df_latest = df_latest.sort_values(by='Maturite_Num')
    
    # -- Ici on formate pour le tableau affiché --
    df_affichage = df_latest[['Code ISIN', 'Emission', 'Echeance', 'Maturite', 'Spread']].copy()

    # Format des colonnes
    df_affichage['Code ISIN'] = df_affichage['Code ISIN'].astype(str)
    df_affichage['Emission'] = df_affichage['Emission'].dt.strftime('%d/%m/%Y')
    df_affichage['Echeance'] = df_affichage['Echeance'].dt.strftime('%d/%m/%Y')
    df_affichage['Spread'] = (df_affichage['Spread'] * 100).round(2).astype(str) + '%'

    # Afficher la table
    st.subheader("Données utilisées :")
    st.dataframe(df_affichage)
    
    # Tracer avec Plotly
    fig = px.line(
        df_latest,
        x='Maturite',
        y='Spread',
        markers=True,
        title=f"Courbe de Spreads - {emetteur}",
        labels={'Maturite': 'Maturité (années)', 'Spread': 'Spread (%)'}
    )
    fig.update_traces(
            hovertemplate='<b>Maturité</b>: %{x} <br><b>Spread</b>: %{y:.2%}<extra></extra>'
    )
    fig.update_layout(
        xaxis=dict(dtick=1),  # Pour afficher toutes les maturités
        yaxis=dict(tickformat=".2%"),
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

Courbe_Spreads("Spreads.xlsx", Emetteur)
code_isin = st.sidebar.text_input("Entrez un Code ISIN")

if code_isin:
    ligne_isin = df[df['Code ISIN'].astype(str) == code_isin]

    if ligne_isin.empty:
        st.sidebar.warning("Code ISIN non trouvé.")
    else:
        ligne = ligne_isin.iloc[0]

        # Infos de base
        emission = ligne['Emission'].strftime('%d/%m/%Y')
        echeance = ligne['Echeance'].strftime('%d/%m/%Y')
        maturite_nominale = ligne['Maturite']
        spread_marche = ligne['Spread']
        emetteur = ligne['Emetteur']

        # Maturité résiduelle
        today = pd.Timestamp(datetime.today().date())
        maturite_residuelle = (ligne['Echeance'] - today).days / 365

        if maturite_residuelle <= 0:
            st.sidebar.warning("Ce titre est déjà arrivé à échéance.")
        else:
            # Courbe interpolée
            df_curve = df_latest.copy()
            df_curve = df_curve.sort_values(by='Maturite_Num')

            maturites = df_curve['Maturite_Num'].values
            spreads = df_curve['Spread'].values
            spread_interp = np.interp(maturite_residuelle, maturites, spreads)
            ecart = spread_marche - spread_interp

            couleur = "🟢" if ecart < 0 else "🔴"

            st.sidebar.markdown("### Résultat")
            st.sidebar.markdown(f"**Émetteur :** {emetteur}")
            st.sidebar.markdown(f"**Code ISIN :** `{code_isin}`")
            st.sidebar.markdown(f"**Émission :** {emission}")
            st.sidebar.markdown(f"**Échéance :** {echeance}")
            st.sidebar.markdown(f"**Maturité résiduelle :** `{maturite_residuelle:.2f}` ans")
            st.sidebar.markdown(f"**Spread observé :** `{spread_marche:.2%}`")
