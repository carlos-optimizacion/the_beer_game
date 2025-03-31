import streamlit as st
import sqlite3
import uuid

# ========================
# CONFIGURACIÓN
# ========================
st.set_page_config(page_title="The Beer Game - Jugar", layout="centered")
st.title("🚚 The Beer Game - Ronda Semanal")

# ========================
# FUNCIONES
# ========================
def conectar_db():
    return sqlite3.connect("beer_game.db")

def obtener_jugadores_por_equipo():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.team_id, t.team_name, p.name, p.role
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
    """)
    data = cursor.fetchall()
    conn.close()
    return data

def obtener_estado_actual(team_id, role):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT week, stock, backorder, incoming_order, incoming_shipment
        FROM rounds
        WHERE team_id = ? AND role = ?
        ORDER BY week DESC LIMIT 1
    """, (team_id, role))
    data = cursor.fetchone()
    conn.close()
    return data

def obtener_semana_actual(team_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(week) FROM rounds WHERE team_id = ?
    """, (team_id,))
    semana = cursor.fetchone()[0]
    conn.close()
    return semana if semana else 1

def equipo_esta_completo(team_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT role) FROM players WHERE team_id = ?
    """, (team_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count == 4

def equipo_completo_para_semana(team_id, semana):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT role)
        FROM rounds
        WHERE team_id = ? AND week = ?
    """, (team_id, semana))
    conteo = cursor.fetchone()[0]
    conn.close()
    return conteo == 4

def registrar_decision(team_id, role, semana, stock, backorder, pedido_recibido, envio_recibido, pedido_proveedor, envio_cliente):
    conn = conectar_db()
    cursor = conn.cursor()
    round_id = str(uuid.uuid4())
    total_cost = 0
    cursor.execute("""
        INSERT INTO rounds (
            round_id, team_id, week, role,
            stock, backorder, incoming_order, incoming_shipment,
            placed_order, sent_shipment, total_cost
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        round_id, team_id, semana, role,
        stock, backorder, pedido_recibido, envio_recibido,
        pedido_proveedor, envio_cliente, total_cost
    ))
    conn.commit()
    conn.close()

def procesar_avance_semana(team_id, semana_actual):
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, placed_order, sent_shipment, stock, backorder
        FROM rounds
        WHERE team_id = ? AND week = ?
    """, (team_id, semana_actual))
    data = cursor.fetchall()

    decisiones = {row[0]: {
        "pedido": row[1],
        "envio": row[2],
        "stock": row[3],
        "backorder": row[4]
    } for row in data}

    roles = ["Retailer", "Distributor", "Wholesaler", "Factory"]

    for i, rol in enumerate(roles):
        envio_recibido = 0
        if i < len(roles) - 1:
            proveedor = roles[i + 1]
            envio_recibido = decisiones[proveedor]["envio"]
        else:
            envio_recibido = 20  # Producción constante de fábrica

        pedido_recibido = 0
        if i > 0:
            cliente = roles[i - 1]
            pedido_recibido = decisiones[cliente]["pedido"]
        else:
            pedido_recibido = 15  # Demanda del cliente final

        stock_anterior = decisiones[rol]["stock"]
        backorder_anterior = decisiones[rol]["backorder"]
        nuevo_stock = stock_anterior + envio_recibido - decisiones[rol]["envio"]
        nuevo_backorder = max(0, backorder_anterior + pedido_recibido - (stock_anterior + envio_recibido))

        nueva_semana = semana_actual + 1
        nuevo_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO rounds (
                round_id, team_id, week, role,
                stock, backorder, incoming_order, incoming_shipment,
                placed_order, sent_shipment, total_cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nuevo_id, team_id, nueva_semana, rol,
            max(0, nuevo_stock), nuevo_backorder,
            pedido_recibido, envio_recibido,
            0, 0, 0
        ))

    conn.commit()
    conn.close()

# ========================
# INTERFAZ
# ========================
jugadores = obtener_jugadores_por_equipo()
equipos_unicos = list(set((j[0], j[1]) for j in jugadores))

st.subheader("🎯 Paso 1: Selección de jugador")
equipo_nombre = st.selectbox("Selecciona tu equipo", [e[1] for e in equipos_unicos])
nombre_jugador = st.text_input("Tu nombre registrado")
rol = st.selectbox("Selecciona tu rol", ["Retailer", "Distributor", "Wholesaler", "Factory"])
boton_validar = st.button("Validar jugador")

if boton_validar:
    equipo_id = [e[0] for e in equipos_unicos if e[1] == equipo_nombre][0]
    jugador_valido = any(j[0] == equipo_id and j[2].lower() == nombre_jugador.lower() and j[3] == rol for j in jugadores)

    if not jugador_valido:
        st.error("❌ No se encontró tu registro. Verifica tu nombre, equipo y rol.")
        st.stop()

    if not equipo_esta_completo(equipo_id):
        st.warning("⏳ Aún no se han registrado los 4 jugadores. El juego comenzará cuando el equipo esté completo.")
        st.stop()

    semana_actual = obtener_semana_actual(equipo_id)
    if semana_actual > 15:
        st.warning("🏁 El juego ha finalizado. Se completaron las 15 rondas.")
        st.stop()

    st.success(f"✅ Bienvenido {nombre_jugador}, rol: {rol}, equipo: {equipo_nombre}")
    st.header(f"📅 Semana {semana_actual}")

    estado = obtener_estado_actual(equipo_id, rol)
    if estado:
        st.info(f"📦 Stock: {estado[1]} | 🔁 Backorder: {estado[2]} | 📥 Pedido recibido: {estado[3]} | 📦 Envío recibido: {estado[4]}")
    else:
        st.warning("Esta es tu primera semana. No hay historial previo.")
        # Simulación inicial (stock base)
        estado = (semana_actual, 10, 0, 0, 0)

    st.subheader("✍️ Ingresar decisiones de esta semana")
    pedido_proveedor = st.number_input("📤 Pedido al proveedor", min_value=0, step=1)
    envio_cliente = st.number_input("📦 Envío al siguiente jugador", min_value=0, step=1)
    confirmar = st.button("Registrar decisiones")

    if confirmar:
        registrar_decision(
            equipo_id, rol, semana_actual,
            estado[1], estado[2], estado[3], estado[4],
            pedido_proveedor, envio_cliente
        )

        st.success("✅ Decisiones registradas para esta semana.")

        if equipo_completo_para_semana(equipo_id, semana_actual):
            st.success(f"✅ Todos los jugadores han registrado decisiones para la semana {semana_actual}.")
            procesar_avance_semana(equipo_id, semana_actual)
            st.info("🔄 El sistema ha procesado la lógica para la próxima semana.")
        else:
            st.info("⏳ Esperando a que los demás jugadores registren sus decisiones.")
