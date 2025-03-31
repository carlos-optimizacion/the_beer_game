import streamlit as st
import sqlite3
from datetime import datetime
import uuid

# ====================
# CONFIGURACIÓN
# ====================
CLAVE_PROFESOR = "F@brizzio01"

# ====================
# CONEXIÓN BASE DE DATOS
# ====================
def conectar_db():
    return sqlite3.connect("beer_game.db")

# ====================
# TÍTULO PRINCIPAL
# ====================
st.set_page_config(page_title="The Beer Game", layout="centered")
st.title("🎲 The Beer Game - Gestión de Equipos y Jugadores")

# ====================
# SELECCIÓN DE ROL
# ====================
st.sidebar.header("👤 Identificación de usuario")
rol_usuario = st.sidebar.selectbox("¿Quién eres?", ["Alumno", "Profesor"])

mostrar_seccion_crear_equipo = False

if rol_usuario == "Profesor":
    clave_profesor = st.sidebar.text_input("🔐 Clave de acceso del profesor", type="password")
    if clave_profesor == CLAVE_PROFESOR:
        mostrar_seccion_crear_equipo = True
    else:
        st.sidebar.warning("Clave incorrecta. Solo puedes ver la sección de alumnos.")

# ====================
# SECCIÓN 1: CREAR EQUIPO (Solo para profesor)
# ====================
if mostrar_seccion_crear_equipo:
    with st.expander("🧑‍🏫 Crear equipo (solo profesor)", expanded=True):
        st.subheader("1️⃣ Crear un nuevo equipo")
        nombre_equipo = st.text_input("Nombre del equipo")
        clave_equipo = st.text_input("Clave de acceso del equipo (compártela con los alumnos)", type="password")
        submitted_equipo = st.button("Crear equipo")

        if submitted_equipo and nombre_equipo and clave_equipo:
            conn = conectar_db()
            cursor = conn.cursor()

            # Intentamos agregar columna team_password si no existe
            try:
                cursor.execute("ALTER TABLE teams ADD COLUMN team_password TEXT")
                conn.commit()
            except:
                pass  # Ya existe

            team_id = str(uuid.uuid4())
            fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO teams (team_id, team_name, creation_date, team_password)
                VALUES (?, ?, ?, ?)
            """, (team_id, nombre_equipo, fecha_creacion, clave_equipo))

            conn.commit()
            conn.close()
            st.success(f"✅ Equipo '{nombre_equipo}' creado con éxito. Comparte la clave con tus alumnos.")

# ====================
# SECCIÓN 2: UNIRSE COMO JUGADOR (Alumno)
# ====================
with st.expander("🧑‍🎓 Unirse a un equipo como jugador", expanded=(rol_usuario == "Alumno")):
    st.subheader("2️⃣ Unirse a un equipo existente")

    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT team_id, team_name FROM teams")
    equipos = cursor.fetchall()
    conn.close()

    if equipos:
        equipo_seleccionado = st.selectbox("Selecciona tu equipo", [e[1] for e in equipos])
        clave_ingresada = st.text_input("Clave del equipo", type="password")

        nombre_jugador = st.text_input("Tu nombre")
        correo_jugador = st.text_input("Tu correo")
        rol = st.selectbox("Selecciona tu rol", ["Retailer", "Distributor", "Wholesaler", "Factory"])
        boton_unirse = st.button("Unirse al equipo")

        if boton_unirse:
            team_id = [e[0] for e in equipos if e[1] == equipo_seleccionado][0]

            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT team_password FROM teams WHERE team_id = ?", (team_id,))
            clave_real = cursor.fetchone()[0]

            if clave_ingresada == clave_real:
                player_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO players (player_id, team_id, name, role, email)
                    VALUES (?, ?, ?, ?, ?)
                """, (player_id, team_id, nombre_jugador, rol, correo_jugador))
                conn.commit()
                conn.close()
                st.success("✅ ¡Te has unido al equipo correctamente!")
            else:
                st.error("❌ Clave incorrecta. Por favor, consulta con tu profesor.")
    else:
        st.warning("Aún no hay equipos registrados. El profesor debe crearlos primero.")
