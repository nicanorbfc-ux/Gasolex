# ============================================================
# PREPARACIÓN
# ============================================================

import streamlit as st
import sqlite3
import requests
import boto3
from botocore.client import Config
import gasolex
from streamlit_geolocation import streamlit_geolocation
import folium
from streamlit_folium import st_folium

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(layout="wide")


# ============================================================
# VARIABLES INICIALES
# ============================================================

if "lat_origen" not in st.session_state:
    st.session_state.lat_origen = 43.36306532

if "lon_origen" not in st.session_state:
    st.session_state.lon_origen = -5.858284443

if "nombre_origen" not in st.session_state:
    st.session_state.nombre_origen = "Plaza de la Libertad, Oviedo"


# ============================================================
# CONEXIÓN CON R2 Y SQLITE
# ============================================================

R2_ACCOUNT_ID = "f0026ea67a66c1918d0233254ca21b0f"

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    region_name="auto",
    aws_access_key_id=st.secrets["R2_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["R2_SECRET_ACCESS_KEY"],
    config=Config(signature_version="s3v4")
)
respuesta = s3.get_object(
    Bucket="gasolex",
    Key="gasolex.db"
)

with open("gasolex.db", "wb") as archivo:
    archivo.write(respuesta["Body"].read())


conexion = sqlite3.connect("gasolex.db")
cursor = conexion.cursor()

cursor.execute("""
    SELECT Valor
    FROM Configuracion
    WHERE Clave = 'FechaDatos'
""")

fecha_datos = cursor.fetchone()[0]

# ============================================================
# DEFINICIONES DE FUNCIONES
# ============================================================

### buscar_coordenadas()
def buscar_coordenadas(direccion):

    url = "https://nominatim.openstreetmap.org/search"

    parametros = {
        "q": direccion,
        "format": "json",
        "limit": 1
    }

    respuesta = requests.get(
        url,
        params=parametros,
        headers={"User-Agent": "GASOLEX"}
    )

    datos = respuesta.json()

    if datos:
        latitud = float(datos[0]["lat"])
        longitud = float(datos[0]["lon"])
        return latitud, longitud

    return None


# ============================================================
# INTERFAZ
# ============================================================

st.title("GASOLEX")
st.write("Encuentra las gasolineras más baratas cerca de ti")


# ============================================================
# ORIGEN
# ============================================================

st.subheader("📍 Origen de la búsqueda")

tipo_origen = st.radio(
    " Opciones",
    [   "Mi ubicación actual",
        "Dirección o localidad",
        "Elegir en el mapa"
    ]
)

# ------------------------------------------------------------
# Mi ubicación actual
# ------------------------------------------------------------

if tipo_origen == "Mi ubicación actual":

    st.write("Pulsa el botón para obtener tu ubicación:")

    col_boton, col_resultado = st.columns([1, 8])

    with col_boton:

        ubicacion = streamlit_geolocation()

    with col_resultado:

        if ubicacion and ubicacion.get("latitude") is not None:

            st.success(
                f"Ubicación obtenida: "
                f"{ubicacion['latitude']:.6f}, "
                f"{ubicacion['longitude']:.6f}"
            )

            st.session_state.lat_origen = ubicacion["latitude"]
            st.session_state.lon_origen = ubicacion["longitude"]
            st.session_state.nombre_origen = "Mi ubicación actual"
# ------------------------------------------------------------
# Elegir en el mapa
# ------------------------------------------------------------

if tipo_origen == "Elegir en el mapa":

    st.write("🗺️ Selecciona tu ubicación en el mapa")

    mapa = folium.Map(
        location=[
            st.session_state.lat_origen,
            st.session_state.lon_origen
        ],
        zoom_start=13
    )

    datos_mapa = st_folium(
        mapa,
        width="100%",
        height=500
    )

    if datos_mapa and datos_mapa.get("last_clicked"):

        latitud = datos_mapa["last_clicked"]["lat"]
        longitud = datos_mapa["last_clicked"]["lng"]

        st.session_state.lat_origen = latitud
        st.session_state.lon_origen = longitud
        st.session_state.nombre_origen = "Ubicación seleccionada"

        st.write(
            f"Ubicación seleccionada: "
            f"{latitud:.6f}, {longitud:.6f}"
        )
# ------------------------------------------------------------
# Dirección o localidad
# ------------------------------------------------------------

if tipo_origen == "Dirección o localidad":

    direccion_origen = st.text_input(
        "Dirección o localidad",
#        value="Plaza de la Libertad, Oviedo"
    )

    col_boton, col_resultado = st.columns([2, 8])

    with col_boton:

        localizar = st.button("LOCALIZAR ORIGEN")

    with col_resultado:

        if localizar:

            coordenadas = buscar_coordenadas(direccion_origen)

            if coordenadas:

                st.session_state.lat_origen = coordenadas[0]
                st.session_state.lon_origen = coordenadas[1]
                st.session_state.nombre_origen = direccion_origen

                st.success(
                    f"Origen localizado: "
                    f"{st.session_state.lat_origen:.6f}, "
                    f"{st.session_state.lon_origen:.6f}"
                )

            else:

                st.error("No se ha encontrado la dirección.")

# ============================================================
# COMBUSTIBLES
# ============================================================
st.subheader("⛽ Seleccionar combustible o combustibles")

combustibles_diesel = {
    "Diésel": "GOA",
    "Diésel Premium": "GOP"
}

combustibles_gasolina = {
    "Gaso95": "GSP95",
    "Gaso95 Premium": "GSP95P",
    "Gaso98": "GSP98"
}


# ------------------------------------------------------------
# Funciones para controlar la selección
# ------------------------------------------------------------

def cambiar_a_diesel():

    st.session_state.gasolina_seleccionadas = []


def cambiar_a_gasolina():

    st.session_state.diesel_seleccionados = []


# ------------------------------------------------------------
# Gasóleos
# ------------------------------------------------------------

st.write("**Gasóleos**")

diesel_seleccionados = st.pills(
    "Selecciona uno o varios",
    list(combustibles_diesel.keys()),
    selection_mode="multi",
    key="diesel_seleccionados",
    on_change=cambiar_a_diesel,
    label_visibility="collapsed"
)


# ------------------------------------------------------------
# Gasolinas
# ------------------------------------------------------------

st.write("**Gasolinas**")

gasolina_seleccionadas = st.pills(
    "Selecciona uno o varios",
    list(combustibles_gasolina.keys()),
    selection_mode="multi",
    key="gasolina_seleccionadas",
    on_change=cambiar_a_gasolina,
    label_visibility="collapsed"
)
# ------------------------------------------------------------
# Precio máximo
# ------------------------------------------------------------

precio_maximo_texto = st.text_input(
    "💶 Precio máximo (€/L)"
)

st.markdown(
    '<div style="margin-top:-18px; margin-bottom:10px; font-size:0.85em;">'
    'Para reducir el nº de resultados o para "Todos" dejar en blanco'
    '</div>',
    unsafe_allow_html=True
)

precio_maximo_valido = True

if precio_maximo_texto.strip() == "":
    precio_maximo = 0

else:

    try:
        precio_maximo = float(
            precio_maximo_texto.replace(",", ".")
        )

    except ValueError:

        st.error(
            "Introduce un precio válido, por ejemplo 1,80."
        )

        precio_maximo_valido = False


# ------------------------------------------------------------
# Radio
# ------------------------------------------------------------

radio = st.number_input(
    "📏 Radio (km)",
    min_value=1.0,
    value=20.0,
    step=1.0
)

st.markdown(
    '<div style="margin-top:-18px; margin-bottom:10px; font-size:0.85em;">'
    'De búsqueda (en línea recta) de las gasolineras'
    '</div>',
    unsafe_allow_html=True
)

# ============================================================
# ORDEN DE LOS RESULTADOS
# ============================================================

numero_combustibles = len(
    diesel_seleccionados
    if diesel_seleccionados
    else gasolina_seleccionadas
)

if numero_combustibles == 1:

    orden = st.radio(
        "Ordenar resultados por:",
        ["Precio", "Distancia"],
        horizontal=True
    )

else:

    orden = "Distancia"
# ============================================================
# BÚSQUEDA
# ============================================================
# ============================================================
# COMPROBAR SELECCIÓN DE COMBUSTIBLE
# ============================================================

hay_combustible = bool(
    diesel_seleccionados or gasolina_seleccionadas
)
if st.button(
    "🔎 BUSCAR",
    type="primary",
    disabled=not hay_combustible
) and precio_maximo_valido:
    # Obtener códigos internos de los combustibles seleccionados

    if diesel_seleccionados:

        combustibles_seleccionados = [
            combustibles_diesel[nombre]
            for nombre in diesel_seleccionados
        ]

    else:

        combustibles_seleccionados = [
            combustibles_gasolina[nombre]
            for nombre in gasolina_seleccionadas
        ]

    resultados = gasolex.buscar_gasolineras(
        cursor,
        combustibles_seleccionados,
        precio_maximo,
        radio,
        st.session_state.lat_origen,
        st.session_state.lon_origen,
        orden
    )

    # ============================================================
    # RESULTADOS
    # ============================================================
    st.write(
        f"Precios actualizados: {fecha_datos}"
    )

    st.write(
        "Número de resultados:",
        len(resultados)
    )

    datos = []

    for (
        ideess,
        rotulo,
        direccion,
        localidad,
        latitud,
        longitud,
        distancia,
        precios
    ) in resultados:

        url_ruta = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={st.session_state.lat_origen},{st.session_state.lon_origen}"
            f"&destination={latitud},{longitud}"
            "&travelmode=driving"
        )

        if len(combustibles_seleccionados) == 1:

            codigo = combustibles_seleccionados[0]

            if orden == "Precio":

                fila = {
                    "Precio": precios[codigo],
                    "Distancia": distancia,
                    "Marca": rotulo,
                    "🚗 Ruta": url_ruta,
                    "Ubicación": f"{localidad} · {direccion}",
                }

            else:

                fila = {
                    "Distancia": distancia,
                    "Precio": precios[codigo],
                    "Marca": rotulo,
                    "🚗 Ruta": url_ruta,
                    "Ubicación": f"{localidad} · {direccion}",
                   "🚗 Ruta": url_ruta
                }

        else:

            fila = {
                "Distancia": distancia
            }

            for nombre, codigo in {
                **combustibles_diesel,
                **combustibles_gasolina
            }.items():

                if codigo in combustibles_seleccionados:

                    if codigo in precios:
                        fila[nombre] =  f"{precios[codigo]:.3f} €/L"
                    else:
                        fila[nombre] = "—"

            fila["Marca"] = rotulo
            fila["🚗 Ruta"] = url_ruta
            fila["Ubicación"] = f"{localidad} · {direccion}"


        datos.append(fila)

    st.dataframe(
        datos,
        hide_index=True,
        width="stretch",
        height=500,
        column_config={
            "Diésel": st.column_config.TextColumn(
                "Diésel",
                width= 65
            ),
            "Diésel Premium": st.column_config.TextColumn(
                "Diésel P",
                width=70
            ),
            "Gaso95": st.column_config.TextColumn(
                "Gaso95",
                width= 65
            ),
            "Gaso95 Premium": st.column_config.TextColumn(
                "Gaso95 Pre",
                width= 75
            ),
            "Gaso98": st.column_config.TextColumn(
                "Gaso98",
                width=65
            ),
            "Precio": st.column_config.NumberColumn(
                "Precio",
                format="%.3f €/L",
                width= 75
            ),
            "Distancia": st.column_config.NumberColumn(
                "Distancia",
                format="%.1f km",
                width= 75
            ),
            "Marca": st.column_config.TextColumn(
                "Marca",
                width= 100
            ),
            "🚗 Ruta": st.column_config.LinkColumn(
                "Ruta",
                width= 60,
                display_text="🚗"
            ),
            "Ubicación": st.column_config.TextColumn(
                "Ubicación",
                width=500
            )
        }
    )
