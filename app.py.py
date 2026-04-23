import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Vesper – Portale IREN",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# STILE CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main { background-color: #f5f7fa; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1b2a 0%, #1a3a5c 100%);
    }
    [data-testid="stSidebar"] * { color: #e8f0fe !important; }
    [data-testid="stSidebar"] .stRadio label { color: #e8f0fe !important; }

    /* KPI Cards */
    .kpi-card {
        background: white;
        border-radius: 16px;
        padding: 24px 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border-left: 5px solid #1a3a5c;
        margin-bottom: 8px;
    }
    .kpi-card.green  { border-left-color: #2ecc71; }
    .kpi-card.orange { border-left-color: #e67e22; }
    .kpi-card.red    { border-left-color: #e74c3c; }
    .kpi-card.blue   { border-left-color: #1a3a5c; }
    .kpi-label { font-size: 12px; font-weight: 600; color: #8899aa; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #0d1b2a; }
    .kpi-sub   { font-size: 12px; color: #aabbcc; margin-top: 4px; }

    /* Section title */
    .section-title {
        font-size: 18px; font-weight: 700; color: #0d1b2a;
        margin: 24px 0 12px 0; border-bottom: 2px solid #e0e8f0; padding-bottom: 6px;
    }

    /* Badge */
    .badge-completata    { background:#d4edda; color:#155724; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-in-lavorazione{ background:#fff3cd; color:#856404; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-ko            { background:#f8d7da; color:#721c24; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }

    /* Table */
    .dataframe thead th { background-color: #1a3a5c !important; color: white !important; }

    /* Header portale */
    .portal-header {
        background: linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 60%, #2471a3 100%);
        border-radius: 16px; padding: 28px 32px; margin-bottom: 24px;
        display: flex; align-items: center; gap: 24px;
    }
    .portal-header h1 { color: white; font-size: 26px; font-weight: 700; margin: 0; }
    .portal-header p  { color: #90b8d8; font-size: 14px; margin: 4px 0 0 0; }

    div[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700 !important; }

    /* Plotly chart container */
    .chart-box {
        background: white; border-radius: 16px;
        padding: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
FILE_PATH = "analitico-iren-utecnico.xlsx"

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
    'light':     '#ecf0f1',
    'iren_orange':'#e85d00',
}

@st.cache_data
def load_all_data():
    xl = pd.ExcelFile(FILE_PATH)

    # ── Monthly sheets
    monthly = {}
    for sheet in MONTHLY_SHEETS:
        df = xl.parse(sheet, header=None)
        # totale
        totale = None
        for col in [9, 8]:
            if df.shape[1] > col:
                val = df.iloc[1, col]
                if pd.notna(val) and isinstance(val, (int, float)):
                    totale = float(val)
                    break

        lavorazioni = []
        i = 2
        while i < len(df):
            desc = df.iloc[i, 1] if not pd.isna(df.iloc[i, 1]) else ''
            desc = str(desc).strip()
            if not desc or desc == 'nan' or desc == 'Lead:':
                i += 1
                continue

            n_lav   = df.iloc[i, 4] if df.shape[1] > 4 else None
            importo = df.iloc[i, 5] if df.shape[1] > 5 else None
            da_fatt = df.iloc[i, 6] if df.shape[1] > 6 else None

            leads = []
            # older format: leads embedded in description
            if '\n' in desc or '
' in desc:
                lines = desc.replace('\n', '
').split('
')
                desc_clean = lines[0].strip()
                for line in lines[1:]:
                    line = line.strip()
                    if line and '_' in line:
                        leads.append(line)
            else:
                desc_clean = desc
                # newer format: next row may be "Lead
 id_cliente..."
                if i + 1 < len(df):
                    next_val = str(df.iloc[i+1, 1]) if not pd.isna(df.iloc[i+1, 1]) else ''
                    if next_val.startswith('Lead'):
                        for part in next_val.replace('Lead', '').replace('\n', '
').split('
'):
                            part = part.strip()
                            if part and '_' in part:
                                leads.append(part)

            # parse importo da fatturare
            da_fatt_val = None
            if pd.notna(da_fatt):
                try:
                    da_fatt_val = float(str(da_fatt).replace('€','').replace('-','').strip())
                except:
                    da_fatt_val = None

            n_lav_val = None
            if pd.notna(n_lav):
                try:
                    n_lav_val = int(float(str(n_lav)))
                except:
                    n_lav_val = None

            importo_val = None
            if pd.notna(importo):
                try:
                    importo_val = float(str(importo))
                except:
                    importo_val = None

            lavorazioni.append({
                'descrizione':    desc_clean,
                'n_lavorazioni':  n_lav_val,
                'importo_unitario': importo_val,
                'da_fatturare':   da_fatt_val,
                'leads':          leads,
                'mese':           sheet,
            })
            i += 1

        monthly[sheet] = {'totale': totale, 'lavorazioni': lavorazioni}

    # ── Vista pratiche
    df_vista = xl.parse('Vista Per ID UFFICIO TECNICO', header=0)
    df_vista = df_vista.dropna(subset=['Tutti gli id'])
    df_vista['Tutti gli id'] = df_vista['Tutti gli id'].astype(int)
    df_vista.columns = df_vista.columns.str.strip()

    # ── Lista ID
    df_lista = xl.parse('Lista ID', header=0)
    df_lista = df_lista[['Mese','Lavorazione','Id','Cliente','Inizio attività','Fine attività','Importo lavorazione']].dropna(subset=['Id'])
    df_lista['Id'] = df_lista['Id'].astype(int)

    # ── Dettaglio Fatture IREN
    df_fatture = xl.parse('DETTAGLIO FATTURE IREN', header=0)
    df_fatture = df_fatture.dropna(subset=['PAGATO'])

    # ── Dettaglio ID IREN
    df_det_iren = xl.parse('DETTAGLIO ID IREN', header=0)
    df_det_iren = df_det_iren.dropna(subset=['ID'])
    df_det_iren['ID'] = df_det_iren['ID'].astype(int)

    return monthly, df_vista, df_lista, df_fatture, df_det_iren

monthly, df_vista, df_lista, df_fatture, df_det_iren = load_all_data()

# ─────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:42px;">⚡</div>
        <div style="font-size:18px; font-weight:700; color:#e8f0fe; margin-top:6px;">VESPER</div>
        <div style="font-size:11px; color:#6a98c0; letter-spacing:2px;">PORTALE IREN</div>
    </div>
    <hr style="border-color:#2a4a6a; margin:10px 0 20px 0;">
    """, unsafe_allow_html=True)

    nav = st.radio(
        "Navigazione",
        ["📊 Dashboard", "📅 Vista Mensile", "🔍 Ricerca Pratiche", "💶 Finanziario"],
        label_visibility="collapsed"
    )

    st.markdown("<hr style=\"border-color:#2a4a6a; margin-top:30px;\">", unsafe_allow_html=True)
    st.markdown("<div style=\"font-size:10px; color:#4a7a9a; text-align:center; padding-top:8px;\">© 2026 Vesper<br>Portale Gestionale IREN</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt_eur(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "–"
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def kpi_card(label, value, sub="", color="blue"):
    st.markdown(f"""
    <div class="kpi-card {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def badge(stato):
    stato = str(stato).strip().upper()
    if stato == "COMPLETATA":
        return f'<span class="badge-completata">✅ Completata</span>'
    elif stato == "IN LAVORAZIONE":
        return f'<span class="badge-in-lavorazione">🔧 In Lavorazione</span>'
    elif stato == "K.O.":
        return f'<span class="badge-ko">❌ K.O.</span>'
    return f'<span>{stato}</span>'

# ─────────────────────────────────────────────
# CALCOLI GLOBALI
# ─────────────────────────────────────────────
totali_mese = {s: monthly[s]['totale'] or 0 for s in MONTHLY_SHEETS}
df_monthly_totals = pd.DataFrame([
    {'sheet': s, 'label': MONTH_LABELS[s], 'totale': totali_mese[s],
     'anno': '20' + s.split('-')[1]}
    for s in MONTHLY_SHEETS
])

totale_generale   = df_monthly_totals['totale'].sum()
n_pratiche_totali = len(df_vista)
n_completate      = len(df_vista[df_vista['Lavoro Ultimato Avanzamento'] == 'COMPLETATA'])
n_in_lav          = len(df_vista[df_vista['Lavoro Ultimato Avanzamento'] == 'IN LAVORAZIONE'])
n_ko              = len(df_vista[df_vista['Lavoro Ultimato Avanzamento'] == 'K.O.'])
totale_iren_pagato = pd.to_numeric(df_vista['Iren'], errors='coerce').sum()
totale_ricavi_maori= pd.to_numeric(df_vista['Ricavo Maori'], errors='coerce').sum()

# ─────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────
if nav == "📊 Dashboard":

    st.markdown("""
    <div class="portal-header">
        <div>
            <h1>⚡ Portale Gestionale IREN</h1>
            <p>Ufficio Tecnico · Riepilogo lavorazioni e fatturato IREN</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Fatturato Totale", fmt_eur(totale_generale), "tutti i mesi", "blue")
    with c2:
        kpi_card("Pagato da IREN", fmt_eur(totale_iren_pagato), "su pratiche completate", "green")
    with c3:
        kpi_card("Ricavi Maori", fmt_eur(totale_ricavi_maori), "netto costi IREN", "orange")
    with c4:
        kpi_card("Pratiche Totali", str(n_pratiche_totali), f"✅ {n_completate} completate", "blue")
    with c5:
        kpi_card("In Lavorazione", str(n_in_lav), f"❌ {n_ko} K.O.", "red")

    st.markdown("<div class=\"section-title\">📈 Andamento Mensile Fatturato</div>", unsafe_allow_html=True)

    # ── Grafico principale andamento mensile
    df_plot = df_monthly_totals.copy()

    fig_bar = go.Figure()
    colors_bars = [COLORS['primary'] if a == '2024' else COLORS['secondary'] if a == '2025' else COLORS['accent']
                   for a in df_plot['anno']]

    fig_bar.add_trace(go.Bar(
        x=df_plot['label'],
        y=df_plot['totale'],
        marker_color=colors_bars,
        marker_line_color='white',
        marker_line_width=1.5,
        text=[fmt_eur(v) if v > 0 else '' for v in df_plot['totale']],
        textposition='outside',
        textfont=dict(size=10, color='#0d1b2a'),
        hovertemplate='<b>%{x}</b><br>Fatturato: %{y:,.2f} €<extra></extra>',
        name='Fatturato mensile'
    ))

    fig_bar.add_trace(go.Scatter(
        x=df_plot['label'],
        y=df_plot['totale'].rolling(3, min_periods=1).mean(),
        mode='lines+markers',
        name='Media mobile (3m)',
        line=dict(color=COLORS['orange'], width=2, dash='dot'),
        marker=dict(size=5),
        hovertemplate='<b>Media 3m</b>: %{y:,.0f} €<extra></extra>'
    ))

    fig_bar.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        height=380,
        margin=dict(t=20, b=40, l=10, r=10),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis=dict(tickangle=-35, tickfont=dict(size=11), gridcolor='#f0f0f0'),
        yaxis=dict(gridcolor='#f0f0f0', tickprefix='€ ', tickformat=',.0f'),
        bargap=0.3,
        font=dict(family='Inter')
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Riepilogo annuo e stato pratiche
    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.markdown("<div class=\"section-title\">📅 Riepilogo Annuo</div>", unsafe_allow_html=True)

        df_annuo = df_monthly_totals.groupby('anno')['totale'].sum().reset_index()
        df_annuo.columns = ['Anno', 'Totale']

        fig_ann = go.Figure()
        ann_colors = [COLORS['primary'], COLORS['secondary'], COLORS['accent']]
        fig_ann.add_trace(go.Bar(
            x=df_annuo['Anno'],
            y=df_annuo['Totale'],
            marker_color=ann_colors[:len(df_annuo)],
            marker_line_color='white',
            marker_line_width=2,
            text=[fmt_eur(v) for v in df_annuo['Totale']],
            textposition='outside',
            textfont=dict(size=12, color='#0d1b2a', family='Inter'),
            hovertemplate='<b>%{x}</b><br>Totale: %{y:,.2f} €<extra></extra>',
            width=0.5
        ))
        fig_ann.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            height=300, margin=dict(t=20, b=10, l=10, r=10),
            xaxis=dict(tickfont=dict(size=13, family='Inter')),
            yaxis=dict(gridcolor='#f0f0f0', tickprefix='€ ', tickformat=',.0f'),
            font=dict(family='Inter')
        )
        st.plotly_chart(fig_ann, use_container_width=True)

        # Tabella riepilogo annuo
        df_annuo_display = df_annuo.copy()
        df_annuo_display['Totale'] = df_annuo_display['Totale'].apply(fmt_eur)
        st.dataframe(df_annuo_display, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown("<div class=\"section-title\">📂 Stato Pratiche</div>", unsafe_allow_html=True)

        fig_pie = go.Figure(go.Pie(
            labels=['✅ Completate', '🔧 In Lavorazione', '❌ K.O.'],
            values=[n_completate, n_in_lav, n_ko],
            hole=0.55,
            marker=dict(colors=[COLORS['green'], COLORS['orange'], COLORS['red']],
                        line=dict(color='white', width=2)),
            textinfo='label+percent',
            textfont=dict(size=12, family='Inter'),
            hovertemplate='<b>%{label}</b><br>%{value} pratiche (%{percent})<extra></extra>'
        ))
        fig_pie.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            height=300, margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False, font=dict(family='Inter'),
            annotations=[dict(
                text=f'<b>{n_pratiche_totali}</b><br><span style="font-size:10px">pratiche</span>',
                x=0.5, y=0.5, font_size=18, showarrow=False
            )]
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        # KPI mini per anno corrente
        df_2026 = df_monthly_totals[df_monthly_totals['anno'] == '2026']
        st.markdown(f"""
        <div class="kpi-card green" style="margin-top:8px;">
            <div class="kpi-label">Fatturato 2026 (YTD)</div>
            <div class="kpi-value">{fmt_eur(df_2026['totale'].sum())}</div>
            <div class="kpi-sub">{len(df_2026)} mesi registrati</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Heatmap per tipo lavorazione
    st.markdown("<div class=\"section-title\">🔥 Heatmap Lavorazioni per Mese</div>", unsafe_allow_html=True)

    tipo_map = {}
    for sheet in MONTHLY_SHEETS:
        for lav in monthly[sheet]['lavorazioni']:
            desc = lav['descrizione']
            n    = lav['n_lavorazioni'] or 0
            # Simplify tipo
            if 'Verifica' in desc:      tipo = 'Verifica paesagg.'
            elif 'Layout' in desc:      tipo = 'Layout & unifilare'
            elif 'Fase 1' in desc:      tipo = 'Connessione Fase 1'
            elif 'Fase 2' in desc:      tipo = 'Connessione Fase 2'
            elif 'Relazion' in desc:    tipo = 'Relazioni tecniche'
            else:                        tipo = 'Altro'
            key = (MONTH_LABELS[sheet], tipo)
            tipo_map[key] = tipo_map.get(key, 0) + (n if isinstance(n, int) else 0)

    if tipo_map:
        rows_heat = [{'Mese': k[0], 'Tipo': k[1], 'N': v} for k, v in tipo_map.items()]
        df_heat = pd.DataFrame(rows_heat)
        df_pivot = df_heat.pivot_table(index='Tipo', columns='Mese', values='N', aggfunc='sum', fill_value=0)
        # Ordina colonne per ordine temporale
        ordered_cols = [MONTH_LABELS[s] for s in MONTHLY_SHEETS if MONTH_LABELS[s] in df_pivot.columns]
        df_pivot = df_pivot[ordered_cols]

        fig_heat = go.Figure(go.Heatmap(
            z=df_pivot.values,
            x=df_pivot.columns.tolist(),
            y=df_pivot.index.tolist(),
            colorscale=[[0,'#ecf0f1'],[0.5,'#2471a3'],[1,'#0d1b2a']],
            text=df_pivot.values,
            texttemplate='%{text}',
            textfont=dict(size=11, color='white'),
            hovertemplate='<b>%{y}</b> · %{x}<br>%{z} lavorazioni<extra></extra>',
            showscale=True
        ))
        fig_heat.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            height=280, margin=dict(t=10, b=40, l=160, r=10),
            xaxis=dict(tickangle=-35, tickfont=dict(size=10)),
            yaxis=dict(tickfont=dict(size=11)),
            font=dict(family='Inter')
        )
        st.plotly_chart(fig_heat, use_container_width=True)

# ─────────────────────────────────────────────
# PAGE: VISTA MENSILE
# ─────────────────────────────────────────────
elif nav == "📅 Vista Mensile":

    st.markdown("<h2 style='color:#0d1b2a;'>📅 Vista Mensile</h2>", unsafe_allow_html=True)

    selected_sheet = st.selectbox(
        "Seleziona mese",
        MONTHLY_SHEETS,
        format_func=lambda s: MONTH_LABELS[s],
        index=len(MONTHLY_SHEETS)-1
    )

    data = monthly[selected_sheet]
    lavorazioni = data['lavorazioni']
    totale_mese = data['totale']

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Totale Mese", fmt_eur(totale_mese), MONTH_LABELS[selected_sheet], "blue")
    with c2:
        n_tipi = len([l for l in lavorazioni if (l['n_lavorazioni'] or 0) > 0])
        kpi_card("Tipi di Lavorazione Attivi", str(n_tipi), "con almeno 1 pratica", "green")
    with c3:
        n_lead = sum(len(l['leads']) for l in lavorazioni)
        kpi_card("Lead Totali nel Mese", str(n_lead), "pratiche associate", "orange")

    st.markdown("<div class=\"section-title\">📋 Dettaglio Lavorazioni</div>", unsafe_allow_html=True)

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
        df_lav = pd.DataFrame(rows_lav)
        st.dataframe(df_lav, use_container_width=True, hide_index=True)

    # ── Lead del mese
    all_leads = []
    for lav in lavorazioni:
        for lead in lav['leads']:
            all_leads.append({'Lead': lead, 'Lavorazione': lav['descrizione']})

    if all_leads:
        st.markdown("<div class=\"section-title\">🎯 Lead Associati</div>", unsafe_allow_html=True)
        df_leads_show = pd.DataFrame(all_leads)
        # Separa ID e Cliente
        df_leads_show['ID'] = df_leads_show['Lead'].apply(lambda x: x.split('_')[0].strip() if '_' in x else x)
        df_leads_show['Cliente'] = df_leads_show['Lead'].apply(lambda x: x.split('_', 1)[1].strip() if '_' in x else '')
        df_leads_show = df_leads_show[['ID', 'Cliente', 'Lavorazione']]

        # Arricchisci con stato da Vista
        df_leads_show['ID_int'] = pd.to_numeric(df_leads_show['ID'], errors='coerce')
        df_leads_enriched = df_leads_show.merge(
            df_vista[['Tutti gli id','Lavoro Ultimato Avanzamento','Iren','Ricavo Maori']],
            left_on='ID_int', right_on='Tutti gli id', how='left'
        )
        df_leads_enriched = df_leads_enriched[['ID','Cliente','Lavorazione','Lavoro Ultimato Avanzamento','Iren','Ricavo Maori']]
        df_leads_enriched.columns = ['ID','Cliente','Lavorazione','Stato','Pagato IREN (€)','Ricavo Maori (€)']
        st.dataframe(df_leads_enriched, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# PAGE: RICERCA PRATICHE
# ─────────────────────────────────────────────
elif nav == "🔍 Ricerca Pratiche":

    st.markdown("<h2 style='color:#0d1b2a;'>🔍 Ricerca Pratiche</h2>", unsafe_allow_html=True)

    col_s1, col_s2, col_s3 = st.columns([2, 2, 1])
    with col_s1:
        search_text = st.text_input("🔎 Cerca per ID o Nome Cliente", placeholder="es. 56720 oppure Rossi")
    with col_s2:
        filter_stato = st.multiselect("Filtra per Stato", ['COMPLETATA','IN LAVORAZIONE','K.O.'],
                                       default=['COMPLETATA','IN LAVORAZIONE','K.O.'])
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

    # Scheda singola pratica
    if len(df_filtered) == 1:
        row = df_filtered.iloc[0]
        st.markdown(f"""
        <div style="background:white; border-radius:16px; padding:24px; box-shadow:0 2px 12px rgba(0,0,0,0.08); margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="font-size:22px; font-weight:700; color:#0d1b2a;">
                        🆔 {int(row['Tutti gli id'])} – {row['Cliente']}
                    </div>
                    <div style="margin-top:8px;">{badge(row['Lavoro Ultimato Avanzamento'])}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:24px; font-weight:700; color:#1a3a5c;">{fmt_eur(row['Iren'])}</div>
                    <div style="font-size:12px; color:#aaa;">Pagato da IREN</div>
                </div>
            </div>
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
            <div><span style="font-size:12px;color:#999;">Ricavo Maori:</span>
                 <span style="font-size:16px;font-weight:600;color:#2ecc71;margin-left:8px;">{fmt_eur(row.get('Ricavo Maori'))}</span>
                 &nbsp;&nbsp;
                 <span style="font-size:12px;color:#999;">Totale Lavorazione:</span>
                 <span style="font-size:16px;font-weight:600;color:#1a3a5c;margin-left:8px;">{fmt_eur(row.get('Totale'))}</span>
            </div>
            {f'<div style="margin-top:10px;font-size:12px;color:#777;">Note: {row["note"]}</div>' if pd.notna(row.get("note")) else ""}
        </div>
        """, unsafe_allow_html=True)

        # Storico lavorazioni per questa pratica
        pratica_id = int(row['Tutti gli id'])
        df_storico = df_lista[df_lista['Id'] == pratica_id]
        if not df_storico.empty:
            st.markdown("<div class=\"section-title\">📋 Storico Lavorazioni per questa Pratica</div>", unsafe_allow_html=True)
            df_storico_disp = df_storico[['Mese','Lavorazione','Importo lavorazione']].copy()
            df_storico_disp['Importo lavorazione'] = df_storico_disp['Importo lavorazione'].apply(fmt_eur)
            st.dataframe(df_storico_disp, use_container_width=True, hide_index=True)

    else:
        # Tabella
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

    # KPI
    df_fatture_clean = df_fatture.copy()
    df_fatture_clean['PAGATO'] = pd.to_numeric(df_fatture_clean['PAGATO'], errors='coerce').fillna(0)
    df_fatture_clean['COSTO lavorazione '] = pd.to_numeric(df_fatture_clean['COSTO lavorazione '], errors='coerce').fillna(0)
    df_fatture_clean['PROGETTAZIONE '] = pd.to_numeric(df_fatture_clean['PROGETTAZIONE '], errors='coerce').fillna(0)

    totale_incassato = df_fatture_clean['PAGATO'].sum()
    totale_lav_fatt  = df_fatture_clean['COSTO lavorazione '].sum()
    n_fatture        = len(df_fatture_clean)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Totale Incassato IREN", fmt_eur(totale_incassato), f"{n_fatture} proforma", "blue")
    with c2:
        kpi_card("Costo Lavorazioni Fatturate", fmt_eur(totale_lav_fatt), "su pratiche chiuse", "orange")
    with c3:
        kpi_card("Pagato da IREN (Vista)", fmt_eur(totale_iren_pagato), "totale su pratiche", "green")
    with c4:
        delta = totale_incassato - totale_lav_fatt
        kpi_card("Margine IREN", fmt_eur(delta), "incassato – costo lav.", "green" if delta >= 0 else "red")

    # Tabella fatture
    st.markdown("<div class=\"section-title\">📄 Dettaglio Proforma IREN</div>", unsafe_allow_html=True)
    df_fatture_disp = df_fatture_clean[['DATA PROFORMA','PAGATO','PROGETTAZIONE ','COSTO lavorazione ']].copy()
    df_fatture_disp.columns = ['Data Proforma','Pagato (€)','N. Progettazioni','Costo Lavorazioni (€)']
    df_fatture_disp['Data Proforma'] = pd.to_datetime(df_fatture_disp['Data Proforma'], errors='coerce').dt.strftime('%d/%m/%Y')
    df_fatture_disp['Pagato (€)'] = df_fatture_disp['Pagato (€)'].apply(fmt_eur)
    df_fatture_disp['Costo Lavorazioni (€)'] = df_fatture_disp['Costo Lavorazioni (€)'].apply(fmt_eur)
    st.dataframe(df_fatture_disp.dropna(subset=['Data Proforma']), use_container_width=True, hide_index=True)

    # Grafico IREN pagato per mese
    st.markdown("<div class=\"section-title\">📊 Confronto Fatturato vs Costi per Mese</div>", unsafe_allow_html=True)

    df_comp = df_monthly_totals.copy()
    # Aggiungi colonna incassato IREN dalla sintesi
    sintesi_map = {
        'lug 2024': ('2024','07'), 'ago 2024': ('2024','08'), 'set 2024': ('2024','09'),
        'ott 2024': ('2024','10'), 'nov 2024': ('2024','11'), 'dic 2024': ('2024','12'),
        'gen 2025': ('2025','01'), 'feb 2025': ('2025','02'), 'mar 2025': ('2025','03'),
        'apr 2025': ('2025','04'), 'mag 2025': ('2025','05'), 'giu 2025': ('2025','06'),
        'lug 2025': ('2025','07'),
    }

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(
        name='Fatturato Mensile (Maori)',
        x=df_comp['label'], y=df_comp['totale'],
        marker_color=COLORS['primary'], opacity=0.85
    ))

    fig_comp.update_layout(
        barmode='group',
        plot_bgcolor='white', paper_bgcolor='white',
        height=360, margin=dict(t=20, b=40, l=10, r=10),
        xaxis=dict(tickangle=-35),
        yaxis=dict(gridcolor='#f0f0f0', tickprefix='€ ', tickformat=',.0f'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        font=dict(family='Inter')
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # Dettaglio ID IREN pagati
    st.markdown("<div class=\"section-title\">🆔 ID Pagati da IREN</div>", unsafe_allow_html=True)
    df_det_disp = df_det_iren[['ID','PAGATO','richiesta mese']].copy()
    df_det_disp.columns = ['ID Pratica','Importo Pagato (€)','Mese Richiesta']
    df_det_disp['Importo Pagato (€)'] = pd.to_numeric(df_det_disp['Importo Pagato (€)'], errors='coerce').apply(fmt_eur)
    st.dataframe(df_det_disp, use_container_width=True, hide_index=True)
