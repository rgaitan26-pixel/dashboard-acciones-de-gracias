import io
import unicodedata
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Acciones de gracias", page_icon="📊", layout="wide")

# ----------------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------------
ARCHIVO = "responsables_acciones_de_gracia.xlsx"

# Cada rol y las columnas del Excel que lo componen (igual que en el notebook:
# Cena 1 + Cena 2, Cables 1 + Cables 2, Puerta 1 + Puerta 2).
ROLES = {
    "Palabra": ["Palabra"],
    "Presidir": ["Presidir"],
    "Cena": ["Cena 1", "Cena 2"],
    "Cables": ["Cables 1", "Cables 2"],
    "Puerta": ["Puerta 1", "Puerta 2"],
}


def norm(texto: str) -> str:
    """minúsculas, sin tildes ni espacios sobrantes (año -> ano)."""
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return t.strip().lower()


def buscar_columna(df: pd.DataFrame, candidatos: list[str]):
    mapa = {norm(c): c for c in df.columns}
    for c in candidatos:
        if norm(c) in mapa:
            return mapa[norm(c)]
    return None


# ----------------------------------------------------------------------------
# Carga de datos
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando datos...")
def leer_excel(contenido: bytes) -> pd.DataFrame:
    return pd.read_excel(io.BytesIO(contenido))


st.sidebar.header("Datos")
subido = st.sidebar.file_uploader("Subir Excel (opcional)", type=["xlsx", "xls"])

if subido is not None:
    contenido = subido.getvalue()
elif Path(ARCHIVO).exists():
    contenido = Path(ARCHIVO).read_bytes()
else:
    st.title("📊 Análisis de acciones de gracias")
    st.info(f"Sube el Excel en la barra lateral o coloca `{ARCHIVO}` junto a `app.py`.")
    st.stop()

df = leer_excel(contenido)

# En el notebook se elimina la fila 0 (df.drop(index=0)).
if st.sidebar.checkbox("Omitir la primera fila (como en el notebook)", value=True):
    df = df.iloc[1:].copy()

# ----------------------------------------------------------------------------
# Columnas de año y responsable
# ----------------------------------------------------------------------------
col_anio = buscar_columna(df, ["año", "ano", "anio", "year"])
if col_anio is None:
    col_anio = st.sidebar.selectbox(
        "No encontré la columna de año, elige cuál es:",
        [None] + list(df.columns),
        format_func=lambda x: "(ninguna)" if x is None else str(x),
    )

col_resp = buscar_columna(df, ["responsable"])

if col_anio is not None:
    serie = pd.to_numeric(df[col_anio], errors="coerce")
    if serie.notna().mean() > 0.5:
        df[col_anio] = serie.astype("Int64")
    df = df[df[col_anio].notna()]

# ----------------------------------------------------------------------------
# Formato largo: una fila por (año, rol, persona)
# ----------------------------------------------------------------------------
mapa_cols = {norm(c): c for c in df.columns}
partes = []
for rol, columnas in ROLES.items():
    for nombre in columnas:
        real = mapa_cols.get(norm(nombre))
        if real is None:
            continue
        partes.append(
            pd.DataFrame(
                {
                    "Año": df[col_anio].astype(str) if col_anio else "Sin año",
                    "Rol": rol,
                    "Persona": df[real].astype("string").str.strip(),
                    "Responsable": df[col_resp].astype("string").str.strip() if col_resp else pd.NA,
                }
            )
        )

if not partes:
    st.error("No encontré ninguna de las columnas esperadas (Palabra, Presidir, Cena 1...).")
    st.stop()

largo = pd.concat(partes, ignore_index=True)
largo = largo[largo["Persona"].notna() & (largo["Persona"] != "")]

# ----------------------------------------------------------------------------
# Filtros
# ----------------------------------------------------------------------------
st.sidebar.header("Filtros")

anios = sorted(largo["Año"].unique(), key=lambda x: (len(x), x))
sel_anios = st.sidebar.multiselect("Año", anios, default=anios)

# Si el Excel tiene una columna "Responsable" se filtra por ella;
# si no, "Responsable" es la persona que aparece en cualquiera de los roles.
campo_resp = "Responsable" if col_resp else "Persona"
opciones_resp = sorted(largo[campo_resp].dropna().unique())
sel_resp = st.sidebar.multiselect("Responsable", opciones_resp, default=opciones_resp)

filtrado = largo[largo["Año"].isin(sel_anios) & largo[campo_resp].isin(sel_resp)]

# ----------------------------------------------------------------------------
# Encabezado y KPIs
# ----------------------------------------------------------------------------
st.title("📊 Análisis de acciones de gracias")

if filtrado.empty:
    st.warning("Con los filtros actuales no hay datos.")
    st.stop()

top = filtrado["Persona"].value_counts()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Asignaciones", f"{len(filtrado):,}")
k2.metric("Personas distintas", filtrado["Persona"].nunique())
k3.metric("Años", filtrado["Año"].nunique())
k4.metric("Más frecuente", top.index[0], f"{top.iloc[0]} veces")

tab_resumen, tab_roles, tab_anio, tab_datos = st.tabs(
    ["Resumen", "Por rol", "Evolución por año", "Datos"]
)

# ----------------------------------------------------------------------------
# Resumen
# ----------------------------------------------------------------------------
with tab_resumen:
    total = (
        filtrado.groupby(["Persona", "Rol"]).size().reset_index(name="Frecuencia")
    )
    orden = top.index.tolist()
    fig = px.bar(
        total,
        x="Persona",
        y="Frecuencia",
        color="Rol",
        category_orders={"Persona": orden},
        title="Frecuencia total por persona (apilada por rol)",
    )
    st.plotly_chart(fig)

    cruce = pd.crosstab(filtrado["Persona"], filtrado["Rol"]).reindex(orden)
    fig_h = px.imshow(
        cruce,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Persona × Rol",
    )
    st.plotly_chart(fig_h)

# ----------------------------------------------------------------------------
# Por rol (equivale a los gráficos individuales del notebook)
# ----------------------------------------------------------------------------
with tab_roles:
    roles_presentes = [r for r in ROLES if r in filtrado["Rol"].unique()]
    for i in range(0, len(roles_presentes), 2):
        cols = st.columns(2)
        for c, rol in zip(cols, roles_presentes[i : i + 2]):
            conteo = (
                filtrado[filtrado["Rol"] == rol]["Persona"]
                .value_counts()
                .reset_index()
            )
            conteo.columns = ["Persona", "Frecuencia"]
            c.plotly_chart(
                px.bar(conteo, x="Persona", y="Frecuencia", title=f"Frecuencia de {rol}"),
            )

# ----------------------------------------------------------------------------
# Evolución por año
# ----------------------------------------------------------------------------
with tab_anio:
    if filtrado["Año"].nunique() < 2:
        st.info("Selecciona más de un año para ver la evolución.")
    else:
        por_anio = filtrado.groupby(["Año", "Rol"]).size().reset_index(name="Frecuencia")
        st.plotly_chart(
            px.bar(
                por_anio,
                x="Año",
                y="Frecuencia",
                color="Rol",
                barmode="group",
                title="Asignaciones por año y rol",
            ),
        )
        persona_anio = pd.crosstab(filtrado["Persona"], filtrado["Año"])
        st.plotly_chart(
            px.imshow(
                persona_anio,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Blues",
                title="Persona × Año",
            ),
        )

# ----------------------------------------------------------------------------
# Datos
# ----------------------------------------------------------------------------
with tab_datos:
    st.dataframe(filtrado.drop(columns=[] if col_resp else ["Responsable"]))
    st.download_button(
        "Descargar CSV filtrado",
        filtrado.to_csv(index=False).encode("utf-8-sig"),
        file_name="acciones_filtradas.csv",
        mime="text/csv",
    )
