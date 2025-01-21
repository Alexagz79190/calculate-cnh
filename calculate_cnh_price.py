import pandas as pd
import numpy as np
import os
from datetime import datetime
import streamlit as st

# Streamlit UI
st.title("Traitement des fichiers CNH")
st.write("Veuillez charger les fichiers nécessaires et lancer le traitement.")

# Section : Répertoire des fichiers
directory = st.text_input("Répertoire des fichiers TXT :", r"G:\Pôle_DATA\Tarif\Cnh")

# Bouton pour lancer le traitement
if st.button("Lancer le traitement"):
    try:
        # Recherche du dernier fichier TXT modifié
        st.write("Recherche du dernier fichier modifié...")
        list_of_files = [f for f in os.listdir(directory) if f.endswith(".txt")]
        if not list_of_files:
            st.error("Aucun fichier TXT trouvé dans le répertoire spécifié.")
            st.stop()

        latest_file = max([os.path.join(directory, f) for f in list_of_files], key=os.path.getmtime)
        st.write(f"Dernier fichier trouvé : `{latest_file}`")

        # Lecture du fichier TXT
        st.write("Lecture du fichier tarif CNH...")
        colspecs = [
            (0, 18), (18, 58), (58, 59), (59, 60), (60, 68), (68, 79), (79, 92),
            (92, 97), (97, 101), (101, 102), (102, 107), (107, 112), (112, 113), (113, 116)
        ]
        df = pd.read_fwf(latest_file, colspecs=colspecs, header=None, skiprows=1)
        st.write(f"Fichier chargé avec succès : {len(df)} lignes.")

        # Renommage des colonnes
        df.columns = [
            "Référence pièce", "Description Pièces", "Type", "Libre", "Date du prix", "Column6", "Column7",
            "Column8", "Column9", "Column10", "Column11", "Column12", "Column13", "Column14"
        ]

        # Traitement des valeurs et conversion des types
        st.write("Traitement des données...")
        df["Date du prix"] = pd.to_numeric(df["Date du prix"], errors='coerce')
        for col in ["Column6", "Column7", "Column8", "Column12"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.fillna(0, inplace=True)
        df["Prix tarif"] = df["Column6"] / 100
        df["Poids kg"] = df["Column7"] / 1000

        # Ajout et calcul des colonnes supplémentaires
        df.rename(columns={
            "Column8": "Quantité", "Column9": "Première ligne de produit",
            "Column10": "Code remise", "Column11": "PCC", "Column12": "MPC"
        }, inplace=True)
        df["Quantité"] = df["Quantité"].replace(0, 1)
        df["MPC"] = df["MPC"].astype(str)
        df["Famille Mistral"] = df["MPC"].str[:3]

        # Table de remise
        remise_data = {
            "Code CNH": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "K", "M", "Z", "1", "2"],
            "Taux de remise": [0.50, 0.44, 0.40, 0.30, 0.30, 0.30, 0.40, 0.25, 0.15, 0.46, 0.24, 0.00, 0.38, 0.45]
        }
        remise_df = pd.DataFrame(remise_data)
        df = pd.merge(df, remise_df, how="left", left_on="Code remise", right_on="Code CNH")

        # Calcul du prix net
        df["Prix net"] = (df["Prix tarif"] - df["Prix tarif"] * df["Taux de remise"]).round(2)
        df["Date d'application du prix"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Création des DataFrames pour export
        export_df_bo = pd.DataFrame({
            "Identifiant fournisseur": 102,
            "Référence fournisseur": df["Référence pièce"],
            "Prix d'achat HT": df["Prix net"],
            "Date d'application du prix": df["Date d'application du prix"],
            "Prix de vente public": df["Prix tarif"],
            "Poids": df["Poids kg"],
        })

        export_df_agri = pd.DataFrame({
            "Référence - Fournisseur (identifiant)": 102,
            "Référence - Référence Fournisseur": df["Référence pièce"],
            "Prix d'achat": df["Prix net"],
            "Prix tarif": df["Prix tarif"],
            "Conditionnement d'achat": df["Quantité"],
            "Poids": df["Poids kg"],
        })

        # Téléchargement des fichiers
        st.write("Téléchargement des fichiers générés :")
        st.download_button(
            label="Télécharger import-prix-bo.csv",
            data=export_df_bo.to_csv(index=False, sep=';', encoding='latin-1'),
            file_name="import-prix-bo.csv"
        )
        st.download_button(
            label="Télécharger import-prix-article-pole-agri.csv",
            data=export_df_agri.to_csv(index=False, sep=';', encoding='latin-1'),
            file_name="import-prix-article-pole-agri.csv"
        )

        st.success("Traitement terminé avec succès !")

    except Exception as e:
        st.error(f"Erreur : {e}")
