import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Anderson Hernández - Geotecnia", layout="wide", page_icon="🏗️")

# FIX VISUAL DEFINITIVO PARA LA TABLA
st.markdown("""
    <style>
    /* Forzamos el contenedor de la tabla a ser blanco con texto negro */
    div[data-testid="stTable"] {
        background-color: white !important;
        border-radius: 10px;
        padding: 10px;
    }
    /* Forzamos a todas las celdas y cabeceras a ser negras */
    div[data-testid="stTable"] table {
        color: #000000 !important;
    }
    div[data-testid="stTable"] th, div[data-testid="stTable"] td {
        color: #000000 !important;
        border-bottom: 1px solid #ddd !important;
    }
    .stButton>button { border-radius: 8px; background-color: #1b5e20; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("👨‍🏫 Panel de Control")
st.sidebar.info("Modo activo: **Datos (Laboratorio)**")

st.title("🏗️ Anderson Hernández - Geotecnia")

# --- LÓGICA DE DATOS ---
diccionario_maestro = {
    "gs": "Gs (Gravedad específica)", "e": "e (Relación de vacíos)", "n": "n (Porosidad %)",
    "w": "w (Contenido de humedad %)", "s": "S (Grado de saturación %)", "wm": "Wt (Peso total)",
    "ws": "Ws (Peso sólidos)", "ww": "Ww (Peso agua)", "vt": "Vt (Volumen total)",
    "vs": "Vs (Volumen sólidos)", "vv": "Vv (Volumen vacíos)", "vw": "Vw (Volumen agua)",
    "va": "Va (Volumen aire)", "gh": "γ (Unitario húmedo)", "gd": "γd (Unitario seco)"
}

st.subheader("📥 1. Entrada de Datos")
seleccionados = st.multiselect("Variables conocidas:", options=list(diccionario_maestro.keys()), format_func=lambda x: diccionario_maestro[x])

inputs = {}
cols_in = st.columns(3)
for i, clave in enumerate(seleccionados):
    inputs[clave] = cols_in[i%3].number_input(f"{diccionario_maestro[clave]}", value=0.0, format="%.4f", key=f"in_{clave}")

if st.button("🚀 Calcular Propiedades"):
    d = {k: 0.0 for k in diccionario_maestro.keys()}
    for k, v in inputs.items():
        d[k] = v / 100 if k in ['w', 'n', 's'] and v > 1.0 else v
    
    # Motor de cálculo
    for _ in range(50):
        if d['gs'] > 0 and d['ws'] > 0 and d['vs'] == 0: d['vs'] = d['ws'] / d['gs']
        if d['gs'] > 0 and d['vs'] > 0 and d['ws'] == 0: d['ws'] = d['gs'] * d['vs']
        if d['vv'] > 0 and d['vs'] > 0 and d['e'] == 0:  d['e'] = d['vv'] / d['vs']
        if d['e'] > 0 and d['n'] == 0: d['n'] = d['e'] / (1 + d['e'])
        if d['vt'] > 0 and d['vs'] > 0 and d['vv'] == 0: d['vv'] = d['vt'] - d['vs']
        if d['vs'] > 0 and d['vv'] > 0 and d['vt'] == 0: d['vt'] = d['vs'] + d['vv']
        if d['ws'] > 0 and d['w'] > 0 and d['ww'] == 0: d['ww'] = d['ws'] * d['w']
        if d['ww'] > 0 and d['vw'] == 0: d['vw'] = d['ww']
        if d['vw'] > 0 and d['vv'] > 0 and d['s'] == 0: d['s'] = d['vw'] / d['vv']

    st.session_state.base_calc = d.copy()
    st.session_state.slider_key = np.random.randint(1, 999)
    st.rerun()

if 'base_calc' in st.session_state:
    st.markdown("---")
    c_sim, c_res = st.columns([1.2, 1.8])
    bc = st.session_state.base_calc
    sk = st.session_state.slider_key

    with c_sim:
        st.subheader("🕹️ 2. Simulador")
        
        # Recuperamos los valores base
        e_def = float(bc['e']) if bc['e'] > 0 else 0.7
        s_def = float(bc['s'] * 100) if bc['s'] > 0 else 50.0
        ws_def = float(bc['ws']) if bc['ws'] > 0 else 100.0
        gs_val = bc['gs'] if bc['gs'] > 0 else 2.65
        
        # SLIDERS (Saturación de vuelta)
        e_val = st.slider("Relación de vacíos (e)", 0.1, 4.0, e_def, key=f"sl_e_{sk}")
        s_val = st.slider("Grado de saturación (S %)", 0.0, 100.0, s_def, key=f"sl_s_{sk}") / 100
        ws_val = st.number_input("Peso de Sólidos (Ws) [g]", value=ws_def, key=f"sl_ws_{sk}")
        
        # RE-CÁLCULO BASADO EN SATURACIÓN
        f = {k: 0.0 for k in diccionario_maestro.keys()}
        f['gs'] = gs_val
        f['e'], f['ws'], f['s'] = e_val, ws_val, s_val
        
        f['vs'] = f['ws'] / f['gs']
        f['vv'] = f['e'] * f['vs']
        f['vw'] = f['s'] * f['vv']
        f['ww'] = f['vw'] # Densidad del agua = 1
        f['w'] = f['ww'] / f['ws'] if f['ws'] > 0 else 0
        f['vt'] = f['vs'] + f['vv']
        f['va'] = max(0.0, f['vv'] - f['vw'])
        f['wm'] = f['ws'] + f['ww']
        f['n'] = f['e'] / (1 + f['e'])

        if st.button("🗑️ Reiniciar"):
            del st.session_state.base_calc
            st.rerun()

    with c_res:
        st.subheader("📊 Resultados")
        gamma_h = (f['wm']/f['vt']) * 9.81 if f['vt'] > 0 else 0
        gamma_d = (f['ws']/f['vt']) * 9.81 if f['vt'] > 0 else 0
        
        res_df = pd.DataFrame({
            "Propiedad": list(diccionario_maestro.values()), 
            "Valor": [
                f"{f['gs']:.3f}", f"{f['e']:.4f}", f"{f['n']*100:.2f}%", 
                f"{f['w']*100:.2f}%", f"{f['s']*100:.2f}%", f"{f['wm']:.2f} g", 
                f"{f['ws']:.2f} g", f"{f['ww']:.2f} g", f"{f['vt']:.2f} cm³", 
                f"{f['vs']:.2f} cm³", f"{f['vv']:.2f} cm³", f"{f['vw']:.2f} cm³", 
                f"{f['va']:.2f} cm³", f"{gamma_h:.2f} kN/m³", f"{gamma_d:.2f} kN/m³"
            ]
        })
        st.table(res_df) # Visualización forzada a ser legible
        
        # Gráfico de Fases
        fig = go.Figure(data=[
            go.Bar(name='Sólidos', x=['Fases'], y=[f['vs']], marker_color='#7E5109'),
            go.Bar(name='Agua', x=['Fases'], y=[f['vw']], marker_color='#3498DB'),
            go.Bar(name='Aire', x=['Fases'], y=[f['va']], marker_color='#BDC3C7')
        ])
        fig.update_layout(barmode='stack', height=300, margin=dict(t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
