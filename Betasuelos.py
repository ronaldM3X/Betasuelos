import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Anderson Hernández - Geotecnia", layout="wide", page_icon="🏗️")

# Estilo personalizado para un look más profesional
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2e7d32; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("👨‍🏫 Panel de Control")
# Se eliminó la selección de modos anteriores
st.sidebar.info("Modo activo: **Datos (Laboratorio)**")
st.sidebar.markdown("---")

st.title("🏗️ Anderson Hernández - Geotecnia")

# --- PESTAÑAS ---
tabs = st.tabs(["🧩 Gravimetría & Fases", "📥 Reporte Final"])

# --- PESTAÑA 1: GRAVIMETRÍA ---
with tabs[0]:
    diccionario_maestro = {
        "gs": "Gs (Gravedad específica)", "e": "e (Relación de vacíos)", "n": "n (Porosidad %)",
        "w": "w (Contenido de humedad %)", "s": "S (Grado de saturación %)", "wm": "Wt (Peso total)",
        "ws": "Ws (Peso sólidos)", "ww": "Ww (Peso agua)", "vt": "Vt (Volumen total)",
        "vs": "Vs (Volumen sólidos)", "vv": "Vv (Volumen vacíos)", "vw": "Vw (Volumen agua)",
        "va": "Va (Volumen aire)", "gh": "γ (Unitario húmedo)", "gd": "γd (Unitario seco)"
    }

    st.subheader("📥 1. Entrada de Datos")
    seleccionados = st.multiselect(
        "Selecciona las variables conocidas para iniciar el cálculo:", 
        options=list(diccionario_maestro.keys()), 
        format_func=lambda x: diccionario_maestro[x]
    )
    
    inputs = {}
    cols_in = st.columns(3)
    for i, clave in enumerate(seleccionados):
        inputs[clave] = cols_in[i%3].number_input(f"{diccionario_maestro[clave]}", value=0.0, format="%.4f", key=f"in_{clave}")

    if st.button("🚀 Calcular Propiedades"):
        # Validación de datos mínimos para magnitudes reales
        tiene_peso = any(k in inputs and inputs[k] > 0 for k in ['ws', 'wm', 'ww'])
        tiene_volumen = any(k in inputs and inputs[k] > 0 for k in ['vs', 'vt', 'vv', 'vw', 'va'])
        
        if not (tiene_peso or tiene_volumen):
            st.error("❌ Para este modo es necesario ingresar al menos un dato de **Peso** o **Volumen** real.")
            st.stop()

        d = {k: 0.0 for k in diccionario_maestro.keys()}
        
        # Ajuste de porcentajes
        for k, v in inputs.items():
            d[k] = v / 100 if k in ['w', 'n', 's'] and v > 1.0 else v
        
        # MOTOR DE INFERENCIA (Iterativo para resolver dependencias circulares)
        for _ in range(100):
            # Fase 1: Gs, Ws, Vs
            if d['gs'] > 0 and d['ws'] > 0 and d['vs'] == 0: d['vs'] = d['ws'] / d['gs']
            if d['gs'] > 0 and d['vs'] > 0 and d['ws'] == 0: d['ws'] = d['gs'] * d['vs']
            if d['ws'] > 0 and d['vs'] > 0 and d['gs'] == 0: d['gs'] = d['ws'] / d['vs']

            # Fase 2: Relaciones volumétricas
            if d['vv'] > 0 and d['vs'] > 0 and d['e'] == 0:  d['e'] = d['vv'] / d['vs']
            if d['e']  > 0 and d['vs'] > 0 and d['vv'] == 0: d['vv'] = d['e'] * d['vs']
            
            # Fase 3: Porosidad
            if d['e'] > 0 and d['n'] == 0: d['n'] = d['e'] / (1 + d['e'])
            if 0 < d['n'] < 1 and d['e'] == 0: d['e'] = d['n'] / (1 - d['n'])
            
            # Fase 4: Volúmenes Totales
            if d['vt'] > 0 and d['vs'] > 0 and d['vv'] == 0: d['vv'] = d['vt'] - d['vs']
            if d['vs'] > 0 and d['vv'] > 0 and d['vt'] == 0: d['vt'] = d['vs'] + d['vv']

            # Fase 5: Humedad y Pesos
            if d['ws'] > 0 and d['w']  > 0 and d['ww'] == 0: d['ww'] = d['ws'] * d['w']
            if d['ws'] > 0 and d['ww'] > 0 and d['w']  == 0: d['w']  = d['ww'] / d['ws']
            if d['ww'] > 0 and d['vw'] == 0: d['vw'] = d['ww'] # Densidad agua = 1

            # Fase 6: Saturación
            if d['vw'] > 0 and d['vv'] > 0 and d['s']  == 0: d['s']  = d['vw'] / d['vv']
            if d['s']  > 0 and d['vv'] > 0 and d['vw'] == 0: d['vw'] = d['s']  * d['vv']

            # Fase 7: Pesos Unitarios
            if d['wm'] > 0 and d['vt'] > 0 and d['gh'] == 0: d['gh'] = d['wm'] / d['vt']
            if d['ws'] > 0 and d['vt'] > 0 and d['gd'] == 0: d['gd'] = d['ws'] / d['vt']
            
            # Aire
            if d['vv'] > 0 and d['vw'] > 0: d['va'] = max(0.0, d['vv'] - d['vw'])
            if d['ws'] > 0 and d['ww'] > 0: d['wm'] = d['ws'] + d['ww']

        st.session_state.base_calc = d.copy()
        st.session_state.slider_key = np.random.randint(1, 999)
        st.rerun()

    if 'base_calc' in st.session_state:
        st.markdown("---")
        c_sim, c_res = st.columns([1.2, 1.8])
        bc = st.session_state.base_calc
        sk = st.session_state.slider_key

        with c_sim:
            st.subheader("🕹️ 2. Simulador de Ajuste")
            
            # Valores por defecto para sliders
            e_def = float(bc['e']) if bc['e'] > 0 else 0.6
            w_def = float(bc['w'] * 100) if bc['w'] > 0 else 15.0
            s_def = float(bc['s'] * 100) if bc['s'] > 0 else 50.0
            ws_def = float(bc['ws']) if bc['ws'] > 0 else 100.0
            
            e_val = st.slider("Ajustar e", 0.1, 3.0, e_def, key=f"sl_e_{sk}")
            s_val = st.slider("Ajustar Saturación (S %)", 0.0, 100.0, s_def, key=f"sl_s_{sk}") / 100
            ws_val = st.number_input("Peso Sólidos (Ws) [g]", value=ws_def, key=f"sl_ws_{sk}")
            
            # Recálculo dinámico
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

            if st.button("🔄 Limpiar Todo"):
                del st.session_state.base_calc
                st.rerun()

        with c_res:
            st.subheader("📊 Resultados Finales")
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
            
            # Gráfico de Fases
            fig = go.Figure(data=[
                go.Bar(name='Sólidos', x=['Fases'], y=[f['vs']], marker_color='#7E5109'),
                go.Bar(name='Agua', x=['Fases'], y=[f['vw']], marker_color='#3498DB'),
                go.Bar(name='Aire', x=['Fases'], y=[f['va']], marker_color='#BDC3C7')
            ])
            fig.update_layout(barmode='stack', height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
