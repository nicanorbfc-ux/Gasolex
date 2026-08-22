# ============================================================
# PREPARACIÓN
# ============================================================

import streamlit as st
import sqlite3
import requests
import gasolex
from streamlit_geolocation import streamlit_geolocation


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
# CONEXIÓN CON SQLITE
# ============================================================

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

st.subheader("Parámetros de búsqueda")


# ============================================================
# ORIGEN
# ============================================================

st.subheader("Origen")

tipo_origen = st.radio(
    "¿Cómo quieres indicar el origen?",
    [
        "Mi ubicación actual",
        "Dirección o localidad",
        "Coordenadas"
    ]
)


# ------------------------------------------------------------
# Mi ubicación actual
# ------------------------------------------------------------

if tipo_origen == "Mi ubicación actual":

    st.write("Pulsa el botón para obtener tu ubicación:")

    ubicacion = streamlit_geolocation()

    st.write("DEBUG ubicación:", ubicacion)

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
# Coordenadas
# ------------------------------------------------------------

if tipo_origen == "Coordenadas":

    lat_origen = st.number_input(
        "Latitud",
        value=st.session_state.lat_origen,
        format="%.8f"
    )

    lon_origen = st.number_input(
        "Longitud",
        value=st.session_state.lon_origen,
        format="%.8f"
    )

    st.session_state.lat_origen = lat_origen
    st.session_state.lon_origen = lon_origen
    st.session_state.nombre_origen = "Coordenadas introducidas"


# ------------------------------------------------------------
# Dirección o localidad
# ------------------------------------------------------------

if tipo_origen == "Dirección o localidad":

    direccion_origen = st.text_input(
        "Dirección o localidad",
        value="Plaza de la Libertad, Oviedo"
    )

    if st.button("LOCALIZAR ORIGEN"):

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
# MOSTRAR ORIGEN
# ============================================================

st.subheader("Origen seleccionado")

st.write(
    f"📍 Origen: **{st.session_state.nombre_origen}**"
)

st.write(
    f"Coordenadas: "
    f"**{st.session_state.lat_origen:.6f}, "
    f"{st.session_state.lon_origen:.6f}**"
)


# ============================================================
# PARÁMETROS DE BÚSQUEDA
# ============================================================
# ============================================================
# COMBUSTIBLES
# ============================================================

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
    "Precio máximo (€/L)",
    value="1.80"
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
    "Radio (km)",
    min_value=1.0,
    value=20.0,
    step=1.0
)


# ============================================================
# RESUMEN DE LA BÚSQUEDA
# ============================================================

st.subheader("Resumen de búsqueda")

if precio_maximo == 0:
    texto_precio = "Sin límite de precio"

else:
    texto_precio = f"Hasta {precio_maximo:.2f} €/L"

nombres_combustibles = (
    diesel_seleccionados
    if diesel_seleccionados
    else gasolina_seleccionadas
)

st.write(
    f"⛽ Combustible: **{', '.join(nombres_combustibles)}**"
)

st.write(
    f"💶 Precio máximo: **{texto_precio}**"
)

st.write(
    f"📏 Radio: **{radio:.0f} km**"
)

st.write(
    f"📍 Origen: **{st.session_state.nombre_origen}**"
)

st.write(
    f"Coordenadas: "
    f"**{st.session_state.lat_origen:.6f}, "
    f"{st.session_state.lon_origen:.6f}**"
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
        width="content",
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
                width=300
            )
        }
    )
