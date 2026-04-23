import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.graph_objects as go
import yaml
from yaml.loader import SafeLoader
import io
import requests

# ─────────────────────────────────────────────
# CONFIG PAGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Maori - Vesper",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f5f7fa; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0d1b2a 0%, #1a3a5c 100%); }
    [data-testid="stSidebar"] * { color: #e8f0fe !important; }
    .kpi-card { background: white; border-radius: 16px; padding: 24px 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07); border-left: 5px solid #1a3a5c; margin-bottom: 8px; }
    .kpi-card.green  { border-left-color: #2ecc71; }
    .kpi-card.orange { border-left-color: #e67e22; }
    .kpi-card.red    { border-left-color: #e74c3c; }
    .kpi-card.blue   { border-left-color: #1a3a5c; }
    .kpi-label { font-size: 12px; font-weight: 600; color: #8899aa; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #0d1b2a; }
    .kpi-sub   { font-size: 12px; color: #aabbcc; margin-top: 4px; }
    .section-title { font-size: 18px; font-weight: 700; color: #0d1b2a;
        margin: 24px 0 12px 0; border-bottom: 2px solid #e0e8f0; padding-bottom: 6px; }
    .badge-completata     { background:#d4edda; color:#155724; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-in-lavorazione { background:#fff3cd; color:#856404; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-ko             { background:#f8d7da; color:#721c24; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    div[data-testid="stForm"] { background: white; border-radius: 16px; padding: 32px; 
        box-shadow: 0 4px 24px rgba(0,0,0,0.10); max-width: 420px; margin: 80px auto; }

    /* Sidebar buttons */
    [data-testid="stSidebar"] .stButton > button {
        background-color: rgba(255,255,255,0.08) !important;
        color: #e8f0fe !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255,255,255,0.18) !important;
        border-color: rgba(255,255,255,0.4) !important;
        color: white !important;
    }
    /* Sidebar logout button */
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background-color: rgba(231,76,60,0.2) !important;
        border-color: rgba(231,76,60,0.4) !important;
        color: #ffaaaa !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background-color: rgba(231,76,60,0.4) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

col_login, col_mid, col_right = st.columns([1, 1, 1])
with col_mid:
    st.markdown("""
    <div style="text-align:center; padding: 40px 0 10px 0;">
        <div style="font-size:52px;">⚡</div>
        <div style="font-size:24px; font-weight:700; color:#0d1b2a; margin-top:8px;">MAORI - VESPER</div>
        <div style="font-size:13px; color:#8899aa; letter-spacing:2px; margin-bottom:24px;">LAVORAZIONI VESPER PER MAORI</div>
    </div>
    """, unsafe_allow_html=True)

authenticator.login(location='main')

if st.session_state.get("authentication_status") is False:
    st.error("❌ Username o password non corretti")
    st.stop()
elif st.session_state.get("authentication_status") is None:
    st.stop()

# ─────────────────────────────────────────────
# UTENTE AUTENTICATO — DA QUI IN POI
# ─────────────────────────────────────────────
name     = st.session_state.get("name", "")
username = st.session_state.get("username", "")
role     = config['credentials']['usernames'].get(username, {}).get('role', 'viewer')

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
SHEET_ID = "1lnaDVhHFEZVGcCKEq2oq6usAbdI18wyJ-G2yQbfiSTQ"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

MONTHLY_SHEETS = [
    '09-24','10-24','11-24','12-24',
    '01-25','02-25','03-25','04-25','05-25','06-25','07-25','08-25','09-25','10-25','11-25','12-25',
    '01-26','02-26','03-26'
]
MONTH_LABELS = {
    '09-24':'Set 2024','10-24':'Ott 2024','11-24':'Nov 2024','12-24':'Dic 2024',
    '01-25':'Gen 2025','02-25':'Feb 2025','03-25':'Mar 2025','04-25':'Apr 2025',
    '05-25':'Mag 2025','06-25':'Giu 2025','07-25':'Lug 2025','08-25':'Ago 2025',
    '09-25':'Set 2025','10-25':'Ott 2025','11-25':'Nov 2025','12-25':'Dic 2025',
    '01-26':'Gen 2026','02-26':'Feb 2026','03-26':'Mar 2026',
}
COLORS = {
    'primary':   '#1a3a5c',
    'secondary': '#2471a3',
    'accent':    '#3498db',
    'green':     '#2ecc71',
    'orange':    '#e67e22',
    'red':       '#e74c3c',
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt_eur(val):
    if val is None:
        return "–"
    try:
        v = float(val)
        if pd.isna(v):
            return "–"
        return "€ {:,.2f}".format(v).replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "–"

def kpi_card(label, value, sub="", color="blue"):
    st.markdown(f"""
    <div class="kpi-card {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def badge(stato):
    s = str(stato).strip().upper()
    if s == "COMPLETATA":
        return '<span class="badge-completata">✅ Completata</span>'
    elif s == "IN LAVORAZIONE":
        return '<span class="badge-in-lavorazione">🔧 In Lavorazione</span>'
    elif s == "K.O.":
        return '<span class="badge-ko">❌ K.O.</span>'
    return f'<span>{stato}</span>'

# ─────────────────────────────────────────────
# LOAD DATA DA GOOGLE SHEETS
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_all_data():
    response = requests.get(SHEET_URL)
    response.raise_for_status()
    xl = pd.ExcelFile(io.BytesIO(response.content))

    monthly = {}
    for sheet in MONTHLY_SHEETS:
        if sheet not in xl.sheet_names:
            continue
        df = xl.parse(sheet, header=None)
        totale = None
        for col in [9, 8]:
            if df.shape[1] > col:
                val = df.iloc[1, col]
                if pd.notna(val) and isinstance(val, (int, float)):
                    totale = float(val)
                    break

        lavorazioni = []
        for i in range(2, len(df)):
            raw = df.iloc[i, 1]
            if pd.isna(raw):
                continue
            desc = str(raw).strip()
            if not desc or desc == "Lead:":
                continue

            n_lav   = df.iloc[i, 4] if df.shape[1] > 4 else None
            importo = df.iloc[i, 5] if df.shape[1] > 5 else None
            da_fatt = df.iloc[i, 6] if df.shape[1] > 6 else None

            leads = []
            sep = "\n"
            if sep in desc:
                parts = desc.split(sep)
                desc_clean = parts[0].strip()
                for part in parts[1:]:
                    p = part.strip()
                    if p and "_" in p:
                        leads.append(p)
            else:
                desc_clean = desc
                if i + 1 < len(df):
                    nxt = df.iloc[i+1, 1]
                    if pd.notna(nxt):
                        nxt_str = str(nxt)
                        if nxt_str.startswith("Lead"):
                            for part in nxt_str.replace("Lead", "").split(sep):
                                p = part.strip()
                                if p and "_" in p:
                                    leads.append(p)

            try:
                da_fatt_val = float(str(da_fatt).replace("€","").replace("-","").strip()) if pd.notna(da_fatt) else None
            except:
                da_fatt_val = None
            try:
                n_lav_val = int(float(str(n_lav))) if pd.notna(n_lav) else None
            except:
                n_lav_val = None
            try:
                importo_val = float(str(importo)) if pd.notna(importo) else None
            except:
                importo_val = None

            lavorazioni.append({
                'descrizione': desc_clean,
                'n_lavorazioni': n_lav_val,
                'importo_unitario': importo_val,
                'da_fatturare': da_fatt_val,
                'leads': leads,
                'mese': sheet,
            })
        monthly[sheet] = {'totale': totale, 'lavorazioni': lavorazioni}

    df_vista = xl.parse('Vista Per ID UFFICIO TECNICO', header=0)
    df_vista = df_vista.dropna(subset=['Tutti gli id'])
    df_vista['Tutti gli id'] = df_vista['Tutti gli id'].astype(int)
    df_vista.columns = df_vista.columns.str.strip()

    df_lista = xl.parse('Lista ID', header=0)
    cols_lista = ['Mese','Lavorazione','Id','Cliente','Inizio attività','Fine attività','Importo lavorazione']
    df_lista = df_lista[cols_lista].dropna(subset=['Id'])
    df_lista['Id'] = df_lista['Id'].astype(int)

    df_fatture = xl.parse('DETTAGLIO FATTURE IREN', header=0)
    df_fatture = df_fatture.dropna(subset=['PAGATO'])

    df_det_iren = xl.parse('DETTAGLIO ID IREN', header=0)
    df_det_iren = df_det_iren.dropna(subset=['ID'])
    df_det_iren['ID'] = df_det_iren['ID'].astype(int)

    df_listino_vesper = xl.parse('listino vesper', header=None)
    df_listino_iren   = xl.parse('listino iren',   header=None)
    return monthly, df_vista, df_lista, df_fatture, df_det_iren, df_listino_vesper, df_listino_iren

try:
    monthly, df_vista, df_lista, df_fatture, df_det_iren, df_listino_vesper, df_listino_iren = load_all_data()
except Exception as e:
    st.error(f"❌ Errore nel caricamento dati da Google Sheets: {e}")
    st.stop()

# ─────────────────────────────────────────────
# GLOBAL CALCS
# ─────────────────────────────────────────────
df_monthly_totals = pd.DataFrame([
    {'sheet': s, 'label': MONTH_LABELS[s], 'totale': monthly.get(s, {}).get('totale') or 0,
     'anno': '20' + s.split('-')[1]}
    for s in MONTHLY_SHEETS if s in monthly
])

totale_generale     = df_monthly_totals['totale'].sum()
n_pratiche_totali   = len(df_vista)
n_completate        = len(df_vista[df_vista['Lavoro Ultimato Avanzamento'] == 'COMPLETATA'])
n_in_lav            = len(df_vista[df_vista['Lavoro Ultimato Avanzamento'] == 'IN LAVORAZIONE'])
n_ko                = len(df_vista[df_vista['Lavoro Ultimato Avanzamento'] == 'K.O.'])
totale_iren_pagato  = pd.to_numeric(df_vista['Iren'], errors='coerce').sum()
totale_ricavi_maori = pd.to_numeric(df_vista['Ricavo Maori'], errors='coerce').sum()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:42px;">⚡</div>
        <div style="font-size:18px; font-weight:700; color:#e8f0fe; margin-top:6px;">MAORI - VESPER</div>

    </div>
    <hr style="border-color:#2a4a6a; margin:10px 0 16px 0;">
    <div style="font-size:12px; color:#90b8d8; text-align:center; margin-bottom:16px;">
        👤 {name}<br>
        <span style="font-size:10px; color:#4a7a9a;">{'🔑 Amministratore' if role == 'admin' else '👁 Viewer'}</span>
    </div>
    """, unsafe_allow_html=True)

    nav = st.radio(
        "Navigazione",
        ["📊 Dashboard", "📅 Vista Mensile", "🔍 Ricerca Pratiche", "💶 Finanziario", "📋 Listino Vesper", "📋 Listino IREN"],
        label_visibility="collapsed"
    )

    st.markdown('<hr style="border-color:#2a4a6a; margin-top:20px;">', unsafe_allow_html=True)

    if st.button("🔄 Aggiorna Dati", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    authenticator.logout("🚪 Logout", location="sidebar")

    st.markdown('''<div style="text-align:center; padding-top:10px;">
        <div style="font-size:10px; color:#4a7a9a; margin-bottom:10px;">© 2026 Maori Group</div>
        <img src="data:image/jpeg;base64,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SAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+56TFdW5T7LSzwgkOrcp9lpZ4QSAyu79z0jd+5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" style="width:85%; border-radius:8px; margin-top:4px;">
    </div>''', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────
if nav == "📊 Dashboard":

    st.markdown("""
    <div style="background:linear-gradient(135deg,#0d1b2a 0%,#1a3a5c 60%,#2471a3 100%);
        border-radius:16px; padding:28px 32px; margin-bottom:24px;">
        <h1 style="color:white; font-size:26px; font-weight:700; margin:0;">⚡ Maori – Vesper</h1>
        <p style="color:#90b8d8; font-size:14px; margin:4px 0 0 0;">Lavorazioni Vesper per Maori</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card("Fatturato Totale", fmt_eur(totale_generale), "tutti i mesi", "blue")
    with c2: kpi_card("Pagato da IREN", fmt_eur(totale_iren_pagato), "pratiche completate", "green")
    with c3: kpi_card("Ricavi Maori", fmt_eur(totale_ricavi_maori), "netto costi IREN", "orange")
    with c4: kpi_card("Pratiche Totali", str(n_pratiche_totali), f"✅ {n_completate} completate", "blue")
    with c5: kpi_card("In Lavorazione", str(n_in_lav), f"❌ {n_ko} K.O.", "red")

    st.markdown('<div class="section-title">📈 Andamento Mensile Fatturato</div>', unsafe_allow_html=True)

    df_plot = df_monthly_totals.copy()
    bar_colors = [COLORS['primary'] if a == '2024' else COLORS['secondary'] if a == '2025' else COLORS['accent']
                  for a in df_plot['anno']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_plot['label'], y=df_plot['totale'],
        marker_color=bar_colors, marker_line_color='white', marker_line_width=1.5,
        text=[fmt_eur(v) if v > 0 else '' for v in df_plot['totale']],
        textposition='outside', textfont=dict(size=10, color='#0d1b2a'),
        hovertemplate='<b>%{x}</b><br>Fatturato: %{y:,.2f} €<extra></extra>',
        name='Fatturato mensile'
    ))
    fig.add_trace(go.Scatter(
        x=df_plot['label'],
        y=df_plot['totale'].rolling(3, min_periods=1).mean(),
        mode='lines+markers', name='Media mobile (3m)',
        line=dict(color=COLORS['orange'], width=2, dash='dot'),
        marker=dict(size=5),
        hovertemplate='<b>Media 3m</b>: %{y:,.0f} €<extra></extra>'
    ))
    fig.update_layout(
        plot_bgcolor='white', paper_bgcolor='white', height=380,
        margin=dict(t=20, b=40, l=10, r=10),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis=dict(tickangle=-35, tickfont=dict(size=11), gridcolor='#f0f0f0'),
        yaxis=dict(gridcolor='#f0f0f0', tickprefix='€ ', tickformat=',.0f'),
        bargap=0.3, font=dict(family='Inter')
    )
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">📅 Riepilogo Annuo</div>', unsafe_allow_html=True)
        df_annuo = df_monthly_totals.groupby('anno')['totale'].sum().reset_index()
        fig_ann = go.Figure(go.Bar(
            x=df_annuo['anno'], y=df_annuo['totale'],
            marker_color=[COLORS['primary'], COLORS['secondary'], COLORS['accent']][:len(df_annuo)],
            marker_line_color='white', marker_line_width=2,
            text=[fmt_eur(v) for v in df_annuo['totale']],
            textposition='outside', width=0.5,
            hovertemplate='<b>%{x}</b><br>%{y:,.2f} €<extra></extra>'
        ))
        fig_ann.update_layout(
            plot_bgcolor='white', paper_bgcolor='white', height=300,
            margin=dict(t=20, b=10, l=10, r=10),
            xaxis=dict(type='category', tickfont=dict(size=14, family='Inter')),
            yaxis=dict(gridcolor='#f0f0f0', tickprefix='€ ', tickformat=',.0f'),
            font=dict(family='Inter')
        )
        st.plotly_chart(fig_ann, use_container_width=True)
        df_annuo_d = df_annuo.copy()
        df_annuo_d.columns = ['Anno', 'Totale']
        df_annuo_d['Totale'] = df_annuo_d['Totale'].apply(fmt_eur)
        st.dataframe(df_annuo_d, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown('<div class="section-title">📂 Stato Pratiche</div>', unsafe_allow_html=True)
        fig_pie = go.Figure(go.Pie(
            labels=['✅ Completate', '🔧 In Lavorazione', '❌ K.O.'],
            values=[n_completate, n_in_lav, n_ko],
            hole=0.55,
            marker=dict(colors=[COLORS['green'], COLORS['orange'], COLORS['red']],
                        line=dict(color='white', width=2)),
            textinfo='label+percent', textfont=dict(size=12, family='Inter'),
            hovertemplate='<b>%{label}</b><br>%{value} pratiche (%{percent})<extra></extra>'
        ))
        fig_pie.update_layout(
            plot_bgcolor='white', paper_bgcolor='white', height=300,
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False, font=dict(family='Inter'),
            annotations=[dict(text=f'<b>{n_pratiche_totali}</b><br>pratiche',
                              x=0.5, y=0.5, font_size=16, showarrow=False)]
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        df_2026 = df_monthly_totals[df_monthly_totals['anno'] == '2026']
        kpi_card("Fatturato 2026 (YTD)", fmt_eur(df_2026['totale'].sum()),
                 f"{len(df_2026)} mesi registrati", "green")

    st.markdown('<div class="section-title">🔥 Heatmap Lavorazioni per Mese</div>', unsafe_allow_html=True)
    tipo_map = {}
    for sheet in MONTHLY_SHEETS:
        if sheet not in monthly:
            continue
        for lav in monthly[sheet]['lavorazioni']:
            desc = lav['descrizione']
            n = lav['n_lavorazioni'] or 0
            if 'Verifica' in desc:       tipo = 'Verifica paesagg.'
            elif 'Layout' in desc:       tipo = 'Layout & unifilare'
            elif 'Fase 1' in desc:       tipo = 'Connessione Fase 1'
            elif 'Fase 2' in desc:       tipo = 'Connessione Fase 2'
            elif 'Relazion' in desc:     tipo = 'Relazioni tecniche'
            else:                         tipo = 'Altro'
            key = (MONTH_LABELS[sheet], tipo)
            tipo_map[key] = tipo_map.get(key, 0) + (n if isinstance(n, int) else 0)

    if tipo_map:
        df_heat = pd.DataFrame([{'Mese': k[0], 'Tipo': k[1], 'N': v} for k, v in tipo_map.items()])
        df_pivot = df_heat.pivot_table(index='Tipo', columns='Mese', values='N', aggfunc='sum', fill_value=0)
        ordered_cols = [MONTH_LABELS[s] for s in MONTHLY_SHEETS if MONTH_LABELS[s] in df_pivot.columns]
        df_pivot = df_pivot[ordered_cols]
        fig_heat = go.Figure(go.Heatmap(
            z=df_pivot.values, x=df_pivot.columns.tolist(), y=df_pivot.index.tolist(),
            colorscale=[[0,'#ecf0f1'],[0.5,'#2471a3'],[1,'#0d1b2a']],
            text=df_pivot.values, texttemplate='%{text}',
            textfont=dict(size=11, color='white'),
            hovertemplate='<b>%{y}</b> · %{x}<br>%{z} lavorazioni<extra></extra>'
        ))
        fig_heat.update_layout(
            plot_bgcolor='white', paper_bgcolor='white', height=280,
            margin=dict(t=10, b=40, l=160, r=10),
            xaxis=dict(tickangle=-35, tickfont=dict(size=10)),
            yaxis=dict(tickfont=dict(size=11)), font=dict(family='Inter')
        )
        st.plotly_chart(fig_heat, use_container_width=True)

# ─────────────────────────────────────────────
# PAGE: VISTA MENSILE
# ─────────────────────────────────────────────
elif nav == "📅 Vista Mensile":
    st.markdown("<h2 style='color:#0d1b2a;'>📅 Vista Mensile</h2>", unsafe_allow_html=True)

    available = [s for s in MONTHLY_SHEETS if s in monthly]
    selected_sheet = st.selectbox("Seleziona mese", available,
                                   format_func=lambda s: MONTH_LABELS[s],
                                   index=len(available)-1)
    data = monthly[selected_sheet]
    lavorazioni = data['lavorazioni']

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Totale Mese", fmt_eur(data['totale']), MONTH_LABELS[selected_sheet], "blue")
    with c2:
        n_attivi = len([l for l in lavorazioni if (l['n_lavorazioni'] or 0) > 0])
        kpi_card("Tipi Lavorazione Attivi", str(n_attivi), "con almeno 1 pratica", "green")
    with c3:
        n_lead = sum(len(l['leads']) for l in lavorazioni)
        kpi_card("Lead Totali nel Mese", str(n_lead), "pratiche associate", "orange")

    st.markdown('<div class="section-title">📋 Dettaglio Lavorazioni</div>', unsafe_allow_html=True)
    rows_lav = []
    for lav in lavorazioni:
        n = lav['n_lavorazioni']
        imp = lav['importo_unitario']
        tot_lav = (n * imp) if (n and imp and isinstance(n, int)) else None
        rows_lav.append({
            'Descrizione': lav['descrizione'],
            'N. Lavorazioni': n if n is not None else '–',
            'Importo Unitario': fmt_eur(imp),
            'Totale Riga': fmt_eur(tot_lav),
            'Da Fatturare': fmt_eur(lav['da_fatturare']),
            'N. Lead': len(lav['leads']),
        })
    if rows_lav:
        st.dataframe(pd.DataFrame(rows_lav), use_container_width=True, hide_index=True)

    all_leads = []
    for lav in lavorazioni:
        for lead in lav['leads']:
            all_leads.append({'Lead': lead, 'Lavorazione': lav['descrizione']})

    if all_leads:
        st.markdown('<div class="section-title">🎯 Lead Associati</div>', unsafe_allow_html=True)
        df_ls = pd.DataFrame(all_leads)
        df_ls['ID'] = df_ls['Lead'].apply(lambda x: x.split('_')[0].strip() if '_' in x else x)
        df_ls['Cliente'] = df_ls['Lead'].apply(lambda x: x.split('_', 1)[1].strip() if '_' in x else '')
        df_ls['ID_int'] = pd.to_numeric(df_ls['ID'], errors='coerce')
        df_enriched = df_ls.merge(
            df_vista[['Tutti gli id','Lavoro Ultimato Avanzamento','Iren','Ricavo Maori']],
            left_on='ID_int', right_on='Tutti gli id', how='left'
        )[['ID','Cliente','Lavorazione','Lavoro Ultimato Avanzamento','Iren','Ricavo Maori']]
        df_enriched.columns = ['ID','Cliente','Lavorazione','Stato','Pagato IREN (€)','Ricavo Maori (€)']
        st.dataframe(df_enriched, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# PAGE: RICERCA PRATICHE
# ─────────────────────────────────────────────
elif nav == "🔍 Ricerca Pratiche":
    st.markdown("<h2 style='color:#0d1b2a;'>🔍 Ricerca Pratiche</h2>", unsafe_allow_html=True)

    col_s1, col_s2, col_s3 = st.columns([2, 2, 1])
    with col_s1:
        search_text = st.text_input("🔎 Cerca per ID o Nome Cliente", placeholder="es. 56720 oppure Rossi")
    with col_s2:
        filter_stato = st.multiselect("Filtra per Stato",
            ['COMPLETATA','IN LAVORAZIONE','K.O.'], default=['COMPLETATA','IN LAVORAZIONE','K.O.'])
    with col_s3:
        filter_presente = st.multiselect("Presente In", df_vista['Presente In'].dropna().unique().tolist())

    df_filtered = df_vista.copy()
    if search_text:
        mask = (
            df_filtered['Tutti gli id'].astype(str).str.contains(search_text, case=False) |
            df_filtered['Cliente'].astype(str).str.contains(search_text, case=False, na=False)
        )
        df_filtered = df_filtered[mask]
    if filter_stato:
        df_filtered = df_filtered[df_filtered['Lavoro Ultimato Avanzamento'].isin(filter_stato)]
    if filter_presente:
        df_filtered = df_filtered[df_filtered['Presente In'].isin(filter_presente)]

    st.markdown(f"<div style='color:#666; margin-bottom:12px;'>Trovate <b>{len(df_filtered)}</b> pratiche</div>", unsafe_allow_html=True)

    if len(df_filtered) == 1:
        row = df_filtered.iloc[0]
        st.markdown(f"""
        <div style="background:white; border-radius:16px; padding:24px; box-shadow:0 2px 12px rgba(0,0,0,0.08);">
            <div style="font-size:22px; font-weight:700; color:#0d1b2a;">
                🆔 {int(row['Tutti gli id'])} – {row['Cliente']}
            </div>
            <div style="margin-top:8px;">{badge(row['Lavoro Ultimato Avanzamento'])}</div>
            <hr style="margin:16px 0; border-color:#eee;">
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:16px;">
                <div><div style="font-size:11px;color:#999;text-transform:uppercase;">Verifica Paesagg.</div>
                     <div style="font-size:16px;font-weight:600;">{fmt_eur(row.get('Verifica paesaggistica'))}</div></div>
                <div><div style="font-size:11px;color:#999;text-transform:uppercase;">Layout & Unifilare</div>
                     <div style="font-size:16px;font-weight:600;">{fmt_eur(row.get('Layout & unifilare'))}</div></div>
                <div><div style="font-size:11px;color:#999;text-transform:uppercase;">Connessione Fase 1</div>
                     <div style="font-size:16px;font-weight:600;">{fmt_eur(row.get('CONNESSIONE Fase 1'))}</div></div>
                <div><div style="font-size:11px;color:#999;text-transform:uppercase;">Connessione Fase 2</div>
                     <div style="font-size:16px;font-weight:600;">{fmt_eur(row.get('CONNESSIONE Fase 2'))}</div></div>
            </div>
            <hr style="margin:16px 0; border-color:#eee;">
            <div>
                <span style="font-size:12px;color:#999;">Pagato IREN:</span>
                <span style="font-size:16px;font-weight:600;color:#1a3a5c;margin-left:8px;">{fmt_eur(row.get('Iren'))}</span>
                &nbsp;&nbsp;
                <span style="font-size:12px;color:#999;">Ricavo Maori:</span>
                <span style="font-size:16px;font-weight:600;color:#2ecc71;margin-left:8px;">{fmt_eur(row.get('Ricavo Maori'))}</span>
                &nbsp;&nbsp;
                <span style="font-size:12px;color:#999;">Totale:</span>
                <span style="font-size:16px;font-weight:600;color:#1a3a5c;margin-left:8px;">{fmt_eur(row.get('Totale'))}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        pratica_id = int(row['Tutti gli id'])
        df_storico = df_lista[df_lista['Id'] == pratica_id]
        if not df_storico.empty:
            st.markdown('<div class="section-title">📋 Storico Lavorazioni</div>', unsafe_allow_html=True)
            df_s = df_storico[['Mese','Lavorazione','Importo lavorazione']].copy()
            df_s['Importo lavorazione'] = df_s['Importo lavorazione'].apply(fmt_eur)
            st.dataframe(df_s, use_container_width=True, hide_index=True)
    else:
        cols_show = ['Tutti gli id','Cliente','Presente In','Lavoro Ultimato Avanzamento','Iren','Ricavo Maori','Totale']
        df_show = df_filtered[cols_show].copy()
        df_show.columns = ['ID','Cliente','Presente In','Stato','Pagato IREN','Ricavo Maori','Totale Lav.']
        for col in ['Pagato IREN','Ricavo Maori','Totale Lav.']:
            df_show[col] = pd.to_numeric(df_show[col], errors='coerce').apply(fmt_eur)
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# PAGE: FINANZIARIO
# ─────────────────────────────────────────────
elif nav == "💶 Finanziario":
    st.markdown("<h2 style='color:#0d1b2a;'>💶 Riepilogo Finanziario</h2>", unsafe_allow_html=True)

    df_fc = df_fatture.copy()
    df_fc['PAGATO'] = pd.to_numeric(df_fc['PAGATO'], errors='coerce').fillna(0)
    df_fc['COSTO lavorazione '] = pd.to_numeric(df_fc['COSTO lavorazione '], errors='coerce').fillna(0)
    df_fc['PROGETTAZIONE '] = pd.to_numeric(df_fc['PROGETTAZIONE '], errors='coerce').fillna(0)

    totale_incassato = df_fc['PAGATO'].sum()
    totale_lav_fatt  = df_fc['COSTO lavorazione '].sum()
    delta = totale_incassato - totale_lav_fatt

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Totale Incassato IREN", fmt_eur(totale_incassato), f"{len(df_fc)} proforma", "blue")
    with c2: kpi_card("Costo Lavorazioni", fmt_eur(totale_lav_fatt), "fatturate ad IREN", "orange")
    with c3: kpi_card("Pagato da IREN (Vista)", fmt_eur(totale_iren_pagato), "totale pratiche", "green")
    with c4: kpi_card("Margine IREN", fmt_eur(delta), "incassato – costo lav.", "green" if delta >= 0 else "red")

    st.markdown('<div class="section-title">📄 Dettaglio Proforma IREN</div>', unsafe_allow_html=True)
    df_fd = df_fc[['DATA PROFORMA','PAGATO','PROGETTAZIONE ','COSTO lavorazione ']].copy()
    df_fd.columns = ['Data Proforma','Pagato (€)','N. Progettazioni','Costo Lavorazioni (€)']
    df_fd['Data Proforma'] = pd.to_datetime(df_fd['Data Proforma'], errors='coerce').dt.strftime('%d/%m/%Y')
    df_fd['Pagato (€)'] = df_fd['Pagato (€)'].apply(fmt_eur)
    df_fd['Costo Lavorazioni (€)'] = df_fd['Costo Lavorazioni (€)'].apply(fmt_eur)
    st.dataframe(df_fd.dropna(subset=['Data Proforma']), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">📊 Andamento Mensile Fatturato</div>', unsafe_allow_html=True)
    fig_fin = go.Figure(go.Bar(
        x=df_monthly_totals['label'], y=df_monthly_totals['totale'],
        marker_color=COLORS['primary'], opacity=0.85,
        hovertemplate='<b>%{x}</b><br>%{y:,.2f} €<extra></extra>'
    ))
    fig_fin.update_layout(
        plot_bgcolor='white', paper_bgcolor='white', height=340,
        margin=dict(t=20, b=40, l=10, r=10),
        xaxis=dict(tickangle=-35),
        yaxis=dict(gridcolor='#f0f0f0', tickprefix='€ ', tickformat=',.0f'),
        font=dict(family='Inter')
    )
    st.plotly_chart(fig_fin, use_container_width=True)

    st.markdown('<div class="section-title">🆔 ID Pagati da IREN</div>', unsafe_allow_html=True)
    df_dd = df_det_iren[['ID','PAGATO','richiesta mese','anno richiesta']].copy() if 'anno richiesta' in df_det_iren.columns else df_det_iren[['ID','PAGATO','richiesta mese']].copy()
    if 'anno richiesta' in df_det_iren.columns:
        df_dd['Mese Richiesta'] = df_dd['richiesta mese'].astype(str) + ' ' + df_dd['anno richiesta'].astype(str).str.replace('.0','', regex=False)
        df_dd = df_dd[['ID','PAGATO','Mese Richiesta']].copy()
    else:
        df_dd.columns = ['ID Pratica','Importo Pagato (€)','Mese Richiesta']
    df_dd.columns = ['ID Pratica','Importo Pagato (€)','Mese Richiesta']
    df_dd['Importo Pagato (€)'] = pd.to_numeric(df_dd['Importo Pagato (€)'], errors='coerce').apply(fmt_eur)
    st.dataframe(df_dd, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# PAGE: LISTINO VESPER
# ─────────────────────────────────────────────
elif nav == "📋 Listino Vesper":
    st.markdown("<h2 style='color:#0d1b2a;'>📋 Listino Vesper</h2>", unsafe_allow_html=True)

    df_lv = df_listino_vesper.copy()
    # Estrai righe valide (col 1 = descrizione, col 2 = importo)
    df_lv = df_lv.iloc[2:].reset_index(drop=True)
    df_lv = df_lv[[df_lv.columns[1], df_lv.columns[2]]].copy()
    df_lv.columns = ['Lavorazione', 'Importo (€)']
    df_lv = df_lv[df_lv['Lavorazione'].notna() & (df_lv['Lavorazione'].astype(str).str.strip() != '')].reset_index(drop=True)
    df_lv['Importo (€)'] = pd.to_numeric(df_lv['Importo (€)'], errors='coerce').apply(
        lambda x: f"€ {x:,.2f}".replace(",","X").replace(".",",").replace("X",".") if pd.notna(x) else "–"
    )

    st.markdown("""
    <div style="background:white; border-radius:16px; padding:20px 24px; box-shadow:0 2px 12px rgba(0,0,0,0.07); margin-bottom:20px;">
        <div style="font-size:13px; color:#666; margin-bottom:4px;">Tariffario ufficiale Vesper per lavorazioni IREN</div>
    </div>
    """, unsafe_allow_html=True)

    for _, row in df_lv.iterrows():
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;
            background:white; border-radius:10px; padding:14px 20px; margin-bottom:8px;
            box-shadow:0 1px 6px rgba(0,0,0,0.06); border-left:4px solid #1a3a5c;">
            <span style="font-size:14px; color:#0d1b2a; font-weight:500;">{row['Lavorazione']}</span>
            <span style="font-size:16px; font-weight:700; color:#1a3a5c;">{row['Importo (€)']}</span>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: LISTINO IREN
# ─────────────────────────────────────────────
elif nav == "📋 Listino IREN":
    st.markdown("<h2 style='color:#0d1b2a;'>📋 Listino IREN</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666; font-size:13px;'>Allegato C – Master Agreement IREN</p>", unsafe_allow_html=True)

    df_li = df_listino_iren.copy()
    df_li = df_li.iloc[2:].reset_index(drop=True)
    df_li.columns = ['_', 'Categoria', 'Descrizione', 'Importo (€)']

    current_cat = ""
    for _, row in df_li.iterrows():
        cat   = str(row['Categoria']).strip() if pd.notna(row['Categoria']) else ""
        desc  = str(row['Descrizione']).strip() if pd.notna(row['Descrizione']) else ""
        imp   = str(row['Importo (€)']).strip() if pd.notna(row['Importo (€)']) else ""

        if not desc or desc == 'nan':
            continue

        if cat and cat != 'nan':
            current_cat = cat.upper()
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0d1b2a,#1a3a5c); color:white;
                border-radius:10px; padding:10px 18px; margin:18px 0 8px 0; font-weight:700; font-size:13px; letter-spacing:1px;">
                {current_cat}
            </div>
            """, unsafe_allow_html=True)

        try:
            imp_num = float(imp)
            imp_fmt = f"€ {imp_num:,.2f}".replace(",","X").replace(".",",").replace("X",".")
            imp_color = "#1a3a5c"
        except:
            imp_fmt = imp if imp and imp != 'nan' else "–"
            imp_color = "#888"

        desc_clean = desc.replace('\n', ' ')
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:flex-start;
            background:white; border-radius:10px; padding:12px 18px; margin-bottom:6px;
            box-shadow:0 1px 6px rgba(0,0,0,0.06); border-left:4px solid #2471a3;">
            <span style="font-size:13px; color:#333; flex:1; padding-right:20px;">{desc_clean}</span>
            <span style="font-size:15px; font-weight:700; color:{imp_color}; white-space:nowrap;">{imp_fmt}</span>
        </div>
        """, unsafe_allow_html=True)
