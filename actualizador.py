# ============================================================
# GASOLEX V6
# actualizador.py
#
# Actualización de la base de datos SQLite
# ============================================================


# ============================================================
# 1. PREPARACIÓN
# ============================================================

import sqlite3
import requests


# ============================================================
# 2. CONFIGURACIÓN
# ============================================================

RUTA_BD = "gasolex.db"

URL_MINISTERIO = (
    "https://energia.serviciosmin.gob.es/"
    "ServiciosRestCarburantes/PreciosCarburantes/"
    "EstacionesTerrestres/"
)

COMBUSTIBLES = {
    "GOA": "Precio Gasoleo A",
    "GOP": "Precio Gasoleo Premium",
    "GSP95": "Precio Gasolina 95 E5",
    "GSP95P": "Precio Gasolina 95 E5 Premium",
    "GSP98": "Precio Gasolina 98 E5"
}


# ============================================================
# 3. DESCARGA DEL MINISTERIO
# ============================================================
def descargar_datos():

    respuesta = requests.get(URL_MINISTERIO, timeout=30)

    if not respuesta.ok:
        raise Exception(
            f"Error al acceder al Ministerio: "
            f"{respuesta.status_code}"
        )

    datos = respuesta.json()

    if datos["ResultadoConsulta"] != "OK":
        raise Exception("El Ministerio no ha devuelto una consulta OK.")

    return datos           # = request.get.json()

# ============================================================
# 4. PREPARACIÓN DE DATOS
# ============================================================
def cargar_gasolineras(conexion):

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT IDEESS
        FROM Gasolineras
    """)

    return {
        fila[0]
        for fila in cursor.fetchall()
    }


def cargar_precios(conexion):

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT IDEESS, Combustible, Precio
        FROM Precios
    """)

    return {
        (fila[0], fila[1]): fila[2]
        for fila in cursor.fetchall()
    }

# ============================================================
# 5. SIMULACIÓN DE LA ACTUALIZACIÓN. 
# ============================================================
def simular_actualizacion(conexion, estaciones):    #(Gasolex.db, estaciones recibidas)

    gasolineras_actuales = cargar_gasolineras(conexion)
    precios_actuales = cargar_precios(conexion)

    gasolineras_nuevas = 0
    gasolineras_actualizar = 0
    precios_nuevos = 0
    precios_actualizar = 0
    precios_eliminar = 0
    precios_sin_cambios = 0

    ideess_ministerio = set()

    for estacion in estaciones:

        ideess = estacion["IDEESS"]

        ideess_ministerio.add(ideess)

        if ideess in gasolineras_actuales:
            gasolineras_actualizar += 1
        else:
            gasolineras_nuevas += 1

        for combustible, campo in COMBUSTIBLES.items():

            precio = estacion[campo]

            clave = (ideess, combustible)

            if precio != "":

                precio_nuevo = float(precio.replace(",", "."))

                if clave not in precios_actuales:

                    precios_nuevos += 1

                elif precios_actuales[clave] != precio_nuevo:

                    precios_actualizar += 1

                else:

                    precios_sin_cambios += 1
            else:

                if clave in precios_actuales:

                    precios_eliminar += 1

    estaciones_no_recibidas = (
        len(gasolineras_actuales - ideess_ministerio)
    )

    print()
    print("SIMULACIÓN DE ACTUALIZACIÓN")
    print("---------------------------")
    print(f"Estaciones recibidas:       {len(estaciones)}")
    print(f"Estaciones nuevas:          {gasolineras_nuevas}")
    print(f"Estaciones a actualizar:    {gasolineras_actualizar}")
    print(f"Estaciones no recibidas:    {estaciones_no_recibidas}")
    print()
    print(f"Precios nuevos:              {precios_nuevos}")
    print(f"Precios a actualizar:        {precios_actualizar}")
    print(f"Precios sin cambios:         {precios_sin_cambios}")
    print(f"Precios a eliminar:          {precios_eliminar}")

# ============================================================
# 6. COPIA DE SEGURIDAD
# ============================================================
def crear_copia_seguridad():

    from datetime import datetime
    import shutil

    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")

    nombre_copia = f"gasolex_backup_{fecha}.db"

    shutil.copy2(RUTA_BD, nombre_copia)

    print()
    print(f"Copia de seguridad creada: {nombre_copia}")

# ============================================================
# 7. ACTUALIAZACION DE SQLite
# ============================================================
def actualizar_estacion(conexion, estacion):

    cursor = conexion.cursor()

    ideess = estacion["IDEESS"]

    # --------------------------------------------------------
    # Actualizar / insertar datos de la gasolinera
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO Gasolineras (
            IDEESS,
            Rotulo,
            Direccion,
            CP,
            Localidad,
            Municipio,
            Provincia,
            Latitud,
            Longitud,
            Margen,
            Horario,
            TipoVenta,
            Remision,
            IDMunicipio,
            IDProvincia,
            IDCCAA
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(IDEESS) DO UPDATE SET
            Rotulo = excluded.Rotulo,
            Direccion = excluded.Direccion,
            CP = excluded.CP,
            Localidad = excluded.Localidad,
            Municipio = excluded.Municipio,
            Provincia = excluded.Provincia,
            Latitud = excluded.Latitud,
            Longitud = excluded.Longitud,
            Margen = excluded.Margen,
            Horario = excluded.Horario,
            TipoVenta = excluded.TipoVenta,
            Remision = excluded.Remision,
            IDMunicipio = excluded.IDMunicipio,
            IDProvincia = excluded.IDProvincia,
            IDCCAA = excluded.IDCCAA
    """, (
        ideess,
        estacion["Rótulo"],
        estacion["Dirección"],
        estacion["C.P."],
        estacion["Localidad"],
        estacion["Municipio"],
        estacion["Provincia"],
        float(estacion["Latitud"].replace(",", ".")),
        float(estacion["Longitud (WGS84)"].replace(",", ".")),
        estacion["Margen"],
        estacion["Horario"],
        estacion["Tipo Venta"],
        estacion["Remisión"],
        estacion["IDMunicipio"],
        estacion["IDProvincia"],
        estacion["IDCCAA"]
    ))

    # --------------------------------------------------------
    # Actualizar / insertar / eliminar precios
    # --------------------------------------------------------

    for combustible, campo in COMBUSTIBLES.items():

        precio = estacion[campo]

        if precio != "":

            precio = float(precio.replace(",", "."))

            cursor.execute("""
                INSERT INTO Precios (
                    IDEESS,
                    Combustible,
                    Precio
                )
                VALUES (?, ?, ?)

                ON CONFLICT(IDEESS, Combustible) DO UPDATE SET
                    Precio = excluded.Precio
            """, (
                ideess,
                combustible,
                precio
            ))

        else:

            cursor.execute("""
                DELETE FROM Precios
                WHERE IDEESS = ?
                AND Combustible = ?
            """, (
                ideess,
                combustible
            ))
# ============================================================
# 8. VALIDACIÓN
# ============================================================

def validar_actualizacion(conexion, fecha_datos):

    cursor = conexion.cursor()

    # --------------------------------------------------------
    # Fecha de los datos
    # --------------------------------------------------------

    cursor.execute("""
        SELECT Valor
        FROM Configuracion
        WHERE Clave = 'FechaDatos'
    """)

    fecha_bd = cursor.fetchone()

    if fecha_bd is None or fecha_bd[0] != fecha_datos:
        raise Exception(
            "La FechaDatos de la BD no coincide con la descarga."
        )

    # --------------------------------------------------------
    # Número de gasolineras
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM Gasolineras
    """)

    numero_gasolineras = cursor.fetchone()[0]

    if numero_gasolineras == 0:
        raise Exception(
            "La tabla Gasolineras ha quedado vacía."
        )

    # --------------------------------------------------------
    # Número de precios
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM Precios
    """)

    numero_precios = cursor.fetchone()[0]

    if numero_precios == 0:
        raise Exception(
            "La tabla Precios ha quedado vacía."
        )

    # --------------------------------------------------------
    # Precios sin gasolinera correspondiente
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM Precios
        WHERE IDEESS NOT IN (
            SELECT IDEESS
            FROM Gasolineras
        )
    """)

    precios_huerfanos = cursor.fetchone()[0]

    if precios_huerfanos != 0:
        raise Exception(
            f"Hay {precios_huerfanos} precios sin gasolinera."
        )

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print()
    print("VALIDACIÓN")
    print("----------")
    print(f"Fecha de datos:          {fecha_bd[0]}")
    print(f"Gasolineras:             {numero_gasolineras}")
    print(f"Precios:                 {numero_precios}")
    print(f"Precios sin gasolinera:  {precios_huerfanos}")
    print("Validación correcta.")

# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print("GASOLEX — Actualizador")
print("----------------------")

datos = descargar_datos()

print(f"Fecha de los datos: {datos['Fecha']}")
print(f"Resultado consulta: {datos['ResultadoConsulta']}")

estaciones = datos["ListaEESSPrecio"]

print(f"Estaciones recibidas: {len(estaciones)}")

# ------------------------------------------------------------
# Simulación
# ------------------------------------------------------------

conexion = sqlite3.connect(RUTA_BD)

simular_actualizacion(conexion, estaciones)

conexion.close()

# ------------------------------------------------------------
# Copia de seguridad
# ------------------------------------------------------------

crear_copia_seguridad()

# ------------------------------------------------------------
# Actualización de SQLite
# ------------------------------------------------------------

conexion = sqlite3.connect(RUTA_BD)

try:

    conexion.execute("PRAGMA foreign_keys = ON")

    conexion.execute("BEGIN")

    conexion.execute("""
        INSERT INTO Configuracion (Clave, Valor)
        VALUES ('FechaDatos', ?)
        ON CONFLICT(Clave) DO UPDATE SET Valor = excluded.Valor
    """, (datos["Fecha"],))

    print()
    print(f"Actualizando {len(estaciones)} estaciones...")

    for numero, estacion in enumerate(estaciones, start=1):

        actualizar_estacion(conexion, estacion)

        if numero % 1000 == 0:
            print(f"{numero} / {len(estaciones)}")

    print(f"{len(estaciones)} / {len(estaciones)}")

    conexion.commit()

    print("Actualización realizada correctamente.")
    print("COMMIT ejecutado.")

    validar_actualizacion(conexion, datos["Fecha"])

except Exception as error:

    conexion.rollback()

    print()
    print("ERROR durante la actualización.")
    print(f"ROLLBACK ejecutado: {error}")

finally:

    conexion.close()

print()
print("Prueba finalizada.")