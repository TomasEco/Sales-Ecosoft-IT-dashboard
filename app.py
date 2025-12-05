import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Sales Dashboard Executive", layout="wide", page_icon="📊")

# --- STILE CSS PERSONALIZZATO ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stApp {
        background-color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI CARICAMENTO DATI ---
@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        # Legge i fogli dal file Excel caricato
        try:
            df_turnover = pd.read_excel(uploaded_file, sheet_name='Source_Turnover')
            df_portfolio = pd.read_excel(uploaded_file, sheet_name='Source_Portfolio')
            return df_turnover, df_portfolio
        except Exception as e:
            st.error(f"Errore nella lettura del file: {e}. Assicurati di usare il file Excel corretto.")
            return None, None
    else:
        return None, None

# --- SIDEBAR (INPUT UTENTE) ---
st.sidebar.header("⚙️ Impostazioni")
st.sidebar.write("Carica il file Excel aggiornato per rinfrescare i dati.")

uploaded_file = st.sidebar.file_uploader("Carica Excel (Executive_Sales_Dashboard.xlsx)", type=["xlsx"])

# Input Budget Annuale
budget_annuale = st.sidebar.number_input("Inserisci Budget Annuale (€)", min_value=0, value=2500000, step=50000)

st.sidebar.markdown("---")
st.sidebar.info("Dashboard creata con Streamlit. Carica il file Excel generato per vedere i tuoi dati aggiornati.")

# --- LOGICA PRINCIPALE ---

# 1. Recupero Dati (o mock data se vuoto)
df_turnover, df_portfolio = load_data(uploaded_file)

if df_turnover is None:
    st.warning("⚠️ In attesa di file. Carico dati di esempio per la visualizzazione.")
    # Dati fittizi per demo
    turnover_val = 1530000
    portfolio_val = 450000
    # Creiamo un df fittizio per i grafici
    months = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
    values = np.random.randint(50000, 200000, 11)
    values = np.append(values, 0) # Dicembre a 0
    df_chart = pd.DataFrame({'Mese': months, 'Fatturato': values})
else:
    # Calcolo dai file reali
    turnover_val = df_turnover['Turnover'].sum()
    portfolio_val = df_portfolio['Net amount'].sum()
    
    # Poiché non abbiamo date reali nei CSV originali, simuliamo la distribuzione mensile
    # (NOTA: In produzione, il file Excel dovrebbe avere una colonna 'Data')
    months = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
    # Distribuiamo il fatturato reale sui primi 11 mesi simulati
    np.random.seed(42) 
    weights = np.random.rand(11)
    weights = weights / weights.sum()
    monthly_vals = weights * turnover_val
    monthly_vals = np.append(monthly_vals, 0) # Dicembre 0
    
    df_chart = pd.DataFrame({'Mese': months, 'Fatturato': monthly_vals})

# 2. Calcoli KPI
total_forecast = turnover_val + portfolio_val
budget_mensile = budget_annuale / 12
delta_budget = total_forecast - budget_annuale

# --- LAYOUT DASHBOARD ---

st.title("📊 Executive Sales Dashboard")
st.markdown("Panoramica dell'andamento vendite, portafoglio ordini e scostamento budget.")

# ROW 1: KPI CARDS
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Fatturato Invoiced (YTD)", value=f"€ {turnover_val:,.0f}", delta="Reale")
with col2:
    st.metric(label="Portafoglio Ordini", value=f"€ {portfolio_val:,.0f}", delta="Backlog", delta_color="off")
with col3:
    st.metric(label="Stima Fine Anno", value=f"€ {total_forecast:,.0f}", delta=f"{((total_forecast/budget_annuale)-1)*100:.1f}% vs Budget")
with col4:
    st.metric(label="Target Budget", value=f"€ {budget_annuale:,.0f}")

st.markdown("---")

# ROW 2: GRAFICI PRINCIPALI
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Andamento Fatturato vs Budget")
    
    # Preparazione dati grafico
    df_chart['Budget'] = budget_mensile
    df_chart['Cumulativo_Fatturato'] = df_chart['Fatturato'].cumsum()
    df_chart['Cumulativo_Budget'] = df_chart['Budget'].cumsum()
    
    # Grafico Combinato
    fig = go.Figure()
    
    # Barre Fatturato
    fig.add_trace(go.Bar(
        x=df_chart['Mese'], 
        y=df_chart['Fatturato'], 
        name='Fatturato Mensile',
        marker_color='#4472C4'
    ))
    
    # Linea Budget
    fig.add_trace(go.Scatter(
        x=df_chart['Mese'], 
        y=df_chart['Budget'], 
        name='Target Mensile',
        line=dict(color='#ED7D31', width=3)
    ))

    # Aggiunta Portafoglio su Dicembre (simulato)
    fig.add_trace(go.Bar(
        x=['Dic'],
        y=[portfolio_val],
        name='Portafoglio (Previsto)',
        marker_color='#70AD47',
        opacity=0.7
    ))
    
    fig.update_layout(barmode='overlay', height=400, template="plotly_white", 
                      legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Composizione Business")
    
    labels = ['Fatturato', 'Portafoglio']
    values = [turnover_val, portfolio_val]
    
    fig_pie = px.donut(names=labels, values=values, hole=0.5, 
                       color_discrete_sequence=['#4472C4', '#70AD47'])
    fig_pie.update_layout(height=400, showlegend=True, 
                          annotations=[dict(text=f'Totale\n€ {(turnover_val+portfolio_val)/1000000:.1f}M', x=0.5, y=0.5, font_size=20, showarrow=False)])
    st.plotly_chart(fig_pie, use_container_width=True)

# ROW 3: DETTAGLIO CLIENTI (Se dati caricati)
if df_turnover is not None:
    st.subheader("Top 10 Clienti per Performance")
    
    # Aggregazione dati
    cust_sales = df_turnover.groupby('Customer')[['Turnover', 'Margin']].sum().reset_index()
    cust_portfolio = df_portfolio.groupby('Customer')[['Net amount']].sum().rename(columns={'Net amount': 'Portfolio'}).reset_index()
    
    merged = pd.merge(cust_sales, cust_portfolio, on='Customer', how='outer').fillna(0)
    merged['Totale'] = merged['Turnover'] + merged['Portfolio']
    top_10 = merged.sort_values('Totale', ascending=False).head(10)
    
    fig_bar = px.bar(top_10, x='Customer', y=['Turnover', 'Portfolio'], 
                     title="Fatturato vs Portafoglio per Top Clienti",
                     labels={'value': 'Valore (€)', 'variable': 'Tipo'},
                     color_discrete_map={'Turnover': '#4472C4', 'Portfolio': '#70AD47'})
    
    st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("Visualizza tabella dati grezzi"):
        st.dataframe(merged)