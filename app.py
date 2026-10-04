from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Acciones de gracias", page_icon="📊", layout="wide")

ARCHIVO = "responsables_acciones_de_gracia.xlsx"

# ----------------------------------------------------------------------------
# Carga de datos (igual que en el notebook)
# ----------------------------------------------------------------------------
st.sidebar.header("Datos")
subido = st.sidebar.file_uploader("Subir Excel (opcional)", type=["xlsx", "xls"])


@st.cache_data(show_spinner="Cargando datos...")
def cargar(origen) -> pd.DataFrame:
    df = pd.read_excel(origen)
    df.drop(index=0, inplace=True)
    return df


if subido is not None:
    df = cargar(subido)
elif Path(ARCHIVO).exists():
    df = cargar(ARCHIVO)
else:
    st.title("Análisis de servicios")
    st.info(f"Sube el Excel en la barra lateral o coloca `{ARCHIVO}` junto a `app.py`.")
    st.stop()

# ----------------------------------------------------------------------------
# Filtros: columnas "año" y "Responsables"
# Sin selección = todas las opciones (no se filtra). Al elegir algunas, se filtra.
# ----------------------------------------------------------------------------
faltantes = [c for c in ["año", "Responsables"] if c not in df.columns]
if faltantes:
    st.error(f"No encontré estas columnas en el archivo: {faltantes}")
    st.write("Columnas disponibles:", list(df.columns))
    st.stop()

st.sidebar.header("Filtros")

anios = sorted(df["año"].dropna().unique(), key=str)
sel_anios = st.sidebar.multiselect("año", anios, placeholder="Todos")

responsables = sorted(df["Responsables"].dropna().unique(), key=str)
sel_resp = st.sidebar.multiselect("Responsables", responsables, placeholder="Todos")

if sel_anios:
    df = df[df["año"].isin(sel_anios)]
if sel_resp:
    df = df[df["Responsables"].isin(sel_resp)]

st.title("Análisis de servicios")

if df.empty:
    st.warning("Con los filtros seleccionados no hay datos.")
    st.stop()

# ----------------------------------------------------------------------------
# Gráficas (mismo código del notebook)
# ----------------------------------------------------------------------------
word_counts = df['Palabra'].value_counts().reset_index()
word_counts.columns = ['Palabra', 'Frecuencia']

fig = px.bar(word_counts, x='Palabra', y='Frecuencia', title='Frecuencia de Palabra')
st.plotly_chart(fig)

presidir_counts = df['Presidir'].value_counts().reset_index()
presidir_counts.columns = ['Presidir', 'Frecuencia']

fig_presidir = px.bar(presidir_counts, x='Presidir', y='Frecuencia', title='Frecuencia de Presidir')
st.plotly_chart(fig_presidir)

cena1_counts = df['Cena 1'].value_counts()
cena2_counts = df['Cena 2'].value_counts()

# Combine the counts from both columns and sum them up
combined_cena_counts = pd.concat([cena1_counts, cena2_counts]).groupby(level=0).sum().reset_index()
combined_cena_counts.columns = ['Persona', 'Frecuencia']

fig_cena = px.bar(combined_cena_counts, x='Persona', y='Frecuencia', title='Frecuencia Combinada de Cena 1 y Cena 2')
st.plotly_chart(fig_cena)

cables1_counts = df['Cables 1'].value_counts()
cables2_counts = df['Cables 2'].value_counts()

# Combine the counts from both columns and sum them up
combined_cables_counts = pd.concat([cables1_counts, cables2_counts]).groupby(level=0).sum().reset_index()
combined_cables_counts.columns = ['Persona', 'Frecuencia']

fig_cables = px.bar(combined_cables_counts, x='Persona', y='Frecuencia', title='Frecuencia Combinada de Cables 1 y Cables 2')
st.plotly_chart(fig_cables)

puerta1_counts = df['Puerta 1'].value_counts()
puerta2_counts = df['Puerta 2'].value_counts()

# Combine the counts from both columns and sum them up
combined_puerta_counts = pd.concat([puerta1_counts, puerta2_counts]).groupby(level=0).sum().reset_index()
combined_puerta_counts.columns = ['Persona', 'Frecuencia']

fig_puerta = px.bar(combined_puerta_counts, x='Persona', y='Frecuencia', title='Frecuencia Combinada de Puerta 1 y Puerta 2')
st.plotly_chart(fig_puerta)

all_relevant_columns = [
    'Palabra', 'Presidir',
    'Cena 1', 'Cena 2',
    'Cables 1', 'Cables 2',
    'Puerta 1', 'Puerta 2'
]

# Collect value counts for all specified columns
all_counts = []
for col in all_relevant_columns:
    if col in df.columns:
        all_counts.append(df[col].value_counts())

# Concatenate all series and sum the counts for each unique value
combined_all_counts = pd.concat(all_counts).groupby(level=0).sum().reset_index()
combined_all_counts.columns = ['Persona', 'Frecuencia Total']

# Sort by frequency for better visualization
combined_all_counts = combined_all_counts.sort_values(by='Frecuencia Total', ascending=False)

fig_all = px.bar(
    combined_all_counts,
    x='Persona',
    y='Frecuencia Total',
    title='Frecuencia Total Combinada de Todas las Variables Relevantes',
    labels={'Persona': 'Persona / Valor', 'Frecuencia Total': 'Frecuencia Total'}
)
st.plotly_chart(fig_all)
