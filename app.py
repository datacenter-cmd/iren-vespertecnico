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

    return monthly, df_vista, df_lista, df_fatture, df_det_iren

try:
    monthly, df_vista, df_lista, df_fatture, df_det_iren = load_all_data()
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
        ["📊 Dashboard", "📅 Vista Mensile", "🔍 Ricerca Pratiche", "💶 Finanziario"],
        label_visibility="collapsed"
    )

    st.markdown('<hr style="border-color:#2a4a6a; margin-top:20px;">', unsafe_allow_html=True)

    if st.button("🔄 Aggiorna Dati", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    authenticator.logout("🚪 Logout", location="sidebar")

    st.markdown('<div style="font-size:10px; color:#4a7a9a; text-align:center; padding-top:12px;">© 2026 Maori Group</div>', unsafe_allow_html=True)

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
    df_dd = df_det_iren[['ID','PAGATO','richiesta mese']].copy()
    df_dd.columns = ['ID Pratica','Importo Pagato (€)','Mese Richiesta']
    df_dd['Importo Pagato (€)'] = pd.to_numeric(df_dd['Importo Pagato (€)'], errors='coerce').apply(fmt_eur)
    st.dataframe(df_dd, use_container_width=True, hide_index=True)
