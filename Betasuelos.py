import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Anderson Hernández - Geotecnia", layout="wide", page_icon="🏗️")

# Estilo para mejorar la visualización
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 8px; background-color: #1b5e20; color: white; font-weight: bold; }
    .stTable { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("👨‍🏫 Panel de Control")
st.sidebar.info("Modo activo: **Datos (Laboratorio)**")
st.sidebar.markdown("---")
st.sidebar.write("Esta herramienta calcula las relaciones de fase a partir de datos conocidos.")

st.title("🏗️ Anderson Hernández - Geotecnia")

# --- CONTENIDO PRINCIPAL (SIN PESTAÑAS) ---
diccionario_maestro = {
    "gs": "Gs (Gravedad específica)", "e": "e (Relación de vacíos)", "n": "n (Porosidad %)",
    "w": "w (Contenido de humedad %)", "s": "S (Grado de saturación %)", "wm": "Wt (Peso total)",
    "ws": "Ws (Peso sólidos)", "ww": "Ww (Peso agua)", "vt": "Vt (Volumen total)",
    "vs": "Vs (Volumen sólidos)", "vv": "Vv (Volumen vacíos)", "vw": "Vw (Volumen agua)",
    "va": "Va (Volumen aire)", "gh": "γ (Unitario húmedo)", "gd": "γd (Unitario seco)"
}

st.subheader("📥 1. Entrada de Datos")
seleccionados = st.multiselect(
    "Selecciona las variables conocidas:", 
    options=list(diccionario_maestro.keys()), 
    format_func=lambda x: diccionario_maestro[x]
)

inputs = {}
cols_in = st.columns(3)
for i, clave in enumerate(seleccionados):
    inputs[clave] = cols_in[i%3].number_input(f"{diccionario_maestro[clave]}", value=0.0, format="%.4f", key=f"in_{clave}")

if st.button("🚀 Calcular Propiedades"):
    # Verificación de datos de magnitud real
    tiene_peso = any(k in inputs and inputs[k] > 0 for k in ['ws', 'wm', 'ww'])
    tiene_volumen = any(k in inputs and inputs[k] > 0 for k in ['vs', 'vt', 'vv', 'vw', 'va'])
    
    if not (tiene_peso or tiene_volumen):
        st.error("❌ ¡Ojo! Necesito al menos un Peso o un Volumen real para procesar los datos de laboratorio.")
        st.stop()

    d = {k: 0.0 for k in diccionario_maestro.keys()}
    for k, v in inputs.items():
        d[k] = v / 100 if k in ['w', 'n', 's'] and v > 1.0 else v
    
    # MOTOR DE INFERENCIA
    for _ in range(100):
        if d['gs'] > 0 and d['ws'] > 0 and d['vs'] == 0: d['vs'] = d['ws'] / d['gs']
        if d['gs'] > 0 and d['vs'] > 0 and d['ws'] == 0: d['ws'] = d['gs'] * d['vs']
        if d['ws'] > 0 and d['vs'] > 0 and d['gs'] == 0: d['gs'] = d['ws'] / d['vs']
        if d['vv'] > 0 and d['vs'] > 0 and d['e'] == 0:  d['e'] = d['vv'] / d['vs']
        if d['e']  > 0 and d['vs'] > 0 and d['vv'] == 0: d['vv'] = d['e'] * d['vs']
        if d['e'] > 0 and d['n'] == 0: d['n'] = d['e'] / (1 + d['e'])
        if 0 < d['n'] < 1 and d['e'] == 0: d['e'] = d['n'] / (1 - d['n'])
        if d['vt'] > 0 and d['vs'] > 0 and d['vv'] == 0: d['vv'] = d['vt'] - d['vs']
        if d['vs'] > 0 and d['vv'] > 0 and d['vt'] == 0: d['vt'] = d['vs'] + d['vv']
        if d['ws'] > 0 and d['w']  > 0 and d['ww'] == 0: d['ww'] = d['ws'] * d['w']
        if d['ws'] > 0 and d['ww'] > 0 and d['w']  == 0: d['w']  = d['ww'] / d['ws']
        if d['ww'] > 0 and d['vw'] == 0: d['vw'] = d['ww']
        if d['vw'] > 0 and d['vv'] > 0 and d['s']  == 0: d['s']  = d['vw'] / d['vv']
        if d['s']  > 0 and d['vv'] > 0 and d['vw'] == 0: d['vw'] = d['s']  * d['vv']
        if d['wm'] > 0 and d['vt'] > 0 and d['gh'] == 0: d['gh'] = d['wm'] / d['vt']
        if d['ws'] > 0 and d['vt'] > 0 and d['gd'] == 0: d['gd'] = d['ws'] / d['vt']
        if d['vv'] > 0 and d['vw'] > 0: d['va'] = max(0.0, d['vv'] - d['vw'])
        if d['ws'] > 0 and d['ww'] > 0: d['wm'] = d['ws'] + d['ww']

    st.session_state.base_calc = d.copy()
    st.session_state.slider_key = np.random.randint(1, 999)
    st.rerun()

# --- ÁREA DE RESULTADOS ---
if 'base_calc' in st.session_state:
    st.markdown("---")
    c_sim, c_res = st.columns([1.2, 1.8])
    bc = st.session_state.base_calc
    sk = st.session_state.slider_key

    with c_sim:
        st.subheader("🕹️ 2. Simulador")
        
        # Sliders basados en el cálculo inicial
        e_def = float(bc['e']) if bc['e'] > 0 else 0.700
        w_def = float(bc['w'] * 100) if bc['w'] > 0 else 20.0
        s_def = float(bc['s'] * 100) if bc['s'] > 0 else 60.0
        ws_def = float(bc['ws']) if bc['ws'] > 0 else 100.0
        
        e_val = st.slider("Ajustar Relación de vacíos (e)", 0.1, 4.0, e_def, key=f"sl_e_{sk}")
        s_val = st.slider("Ajustar Saturación (S %)", 0.0, 100.0, s_def, key=f"sl_s_{sk}") / 100
        ws_val = st.number_input("Peso de Sólidos (Ws) [g]", value=ws_def, key=f"sl_ws_{sk}")
        
        # Recálculo instantáneo
        f = {k: 0.0 for k in diccionario_maestro.keys()}
        f['gs'] = bc['gs'] if bc['gs'] > 0 else 2.65
        f['e'], f['ws'] = e_val, ws_val
        f['vs'] = f['ws'] / f['gs']
        f['vv'] = f['e'] * f['vs']
        f['s'] = s_val
        f['vw'] = f['s'] * f['vv']
        f['ww'] = f['vw']
        f['w'] = f['ww'] / f['ws'] if f['ws'] > 0 else 0
        f['vt'] = f['vs'] + f['vv']
        f['va'] = max(0.0, f['vv'] - f['vw'])
        f['wm'] = f['ws'] + f['ww']
        f['n'] = f['vv'] / f['vt']

        if st.button("🗑️ Reiniciar Pantalla"):
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
        st.table(res_df)
        
        fig = go.Figure(data=[
            go.Bar(name='Sólidos', x=['Fases'], y=[f['vs']], marker_color='#7E5109'),
            go.Bar(name='Agua', x=['Fases'], y=[f['vw']], marker_color='#3498DB'),
            go.Bar(name='Aire', x=['Fases'], y=[f['va']], marker_color='#BDC3C7')
        ])
        fig.update_layout(barmode='stack', height=350, margin=dict(t=0, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)
        
