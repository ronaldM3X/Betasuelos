import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. CONFIGURACIÓN Y ESTILO VISUAL
st.set_page_config(page_title="Anderson Hernández - Geotecnia", layout="wide", page_icon="🏗️")

st.markdown("""
    <style>
    div[data-testid="stTable"] { 
        background-color: white !important; 
        border-radius: 10px; 
        padding: 10px; 
    }
    div[data-testid="stTable"] table { color: #000000 !important; }
    div[data-testid="stTable"] th, div[data-testid="stTable"] td { 
        color: #000000 !important; 
        border-bottom: 1px solid #ddd !important; 
    }
    .stButton>button { 
        border-radius: 8px; 
        background-color: #1b5e20; 
        color: white; 
        font-weight: bold; 
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏗️ Anderson Hernández - Geotecnia")

# 2. DEFINICIÓN DE VARIABLES (Unidades actualizadas a g/cm3)
diccionario_maestro = {
    "gs": "Gs (Gravedad específica)", "e": "e (Relación de vacíos)", "n": "n (Porosidad %)",
    "w": "w (Contenido de humedad %)", "s": "S (Grado de saturación %)", "wm": "Wt (Peso total g)",
    "ws": "Ws (Peso sólidos g)", "ww": "Ww (Peso agua g)", "vt": "Vt (Volumen total cm³)",
    "vs": "Vs (Volumen sólidos cm³)", "vv": "Vv (Volumen vacíos cm³)", "vw": "Vw (Volumen agua cm³)",
    "va": "Va (Volumen aire cm³)", "gh": "γ (Densidad húmeda g/cm³)", "gd": "γd (Densidad seca g/cm³)"
}

# 3. ENTRADA DE DATOS
st.subheader("📥 1. Entrada de Datos")
seleccionados = st.multiselect(
    "Selecciona las variables conocidas:", 
    options=list(diccionario_maestro.keys()), 
    format_func=lambda x: diccionario_maestro[x]
)

inputs = {}
cols_in = st.columns(3)
for i, clave in enumerate(seleccionados):
    inputs[clave] = cols_in[i%3].number_input(
        f"{diccionario_maestro[clave]}", 
        value=0.0, 
        format="%.4f", 
        key=f"in_{clave}"
    )

# 4. BOTÓN DE CÁLCULO Y MOTOR DE INFERENCIA REFORZADO
if st.button("🚀 Calcular Propiedades"):
    d = {k: 0.0 for k in diccionario_maestro.keys()}
    for k, v in inputs.items():
        if v > 0:
            d[k] = v / 100 if k in ['w', 'n', 's'] and v > 1.0 else v
    
    for _ in range(100):
        # Bloque Pesos
        if d['wm'] > 0 and d['w'] > 0 and d['ws'] == 0: d['ws'] = d['wm'] / (1 + d['w'])
        if d['wm'] > 0 and d['ws'] > 0 and d['w'] == 0: d['w'] = (d['wm'] / d['ws']) - 1
        if d['ws'] > 0 and d['w'] > 0 and d['wm'] == 0: d['wm'] = d['ws'] * (1 + d['w'])
        # Bloque Gs y Volúmenes Sólidos
        if d['gs'] > 0 and d['ws'] > 0 and d['vs'] == 0: d['vs'] = d['ws'] / d['gs']
        if d['gs'] > 0 and d['vs'] > 0 and d['ws'] == 0: d['ws'] = d['gs'] * d['vs']
        if d['ws'] > 0 and d['vs'] > 0 and d['gs'] == 0: d['gs'] = d['ws'] / d['vs']
        # Bloque Agua (Densidad = 1 g/cm3)
        if d['wm'] > 0 and d['ws'] > 0 and d['ww'] == 0: d['ww'] = d['wm'] - d['ws']
        if d['ww'] > 0: d['vw'] = d['ww']
        if d['vw'] > 0: d['ww'] = d['vw']
        # Bloque Volúmenes Totales y Vacíos
        if d['vt'] > 0 and d['vs'] > 0 and d['vv'] == 0: d['vv'] = d['vt'] - d['vs']
        if d['vt'] > 0 and d['vv'] > 0 and d['vs'] == 0: d['vs'] = d['vt'] - d['vv']
        if d['vs'] > 0 and d['vv'] > 0 and d['vt'] == 0: d['vt'] = d['vs'] + d['vv']
        # Relaciones e, n, S
        if d['vv'] > 0 and d['vs'] > 0 and d['e'] == 0:  d['e'] = d['vv'] / d['vs']
        if d['e'] > 0 and d['vs'] > 0 and d['vv'] == 0:  d['vv'] = d['e'] * d['vs']
        if d['e'] > 0 and d['n'] == 0: d['n'] = d['e'] / (1 + d['e'])
        if d['n'] > 0 and d['e'] == 0: d['e'] = d['n'] / (1 - d['n'])
        if d['vw'] > 0 and d['vv'] > 0 and d['s'] == 0: d['s'] = d['vw'] / d['vv']
        if d['s'] > 0 and d['vv'] > 0 and d['vw'] == 0: d['vw'] = d['s'] * d['vv']
        # Aire y Densidades
        if d['vv'] > 0 and d['vw'] > 0: d['va'] = max(0.0, d['vv'] - d['vw'])
        if d['wm'] > 0 and d['vt'] > 0: d['gh'] = d['wm'] / d['vt']
        if d['ws'] > 0 and d['vt'] > 0: d['gd'] = d['ws'] / d['vt']

    if d['e'] == 0 or d['ws'] == 0 or d['gs'] == 0:
        st.warning("⚠️ **Datos insuficientes:** No se puede cerrar el balance. Revisa los datos ingresados.")
    else:
        st.session_state.base_calc = d.copy()
        st.session_state.slider_key = np.random.randint(1, 999)
        st.rerun()

# 5. RESULTADOS Y SIMULADOR
if 'base_calc' in st.session_state:
    st.markdown("---")
    c_sim, c_res = st.columns([1.2, 1.8])
    bc = st.session_state.base_calc
    sk = st.session_state.slider_key

    with c_sim:
        st.subheader("🕹️ 2. Simulador")
        e_val = st.slider("Relación de vacíos (e)", 0.01, 5.0, float(bc['e']), key=f"sl_e_{sk}")
        s_val = st.slider("Grado de saturación (S %)", 0.0, 100.0, float(bc['s']*100), key=f"sl_s_{sk}") / 100
        ws_val = st.number_input("Peso de Sólidos (Ws) [g]", value=float(bc['ws']), key=f"sl_ws_{sk}")
        
        f = {k: 0.0 for k in diccionario_maestro.keys()}
        f['gs'], f['e'], f['ws'], f['s'] = bc['gs'], e_val, ws_val, s_val
        f['vs'] = f['ws'] / f['gs']
        f['vv'] = f['e'] * f['vs']
        f['vw'] = f['s'] * f['vv']
        f['ww'], f['vt'] = f['vw'], f['vs'] + f['vv']
        f['va'], f['wm'] = max(0.0, f['vv'] - f['vw']), f['ws'] + f['ww']
        f['w'], f['n'] = (f['ww'] / f['ws'] if f['ws'] > 0 else 0), f['e'] / (1 + f['e'])
        f['gh'], f['gd'] = (f['wm'] / f['vt'] if f['vt'] > 0 else 0), (f['ws'] / f['vt'] if f['vt'] > 0 else 0)

        if st.button("🗑️ Reiniciar"):
            del st.session_state.base_calc
            st.rerun()

    with c_res:
        st.subheader("📊 Resultados")
        res_df = pd.DataFrame({
            "Propiedad": list(diccionario_maestro.values()), 
            "Valor": [
                f"{f['gs']:.3f}", f"{f['e']:.4f}", f"{f['n']*100:.2f}%", 
                f"{f['w']*100:.2f}%", f"{f['s']*100:.2f}%", f"{f['wm']:.2f} g", 
                f"{f['ws']:.2f} g", f"{f['ww']:.2f} g", f"{f['vt']:.2f} cm³", 
                f"{f['vs']:.2f} cm³", f"{f['vv']:.2f} cm³", f"{f['vw']:.2f} cm³", 
                f"{f['va']:.2f} cm³", f"{f['gh']:.3f} g/cm³", f"{f['gd']:.3f} g/cm³"
            ]
        })
        st.table(res_df)
        
        fig = go.Figure(data=[
            go.Bar(name='Sólidos', x=['Fases'], y=[f['vs']], marker_color='#7E5109'),
            go.Bar(name='Agua', x=['Fases'], y=[f['vw']], marker_color='#3498DB'),
            go.Bar(name='Aire', x=['Fases'], y=[f['va']], marker_color='#BDC3C7')
        ])
        fig.update_layout(barmode='stack', height=300, margin=dict(t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
