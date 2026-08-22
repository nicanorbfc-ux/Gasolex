# ============================================================
# PREPARACIÓN
# ============================================================

import sqlite3
import sys

conexion = sqlite3.connect("gasolex.db")
cursor = conexion.cursor()

from math import sqrt, cos, radians

# ============================================================
# DEFINICIONES DE FUNCIONES
# ============================================================

### Distancia_km()
def distancia_km(lat1, lon1, lat2, lon2):
    diferencia_latitud = (lat2 - lat1) * 111
    diferencia_longitud = (lon2 - lon1) * 111 * cos(radians(lat1))

    distancia = sqrt(
        diferencia_latitud ** 2 +
        diferencia_longitud ** 2
    )

    return distancia

### obtener_parametros()
def obtener_parametros():

    if len(sys.argv) != 6:
        print("Uso: python gasolex.py COMBUSTIBLE PRECIO_MAXIMO RADIO LATITUD LONGITUD")
        sys.exit()

    combustible = sys.argv[1]

    combustibles_validos = ["GOA", "GSP95", "GOP", "GSP98", "GSP95P"]

    if combustible not in combustibles_validos:
        print("Combustible no válido")
        print("Combustibles válidos:", ", ".join(combustibles_validos))
        sys.exit()

    try:
        precio_maximo = float(sys.argv[2])
        radio = float(sys.argv[3])
        latitud_origen = float(sys.argv[4])
        longitud_origen = float(sys.argv[5])
    except ValueError:
        print("El precio máximo, el radio y las coordenadas deben deben ser números")
        sys.exit()

    if precio_maximo == 0:
        precio_sin_limite = True
        precio_maximo = 100
    else:
        precio_sin_limite = False

    return (
        combustible,
        precio_maximo,
        radio,
        latitud_origen,
        longitud_origen,
        precio_sin_limite
    )
### buscar_gasolineras()
def buscar_gasolineras(
    cursor,
    combustibles,
    precio_maximo,
    radio,
    lat_origen,
    lon_origen,
    orden
):

    marcadores = ",".join("?" for _ in combustibles)

    cursor.execute(f"""
        SELECT
            Gasolineras.IDEESS,
            Gasolineras.Rotulo,
            Gasolineras.Direccion,
            Gasolineras.Localidad,
            Gasolineras.Latitud,
            Gasolineras.Longitud,
            Precios.Combustible,
            Precios.Precio
        FROM Precios
        JOIN Gasolineras
            ON Gasolineras.IDEESS = Precios.IDEESS
        WHERE Precios.Combustible IN ({marcadores})
    """, combustibles)

    filas = cursor.fetchall()

    estaciones = {}

    for fila in filas:

        (
            ideess,
            rotulo,
            direccion,
            localidad,
            latitud,
            longitud,
            combustible,
            precio
        ) = fila

        distancia = distancia_km(
            lat_origen,
            lon_origen,
            latitud,
            longitud
        )

        if distancia <= radio:

            if ideess not in estaciones:

                estaciones[ideess] = {
                    "rotulo": rotulo,
                    "direccion": direccion,
                    "localidad": localidad,
                    "latitud": latitud,
                    "longitud": longitud,
                    "distancia": distancia,
                    "precios": {}
                }

            estaciones[ideess]["precios"][combustible] = precio


    resultados = []

    for ideess, estacion in estaciones.items():

        precios = estacion["precios"]

        # ----------------------------------------------------
        # Comprobar si la gasolinera cumple el precio máximo
        # ----------------------------------------------------

        if precio_maximo == 0:

            cumple_precio = True

        else:

            cumple_precio = any(
                precio <= precio_maximo
                for precio in precios.values()
            )

        if cumple_precio:

            resultados.append((
                ideess,
                estacion["rotulo"],
                estacion["direccion"],
                estacion["localidad"],
                estacion["latitud"],
                estacion["longitud"],
                estacion["distancia"],
                precios
            ))

    # ========================================================
    # ORDEN DE LOS RESULTADOS
    # ========================================================

    if orden == "Precio":

        resultados.sort(
            key=lambda fila: (min(fila[7].values()), fila[6])
        )

    else:

        resultados.sort(
            key=lambda fila: fila[6]
        )

    return resultados

### mostrar_resultados()
def mostrar_resultados(resultados):

    for ideess, rotulo, direccion, localidad, precio, distancia in resultados:
        print(
            f"{distancia:.1f} km | "
            f"{precio:.3f} € | "
            f"{rotulo} | "
            f"{direccion} | "
            f"{localidad}"
        )

# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================
if __name__ == "__main__":

    ### Obtener Parámetros
    combustible, precio_maximo, radio, lat_origen, lon_origen, precio_sin_limite = obtener_parametros()

    ### Mostrar encabezado
    print()
    print("GASOLEX")
    print("Combustible:", combustible)
    if precio_sin_limite:
        print("Precio máximo: sin límite")
    else:
        print(f"Precio máximo: {precio_maximo:.2f} €/L")
    print(f"Radio: {radio:.0f} km")
    print()

    ### Buscar
    resultados = buscar_gasolineras(
        cursor,
        combustible,
        precio_maximo,
        radio,
        lat_origen,
        lon_origen
    )

    print("Número de resultados:", len(resultados))
    print()

    ### Mostrar resultados
    mostrar_resultados(resultados)

    ### Cerrar conexión
    conexion.close()