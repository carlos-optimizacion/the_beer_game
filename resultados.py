import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Resultados por Equipo - Beer Game", layout="wide")
st.title("📊 Resultados por Equipo - The Beer Game")

# ========================
# FUNCIONES DE BASE DE DATOS
# ========================
def conectar_db():
    return sqlite3.connect("beer_game.db")

def cargar_equipos():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT t.team_id, t.team_name FROM teams t")
    equipos = cursor.fetchall()
    conn.close()
    return equipos

def obtener_datos_jugador(team_id, role):
    conn = conectar_db()
    query = """
        SELECT week, stock, backorder, incoming_order, incoming_shipment,
               placed_order, sent_shipment
        FROM rounds
        WHERE team_id = ? AND role = ?
        ORDER BY week
    """
    df = pd.read_sql_query(query, conn, params=(team_id, role))
    conn.close()
    return df

def calcular_kpis(df, holding_cost=1, backorder_cost=2):
    df["inventory_cost"] = df["stock"] * holding_cost
    df["backorder_cost"] = df["backorder"] * backorder_cost
    df["total_cost"] = df["inventory_cost"] + df["backorder_cost"]

    pedidos = df["incoming_order"].sum()
    pedidos_atendidos = (df["incoming_order"] - df["backorder"]).clip(lower=0).sum()
    nivel_servicio = (pedidos_atendidos / pedidos * 100) if pedidos > 0 else 100

    return {
        "Costo Total": round(df["total_cost"].sum(), 2),
        "Costo Inventario": round(df["inventory_cost"].sum(), 2),
        "Costo Faltantes": round(df["backorder_cost"].sum(), 2),
        "Stock Promedio": round(df["stock"].mean(), 2),
        "Backorder Promedio": round(df["backorder"].mean(), 2),
        "Nivel de Servicio (%)": round(nivel_servicio, 2)
    }

def graficar_jugador(df, rol):
    fig, ax = plt.subplots()
    ax.plot(df["week"], df["stock"], marker='o', label="Stock")
    ax.plot(df["week"], df["backorder"], marker='x', label="Backorder")
    ax.set_title(f"{rol} - Evolución Stock / Backorder")
    ax.set_xlabel("Semana")
    ax.set_ylabel("Unidades")
    ax.legend()
    st.pyplot(fig)

# ========================
# INTERFAZ PRINCIPAL
# ========================
equipos = cargar_equipos()
equipo_nombre = st.selectbox("Selecciona un equipo", [e[1] for e in equipos])
equipo_id = [e[0] for e in equipos if e[1] == equipo_nombre][0]

roles = ["Retailer", "Distributor", "Wholesaler", "Factory"]
datos_equipo = {}
kpis_equipo = []

st.markdown("## 🔍 Análisis por Jugador")
tabs = st.tabs(roles)

for i, rol in enumerate(roles):
    df = obtener_datos_jugador(equipo_id, rol)
    datos_equipo[rol] = df
    with tabs[i]:
        if df.empty:
            st.warning(f"No hay datos para el rol {rol}.")
        else:
            graficar_jugador(df, rol)
            kpis = calcular_kpis(df)
            for k, v in kpis.items():
                st.metric(label=k, value=v)
            kpis["Rol"] = rol
            kpis_equipo.append(kpis)

# ========================
# COMPARATIVA DE LOS 4 ROLES
# ========================
st.markdown("---")
st.subheader("📊 Comparativa de los 4 jugadores")
if kpis_equipo:
    df_comp = pd.DataFrame(kpis_equipo)
    df_comp = df_comp.set_index("Rol")
    st.dataframe(df_comp.style.format("{:.2f}"))

# ========================
# GRÁFICO EFECTO BULLWHIP
# ========================
st.subheader("📈 Efecto Látigo (Bullwhip Effect)")
stds = []
for rol in roles:
    df = datos_equipo.get(rol, pd.DataFrame())
    if not df.empty:
        stds.append(df["placed_order"].std())
    else:
        stds.append(0)

fig2, ax2 = plt.subplots()
ax2.plot(roles, stds, marker='o')
ax2.set_title("Desviación Estándar de Pedidos por Rol")
ax2.set_ylabel("STD Pedidos")
ax2.set_xlabel("Rol")
st.pyplot(fig2)

# ========================
# TOTALES DEL EQUIPO
# ========================
st.subheader("📦 Totales del equipo")
if kpis_equipo:
    total_cost = sum(k["Costo Total"] for k in kpis_equipo)
    prom_servicio = sum(k["Nivel de Servicio (%)"] for k in kpis_equipo) / 4
    st.metric("Costo Total del Equipo", f"S/ {round(total_cost,2)}")
    st.metric("Nivel de Servicio Promedio", f"{round(prom_servicio,2)} %")
