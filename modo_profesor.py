import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Modo Profesor - Beer Game", layout="wide")
st.title("👨‍🏫 Modo Profesor - Resultados Globales")

# Contraseña para acceder
clave_correcta = "F@brizzio01"
clave_ingresada = st.sidebar.text_input("🔐 Ingrese clave de profesor", type="password")

if clave_ingresada != clave_correcta:
    st.warning("⚠️ Acceso restringido. Por favor ingrese la clave correcta.")
    st.stop()

# Conexión a base de datos
def conectar_db():
    return sqlite3.connect("beer_game.db")

# Reiniciar juego
def reiniciar_juego():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rounds")
    cursor.execute("DELETE FROM players")
    conn.commit()
    conn.close()

# Botón de reinicio
if st.sidebar.button("🔄 Reiniciar Juego"):
    reiniciar_juego()
    st.sidebar.success("✅ Juego reiniciado correctamente.")

# Cargar todos los equipos
def cargar_equipos():
    conn = conectar_db()
    query = "SELECT team_id, team_name FROM teams"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Obtener datos por equipo
def obtener_datos_equipo(team_id):
    conn = conectar_db()
    query = """
        SELECT week, role, stock, backorder, incoming_order, placed_order
        FROM rounds
        WHERE team_id = ?
    """
    df = pd.read_sql_query(query, conn, params=(team_id,))
    conn.close()
    return df

# Calcular KPIs por equipo
def calcular_kpis_equipo(df):
    holding_cost, backorder_cost = 1, 2
    df["inventory_cost"] = df["stock"] * holding_cost
    df["backorder_cost"] = df["backorder"] * backorder_cost
    df["total_cost"] = df["inventory_cost"] + df["backorder_cost"]

    pedidos = df["incoming_order"].sum()
    atendidos = (df["incoming_order"] - df["backorder"]).clip(lower=0).sum()
    nivel_servicio = (atendidos / pedidos * 100) if pedidos > 0 else 100

    return {
        "Costo Total": df["total_cost"].sum(),
        "Nivel Servicio (%)": nivel_servicio
    }

# Exportar datos a Excel
def exportar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    processed_data = output.getvalue()
    return processed_data

# Interfaz
st.subheader("📋 Tabla comparativa entre equipos")
equipos = cargar_equipos()
tabla_resumen = []

for _, row in equipos.iterrows():
    df_equipo = obtener_datos_equipo(row["team_id"])
    if not df_equipo.empty:
        kpis = calcular_kpis_equipo(df_equipo)
        tabla_resumen.append({
            "Equipo": row["team_name"],
            "Costo Total": round(kpis["Costo Total"], 2),
            "Nivel Servicio (%)": round(kpis["Nivel Servicio (%)"], 2)
        })

if tabla_resumen:
    df_resumen = pd.DataFrame(tabla_resumen)
    df_resumen = df_resumen.sort_values(by="Costo Total")
    df_resumen["Ranking"] = range(1, len(df_resumen) + 1)
    st.dataframe(df_resumen.set_index("Ranking"))

    # Exportar Excel
    excel_data = exportar_excel(df_resumen)
    st.download_button(
        label="📥 Descargar Resultados en Excel",
        data=excel_data,
        file_name="resultados_beer_game.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Gráfico del efecto látigo global
    st.subheader("📈 Gráfico del Efecto Látigo Global")
    fig, ax = plt.subplots(figsize=(8,4))

    for _, row in equipos.iterrows():
        df_equipo = obtener_datos_equipo(row["team_id"])
        if not df_equipo.empty:
            std_pedidos = df_equipo.groupby("role")["placed_order"].std().reindex(["Retailer", "Distributor", "Wholesaler", "Factory"])
            ax.plot(std_pedidos.index, std_pedidos.values, marker='o', label=row["team_name"])

    ax.set_title("Efecto Látigo Global - Desviación STD de Pedidos")
    ax.set_xlabel("Rol")
    ax.set_ylabel("STD de Pedidos")
    ax.legend(title="Equipos")
    st.pyplot(fig)
else:
    st.warning("No hay suficientes datos para mostrar.")
