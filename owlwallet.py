import calendar
import json
import re
import unicodedata
from io import BytesIO
from pathlib import Path
 
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
 
st.set_page_config(page_title="OwlWallet", page_icon="🦉", layout="wide")
 
# ───────────────────────── Constantes ─────────────────────────
LOGO_URL = "https://i.postimg.cc/fbXHRGfY/logo-a.png"
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "owlwallet_datos.json"
SETTINGS_FILE = BASE_DIR / "owlwallet_ajustes.json"
 
COLS = ["Fecha", "Tipo", "Categoría", "Descripción", "Monto"]
TIPOS = ["Gasto", "Ingreso"]
DEFAULT_CATEGORIES = [
    "Comida", "Transporte", "Servicios", "Hogar", "Entretenimiento",
    "Salud", "Educación", "Ropa", "Ahorro", "Otros",
]
MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
 
# Paleta negro + morado
BG = "#0A0A0A"
CARD = "#141109"
CARD_2 = "#1C170B"
BORDER = "#3A2F12"
TEXT = "#F5ECD0"
MUTED = "#B3A57A"
P1, P2, P3, P4, P5, P6 = "#D4AF37", "#E6C65C", "#B8860B", "#F2D98A", "#7A5C10", "#FBEFC4"
DANGER = "#F43F5E"
PALETTE = ["#D4AF37", "#F2D98A", "#B8860B", "#8C6D1F", "#FFE9A8", "#C9A227", "#6B5416", "#E8C547", "#A67C00", "#F7E7B0"]
 
METRIC_TERMS = {"monto", "gasto", "gastos", "importe", "valor", "precio", "costo", "total", "amount", "price", "cost"}
CAT_TERMS = {"categoria", "category", "tipo_gasto", "concepto", "rubro", "grupo"}
DESC_TERMS = {"descripcion", "detalle", "nota", "notas", "description", "detail", "nombre", "producto"}
DATE_TERMS = {"fecha", "date", "dia", "periodo"}
TYPE_TERMS = {"tipo", "type", "movimiento", "clase"}
 
 
# ───────────────────────── Estilos ─────────────────────────
def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
        .stApp {{ background: radial-gradient(1200px 600px at 85% -10%, #3a2d0a 0%, {BG} 55%); color: {TEXT}; }}
        header[data-testid="stHeader"] {{ background: transparent; }}
        section[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #050505 0%, #231a07 100%); border-right: 1px solid {BORDER}; }}
        section[data-testid="stSidebar"] * {{ color: {TEXT}; }}
        h1, h2, h3, h4, h5, p, label, span, div {{ color: {TEXT}; }}
        .brand {{ display:flex; align-items:center; gap:12px; padding: 6px 0 20px; }}
        .brand img {{ width:44px; height:44px; object-fit:contain; }}
        .brand-title {{ font-size:20px; font-weight:800; line-height:1.1; }}
        .brand-subtitle {{ font-size:9px; letter-spacing:1.6px; color:{P4}; margin-top:4px; font-weight:700; }}
        .hero {{ background: linear-gradient(115deg, #0a0a0a 0%, #2a2008 60%, {P3} 140%); border:1px solid {BORDER};
                 border-radius:22px; padding:30px 36px; box-shadow:0 14px 40px rgba(212,175,55,.22); margin-bottom:20px; }}
        .hero h1 {{ font-size:32px; margin:0 0 8px; font-weight:800; letter-spacing:-1px; }}
        .hero p {{ margin:0; max-width:760px; color:{P6}; font-size:14.5px; line-height:1.6; }}
        .section-title {{ font-size:19px; font-weight:800; margin:26px 0 4px; color:{P6}; }}
        .section-subtitle {{ color:{MUTED}; font-size:13px; margin-bottom:14px; }}
        .kpi-card {{ background: linear-gradient(160deg, {CARD_2}, {CARD}); border:1px solid {BORDER}; border-radius:16px;
                     padding:18px 20px; min-height:108px; box-shadow:0 6px 20px rgba(0,0,0,.45); }}
        .kpi-label {{ color:{MUTED}; font-size:11.5px; font-weight:700; text-transform:uppercase; letter-spacing:.8px; }}
        .kpi-value {{ color:{P6}; font-size:25px; font-weight:800; margin-top:8px; letter-spacing:-.5px; }}
        .kpi-detail {{ color:{P2}; font-size:12px; margin-top:5px; }}
        .kpi-card.danger {{ border-color:{DANGER}; box-shadow:0 0 0 1px {DANGER}55, 0 6px 20px rgba(0,0,0,.45); }}
        .kpi-card.danger .kpi-value {{ color:#FDA4AF; }}
        .alert-box {{ border-radius:14px; padding:14px 18px; margin:10px 0; border:1px solid; }}
        .alert-box.danger {{ background: rgba(244,63,94,.10); border-color: {DANGER}; }}
        .alert-box.warn {{ background: rgba(230,198,92,.12); border-color: {P2}; }}
        .alert-box.ok {{ background: rgba(212,175,55,.10); border-color: {P3}; }}
        .alert-box h4 {{ margin:0 0 6px; font-size:15px; }}
        .alert-box ul {{ margin:6px 0 0 18px; padding:0; }}
        .alert-box li {{ margin:3px 0; font-size:13.5px; color:{TEXT}; }}
        .pill {{ display:inline-block; background:{CARD_2}; border:1px solid {BORDER}; border-radius:99px; padding:4px 12px; font-size:12px; color:{P4}; font-weight:600; }}
        div[data-testid="stTabs"] button[role="tab"] {{ color:{MUTED}; font-weight:600; }}
        div[data-testid="stTabs"] button[aria-selected="true"] {{ color:{P1}; }}
        div[data-testid="stForm"] {{ background:{CARD}; border:1px solid {BORDER}; border-radius:16px; padding:18px; }}
        .stButton > button, div[data-testid="stDownloadButton"] button, div[data-testid="stFormSubmitButton"] button {{
            background: linear-gradient(90deg, {P3}, {P1}); color:#111; border:0; border-radius:10px; font-weight:800; }}
        .stButton > button:hover, div[data-testid="stFormSubmitButton"] button:hover {{ filter:brightness(1.12); color:#000; }}
        div[data-testid="stMetric"] {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; padding:12px 16px; }}
        div[data-testid="stProgress"] > div > div > div {{ background-color:{P1}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
 
 
# ───────────────────────── Utilidades ─────────────────────────
def normalized(value):
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
 
 
def norm_cat(name):
    name = re.sub(r"\s+", " ", str(name or "")).strip().lower()
    return name[:1].upper() + name[1:] if name else ""
 
 
def parse_money(text):
    """Entiende '10.000', '10000', '$ 10.000', '10k', '1,5M', '10 mil'. Devuelve float o None."""
    if text is None:
        return None
    t = str(text).strip().lower().replace("$", "").replace(" ", "")
    if not t:
        return None
    mult = 1
    for suffix, m in (("mil", 1000), ("k", 1000), ("millones", 1_000_000), ("millon", 1_000_000), ("m", 1_000_000)):
        if t.endswith(suffix):
            t, mult = t[: -len(suffix)], m
            break
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+", t):
        t = t.replace(",", "")
    try:
        val = parse_amount(pd.Series([t])).iloc[0]
    except Exception:
        return None
    if pd.isna(val):
        return None
    return abs(float(val)) * mult
 
 
def fmt_input(value):
    return f"{int(round(value)):,}".replace(",", ".") if value else ""
 
 
def money_preview(text):
    """Muestra bajo el campo cómo se entendió el monto."""
    if text is None or not str(text).strip():
        st.caption("Escribe el monto con o sin puntos: 15000 o 15.000 (también 15k).")
        return
    v = parse_money(text)
    if v is None:
        st.caption("⚠️ No entendí ese monto. Prueba con 15.000")
    else:
        st.caption(f"💰 Entendí: **{cop(v)}**")
 
 
def logo_html():
    logo = BASE_DIR / "logo.png"
    if logo.exists():
        import base64
        b64 = base64.b64encode(logo.read_bytes()).decode()
        return f'<div style="text-align:center;padding:4px 0 14px"><img src="data:image/png;base64,{b64}" style="width:170px;border-radius:14px"></div>'
    return (f'<div class="brand"><img src="{LOGO_URL}"><div><div class="brand-title">OwlWallet</div>'
            f'<div class="brand-subtitle">FINANZAS PERSONALES</div></div></div>')
 
 
def cop(value):
    if value is None or pd.isna(value):
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}".replace(",", ".")
 
 
def month_label(key):
    y, m = key.split("-")
    return f"{MESES[int(m)].capitalize()} {y}"
 
 
def now_bogota():
    return pd.Timestamp.now(tz="America/Bogota").tz_localize(None)
 
 
def show_chart(fig):
    try:
        st.plotly_chart(fig, width="stretch")
    except Exception:
        st.plotly_chart(fig, use_container_width=True)
 
 
def show_df(df, **kwargs):
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kwargs)
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True, **kwargs)
 
 
def style_fig(fig, height=380, title=None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT),
        height=height,
        margin=dict(l=10, r=10, t=55 if title else 20, b=15),
        title=dict(text=title, font=dict(size=16, color=P6)) if title else None,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        colorway=PALETTE,
    )
    fig.update_layout(separators=",.")
    fig.update_xaxes(gridcolor="#2a2210", zerolinecolor="#2a2210")
    fig.update_yaxes(gridcolor="#2a2210", zerolinecolor="#2a2210")
    return fig
 
 
def kpi(label, value, detail="", danger=False):
    cls = "kpi-card danger" if danger else "kpi-card"
    st.markdown(
        f'<div class="{cls}"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>'
        f'<div class="kpi-detail">{detail}</div></div>',
        unsafe_allow_html=True,
    )
 
 
def section(title, subtitle=""):
    st.markdown(
        f'<div class="section-title">{title}</div><div class="section-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )
 
 
# ───────────────────────── Datos y persistencia ─────────────────────────
def clean_df(df):
    """Normaliza el DataFrame al esquema estándar."""
    df = df.copy()
    for c in COLS:
        if c not in df.columns:
            df[c] = None
    df = df[COLS]
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["Fecha"] = df["Fecha"].fillna(now_bogota().normalize()).dt.normalize()
    df["Tipo"] = df["Tipo"].where(df["Tipo"].isin(TIPOS), "Gasto")
    df["Categoría"] = df["Categoría"].astype(object).where(df["Categoría"].notna(), "Otros")
    df["Categoría"] = df["Categoría"].astype(str).map(norm_cat).replace({"": "Otros", "Nan": "Otros", "None": "Otros"})
    df["Descripción"] = df["Descripción"].astype(object).where(df["Descripción"].notna(), "")
    df["Descripción"] = df["Descripción"].astype(str).replace({"nan": "", "None": ""})
    df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0.0).abs().round(2).astype(float)
    return df.sort_values("Fecha", ascending=False).reset_index(drop=True)
 
 
def empty_df():
    return clean_df(pd.DataFrame(columns=COLS))
 
 
def load_data():
    if DATA_FILE.exists():
        try:
            return clean_df(pd.read_json(DATA_FILE, orient="records"))
        except Exception:
            pass
    return empty_df()
 
 
def save_data(df):
    try:
        out = df.copy()
        out["Fecha"] = out["Fecha"].dt.strftime("%Y-%m-%d")
        out.to_json(DATA_FILE, orient="records", force_ascii=False)
    except Exception:
        pass
 
 
def load_settings():
    base = {"budgets": {}, "limits": {}, "initial_balance": 0.0}
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            base["budgets"] = {str(k): float(v) for k, v in data.get("budgets", {}).items()}
            base["limits"] = {norm_cat(k): float(v) for k, v in data.get("limits", {}).items()}
            base["initial_balance"] = float(data.get("initial_balance", 0) or 0)
        except Exception:
            pass
    return base
 
 
def save_settings(settings):
    try:
        SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
 
 
def set_data(df):
    st.session_state["data"] = clean_df(df)
    save_data(st.session_state["data"])
 
 
def budget_for(settings, month_key):
    """Presupuesto del mes; si no existe, hereda el más reciente anterior."""
    budgets = settings["budgets"]
    if month_key in budgets:
        return budgets[month_key], True
    earlier = sorted(k for k in budgets if k < month_key)
    if earlier:
        return budgets[earlier[-1]], False
    return 0.0, False
 
 
# ───────────────────────── Importación ─────────────────────────
def parse_amount(series):
    text = series.astype(str).str.strip()
    text = text.str.replace(r"[\$€£₡%\s]", "", regex=True)
    text = text.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    both = text.str.contains(r"\.\,|\,\.", regex=True, na=False) | (
        text.str.contains(",", regex=False, na=False) & text.str.contains(".", regex=False, na=False)
    )
    comma_decimal = both & (text.str.rfind(",") > text.str.rfind("."))
    text.loc[comma_decimal] = text.loc[comma_decimal].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    text.loc[both & ~comma_decimal] = text.loc[both & ~comma_decimal].str.replace(",", "", regex=False)
    only_comma = ~both & text.str.contains(",", regex=False, na=False)
    text.loc[only_comma] = text.loc[only_comma].str.replace(",", ".", regex=False)
    only_dots = ~both & text.str.fullmatch(r"-?\d{1,3}(\.\d{3})+").fillna(False).astype(bool)
    text.loc[only_dots] = text.loc[only_dots].str.replace(".", "", regex=False)
    return pd.to_numeric(text, errors="coerce")
 
 
def guess_col(columns, terms, exclude=()):
    for col in columns:
        if col in exclude:
            continue
        name = normalized(col)
        if name in terms or any(t in name.split("_") for t in terms):
            return col
    return None
 
 
@st.cache_data(show_spinner=False, ttl=900)
def load_google_sheet(url):
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError("No se encontró un ID de Google Sheets en el enlace.")
    csv_url = f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?format=csv"
    return pd.read_csv(csv_url)
 
 
@st.cache_data(show_spinner=False)
def read_uploaded_file(file_bytes, sheet_name=0):
    return pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)
 
 
def map_to_schema(raw, col_fecha, col_monto, col_cat, col_desc, col_tipo, tipo_default):
    out = pd.DataFrame(index=raw.index)
    out["Fecha"] = pd.to_datetime(raw[col_fecha], errors="coerce", dayfirst=True) if col_fecha else pd.NaT
    monto = parse_amount(raw[col_monto]) if raw[col_monto].dtype == object or str(raw[col_monto].dtype).startswith("str") else pd.to_numeric(raw[col_monto], errors="coerce")
    out["Monto"] = monto
    out["Categoría"] = raw[col_cat].astype(str) if col_cat else "Otros"
    out["Descripción"] = raw[col_desc].astype(str) if col_desc else ""
    if col_tipo:
        t = raw[col_tipo].astype(str).map(normalized)
        out["Tipo"] = t.apply(lambda v: "Ingreso" if ("ingres" in v or "income" in v or "entrada" in v) else "Gasto")
    else:
        out["Tipo"] = tipo_default
    return out.dropna(subset=["Monto"])
 
 
def split_marked(edited):
    """Separa lo que se queda y lo que se borra según la casilla «Borrar»."""
    if "Borrar" not in edited.columns:
        return edited, edited.iloc[0:0]
    mark = edited["Borrar"].fillna(False).astype(bool)
    keep = edited[~mark].drop(columns=["Borrar"])
    gone = edited[mark].drop(columns=["Borrar"])
    return keep, gone
 
 
def drop_empty(df):
    """Quita filas sin monto (por ejemplo filas en blanco de la tabla)."""
    return df[pd.to_numeric(df["Monto"], errors="coerce").fillna(0) > 0]
 
 
def auto_import(raw):
    """Detecta columnas automáticamente y devuelve datos en el formato de la app (por defecto, gastos)."""
    cols = list(raw.columns)
    m = guess_col(cols, METRIC_TERMS)
    if m is None:
        nums = [c for c in cols if pd.api.types.is_numeric_dtype(raw[c])]
        m = nums[0] if nums else None
    if m is None:
        return empty_df()
    d = guess_col(cols, DATE_TERMS)
    if d is None:
        d = next((c for c in cols if pd.api.types.is_datetime64_any_dtype(raw[c])), None)
    c = guess_col(cols, CAT_TERMS, exclude=[m])
    x = guess_col(cols, DESC_TERMS, exclude=[m, c])
    t = guess_col(cols, TYPE_TERMS, exclude=[m, c, x])
    mapped = map_to_schema(raw, d, m, c, x, t, "Gasto")
    return clean_df(mapped) if not mapped.empty else empty_df()
 
 
# ───────────────────────── Cálculos ─────────────────────────
def month_slice(df, month_key):
    if df.empty:
        return df
    return df[df["Fecha"].dt.strftime("%Y-%m") == month_key]
 
 
def month_context(month_key):
    y, m = map(int, month_key.split("-"))
    days_in_month = calendar.monthrange(y, m)[1]
    today = now_bogota()
    if (today.year, today.month) == (y, m):
        day = today.day
        is_current = True
    elif (today.year, today.month) > (y, m):
        day, is_current = days_in_month, False
    else:
        day, is_current = 0, False
    return {"days": days_in_month, "day": day, "left": max(days_in_month - day, 0), "is_current": is_current}
 
 
def category_spend(month_df):
    spend = month_df[month_df["Tipo"] == "Gasto"].groupby("Categoría")["Monto"].sum()
    return spend.sort_values(ascending=False)
 
 
def build_alerts(month_df, month_key, settings):
    """Devuelve lista de alertas con sugerencias para corregir."""
    alerts = []
    ctx = month_context(month_key)
    spend = category_spend(month_df)
    gastos = month_df[month_df["Tipo"] == "Gasto"]
    limits = settings["limits"]
 
    for cat, limit in limits.items():
        spent = float(spend.get(cat, 0.0))
        if limit <= 0:
            continue
        pct = spent / limit
        if pct < 0.8:
            continue
        over = spent - limit
        tips = []
        if pct > 1:
            title = f"Superaste el límite de {cat}: gastaste {cop(spent)} de {cop(limit)} (te pasaste por {cop(over)})"
            level = "danger"
            top = gastos[gastos["Categoría"] == cat].sort_values("Monto", ascending=False).head(3)
            if not top.empty:
                items = ", ".join(f"{(r['Descripción'] or 'sin descripción')} ({cop(r['Monto'])})" for _, r in top.iterrows())
                tips.append(f"Tus gastos más grandes en {cat} fueron: {items}. Revisa si alguno era evitable o se puede recortar.")
            if ctx["left"] > 0:
                tips.append(f"No gastes más en {cat} durante los {ctx['left']} días que quedan del mes; así evitas ampliar el exceso.")
            slack = [(c, l - float(spend.get(c, 0.0))) for c, l in limits.items() if c != cat and l - float(spend.get(c, 0.0)) > 0]
            slack.sort(key=lambda x: -x[1])
            if slack:
                c2, s2 = slack[0]
                move = min(s2, over)
                tips.append(f"Puedes mover {cop(move)} del límite de {c2} (te sobran {cop(s2)}) para cubrir parte del exceso.")
            tips.append("Si el gasto era necesario, sube el límite de esta categoría para el próximo mes o recorta otra categoría para compensarlo.")
        else:
            left = limit - spent
            title = f"Cuidado con {cat}: ya usaste el {pct:.0%} de tu límite ({cop(spent)} de {cop(limit)})"
            level = "warn"
            if ctx["left"] > 0:
                tips.append(f"Te quedan {cop(left)} para {ctx['left']} días, unos {cop(left / ctx['left'])} por día.")
            else:
                tips.append(f"Te quedan {cop(left)} disponibles en esta categoría.")
            tips.append("Prioriza solo lo esencial en esta categoría hasta que cierre el mes.")
        alerts.append({"level": level, "title": title, "tips": tips, "cat": cat})
 
    budget, _ = budget_for(settings, month_key)
    total_spent = float(gastos["Monto"].sum()) if not gastos.empty else 0.0
    if budget > 0:
        pct = total_spent / budget
        if pct > 1:
            over = total_spent - budget
            tips = []
            if not spend.empty:
                top_cat, top_val = spend.index[0], spend.iloc[0]
                tips.append(f"Tu categoría más pesada es {top_cat} ({cop(top_val)}, {top_val / total_spent:.0%} del gasto). Empieza a recortar por ahí.")
            if ctx["left"] > 0:
                tips.append(f"Evita gastos no esenciales los {ctx['left']} días que quedan del mes.")
            tips.append(f"Para el próximo mes, intenta reducir al menos {cop(over)} o ajusta tu presupuesto a una cifra realista.")
            alerts.insert(0, {"level": "danger", "title": f"Superaste tu presupuesto mensual: {cop(total_spent)} de {cop(budget)} (exceso de {cop(over)})", "tips": tips, "cat": None})
        elif pct >= 0.8:
            left = budget - total_spent
            tips = [f"Te quedan {cop(left)} del presupuesto." + (f" Son unos {cop(left / ctx['left'])} por día durante {ctx['left']} días." if ctx["left"] > 0 else "")]
            alerts.insert(0, {"level": "warn", "title": f"Ya usaste el {pct:.0%} de tu presupuesto del mes", "tips": tips, "cat": None})
    return alerts
 
 
def render_alerts(alerts):
    for a in alerts:
        tips = "".join(f"<li>{t}</li>" for t in a["tips"])
        icon = "🚨" if a["level"] == "danger" else "⚠️"
        st.markdown(
            f'<div class="alert-box {a["level"]}"><h4>{icon} {a["title"]}</h4>'
            f'<div style="font-size:12.5px;color:{MUTED}">Cómo arreglarlo:</div><ul>{tips}</ul></div>',
            unsafe_allow_html=True,
        )
 
 
# ───────────────────────── Estado inicial ─────────────────────────
inject_css()
ss = st.session_state
 
if "data" not in ss:
    ss["data"] = load_data()
if "settings" not in ss:
    ss["settings"] = load_settings()
if "flash" not in ss:
    ss["flash"] = []
if "q_fecha" not in ss:
    ss["q_fecha"] = now_bogota().date()
 
data = ss["data"]
settings = ss["settings"]
 
 
# ───────────────────────── Acciones (callbacks) ─────────────────────────
def quick_add():
    amount = parse_money(ss.get("q_monto"))
    pick = ss.get("q_cat") or ""
    cat = norm_cat(ss.get("q_cat_new")) if pick.startswith("➕") else pick
    tipo = ss.get("q_tipo", "Gasto")
    if not amount or amount <= 0:
        ss["quick_msg"] = ("warn", "Escribe un monto válido, por ejemplo 15.000")
        return
    if not cat:
        ss["quick_msg"] = ("warn", "Escribe el nombre de la categoría.")
        return
    fecha = pd.Timestamp(ss.get("q_fecha") or now_bogota().date())
    row = pd.DataFrame([{"Fecha": fecha, "Tipo": tipo, "Categoría": cat, "Descripción": (ss.get("q_desc") or "").strip(), "Monto": amount}])
    set_data(pd.concat([ss["data"], row], ignore_index=True))
    ss["last_added"] = {"Fecha": fecha.normalize(), "Tipo": tipo, "Categoría": cat, "Descripción": (ss.get("q_desc") or "").strip(), "Monto": float(amount)}
    mk = fecha.strftime("%Y-%m")
    ss["pending_month"] = mk
    ss["quick_msg"] = ("ok", f"✅ {tipo} de {cop(amount)} en {cat} agregado.")
    if tipo == "Gasto":
        for al in build_alerts(month_slice(ss["data"], mk), mk, ss["settings"]):
            if al["cat"] in (cat, None):
                ss.setdefault("toasts", []).append((al["title"], "🚨" if al["level"] == "danger" else "⚠️"))
    ss["q_monto"] = ""
    ss["q_desc"] = ""
    ss["q_cat_new"] = ""
 
 
def undo_last():
    la = ss.get("last_added")
    d = ss["data"]
    if la:
        mask = ((d["Tipo"] == la["Tipo"]) & (d["Categoría"] == la["Categoría"]) & (d["Monto"] == la["Monto"])
                & (d["Descripción"] == la["Descripción"]) & (d["Fecha"] == la["Fecha"]))
        if mask.any():
            set_data(d.drop(index=d[mask].index[0]))
            ss["quick_msg"] = ("ok", "↩️ Se deshizo el último movimiento.")
        else:
            ss["quick_msg"] = ("warn", "Ese movimiento ya no está en la lista.")
    ss["last_added"] = None
 
 
def undo_delete():
    gone = ss.get("last_deleted")
    if gone is not None and not gone.empty:
        set_data(pd.concat([ss["data"], gone], ignore_index=True))
        ss["flash"].append(("ok", f"↩️ Se recuperaron {len(gone)} movimientos."))
    ss["last_deleted"] = None
 
 
def save_initial():
    amount = parse_money(ss.get("init_bal"))
    ss["settings"]["initial_balance"] = float(amount or 0.0)
    save_settings(ss["settings"])
    ss["flash"].append(("ok", f"Dinero inicial guardado: {cop(amount or 0)}"))
 
 
def save_budget(mk):
    amount = parse_money(ss.get(f"b_{mk}"))
    if not amount or amount <= 0:
        ss["flash"].append(("warn", "Escribe un presupuesto válido, por ejemplo 1.500.000"))
        return
    ss["settings"]["budgets"][mk] = amount
    save_settings(ss["settings"])
    ss["flash"].append(("ok", f"Presupuesto de {month_label(mk)} guardado: {cop(amount)}"))
 
 
def save_limit():
    amount = parse_money(ss.get("l_monto"))
    pick = ss.get("l_cat") or ""
    name = norm_cat(ss.get("l_cat_new")) if pick.startswith("➕") else pick
    if not name:
        ss["flash"].append(("warn", "Escribe el nombre de la categoría."))
        return
    if not amount or amount <= 0:
        ss["flash"].append(("warn", "Escribe un límite válido, por ejemplo 10.000"))
        return
    ss["settings"]["limits"][name] = amount
    save_settings(ss["settings"])
    ss["flash"].append(("ok", f"Límite de {name} guardado: {cop(amount)} al mes"))
    ss["l_monto"] = ""
    ss["l_cat_new"] = ""
 
 
def remove_limit(cat):
    ss["settings"]["limits"].pop(cat, None)
    save_settings(ss["settings"])
 
 
freq = data["Categoría"].value_counts().index.tolist() if not data.empty else []
all_categories = list(dict.fromkeys(list(settings["limits"].keys()) + freq + DEFAULT_CATEGORIES))
 
# ───────────────────────── Sidebar ─────────────────────────
current_key = now_bogota().strftime("%Y-%m")
month_keys = set([current_key])
if not data.empty:
    month_keys |= set(data["Fecha"].dt.strftime("%Y-%m").unique())
month_options = sorted(month_keys, reverse=True)
if "pending_month" in ss:
    ss["month_sel"] = ss.pop("pending_month")
if ss.get("month_sel") not in month_options:
    with_data = sorted(set(data["Fecha"].dt.strftime("%Y-%m"))) if not data.empty else []
    ss["month_sel"] = with_data[-1] if with_data else current_key
 
with st.sidebar:
    st.markdown(logo_html(), unsafe_allow_html=True)
 
    with st.expander("➕ Agregar gasto o ingreso", expanded=True):
        st.radio("Tipo", TIPOS, horizontal=True, key="q_tipo")
        st.selectbox("Categoría", all_categories + ["➕ Otra (escribir)"], key="q_cat")
        if str(ss.get("q_cat", "")).startswith("➕"):
            st.text_input("Nombre de la categoría nueva", key="q_cat_new", placeholder="Ej: Mascotas")
        st.text_input("Monto (COP)", key="q_monto", placeholder="Ej: 15.000")
        money_preview(ss.get("q_monto"))
        st.text_input("Descripción (opcional)", key="q_desc", placeholder="Ej: Almuerzo")
        st.date_input("Fecha", key="q_fecha")
        st.button("➕ Agregar", on_click=quick_add, key="q_btn")
        if "quick_msg" in ss:
            kind, text = ss["quick_msg"]
            (st.success if kind == "ok" else st.warning)(text)
        if ss.get("last_added"):
            st.button("↩️ Deshacer el último que agregué", on_click=undo_last, key="undo_btn")
 
    with st.expander("📥 Cargar Excel", expanded=False):
        st.caption("Sube tu Excel y se agrega solo a tus gastos.")
        up = st.file_uploader("Excel", type=["xlsx", "xls"], label_visibility="collapsed", key="sb_upload")
        if up is not None:
            sig = (up.name, up.size)
            if ss.get("last_import") != sig:
                try:
                    raw = read_uploaded_file(up.getvalue(), 0)
                    raw.columns = [str(c).strip() or f"Columna {i + 1}" for i, c in enumerate(raw.columns)]
                    new = auto_import(raw)
                    if new.empty:
                        st.error("No encontré una columna de montos en tu Excel.")
                    else:
                        set_data(pd.concat([ss["data"], new], ignore_index=True).drop_duplicates())
                        ss["last_import"] = sig
                        ss["pending_month"] = new["Fecha"].max().strftime("%Y-%m")
                        ss["flash"].append(("ok", f"Listo: se agregaron {len(new):,} movimientos desde «{up.name}»."))
                        st.rerun()
                except Exception as exc:
                    st.error(f"No se pudo leer el Excel: {exc}")
            else:
                st.success("Archivo cargado ✔")
 
    st.markdown("### 📅 Mes")
    month_key = st.selectbox("Mes", month_options, format_func=month_label, label_visibility="collapsed", key="month_sel")
    st.caption("Tus datos se guardan solos en esta app.")
 
month_df_all = month_slice(data, month_key)
month_df = month_df_all  # un solo origen de datos: todo suma lo mismo
 
# ───────────────────────── Encabezado ─────────────────────────
st.markdown(
    f'<div class="hero"><h1>Tu dinero, bajo control.</h1>'
    f'<p>Anota tus gastos, define un presupuesto y límites por categoría. '
    f'OwlWallet te avisa al instante cuando te pases y te dice cómo corregirlo.</p>'
    f'<div style="margin-top:14px"><span class="pill">📅 {month_label(month_key)}</span></div></div>',
    unsafe_allow_html=True,
)
 
with st.expander("❓ ¿Cómo funciona OwlWallet?", expanded=data.empty):
    st.markdown(
        """
**1. Anota un gasto:** en el menú de la izquierda, **➕ Agregar gasto o ingreso**. Escribe el monto como quieras (`15000` o `15.000`) y listo. También puedes subir tu Excel en **📥 Cargar Excel**.
 
**2. Define tu presupuesto:** en **🎯 Presupuesto y límites** pones cuánto quieres gastar en el mes y, si quieres, un tope por categoría (ej: Comida máximo `10.000`).
 
**3. Mira el estado:** arriba siempre ves cómo va tu presupuesto. Si te pasas de un tope, sale una **alerta roja** con consejos para arreglarlo.
 
**Editar o borrar:** pestaña **✏️ Movimientos**.
        """
    )
 
for kind, text in ss["flash"]:
    (st.error if kind == "danger" else st.warning if kind == "warn" else st.success)(text, icon="🚨" if kind == "danger" else "⚠️" if kind == "warn" else "✅")
ss["flash"] = []
for title, icon in ss.pop("toasts", []):
    st.toast(title, icon=icon)
 
# ───────────────────────── Estado del presupuesto (siempre visible) ─────────────────────────
budget, budget_is_set = budget_for(settings, month_key)
ctx = month_context(month_key)
gastos_all = month_df_all[month_df_all["Tipo"] == "Gasto"]
spent_all = float(gastos_all["Monto"].sum()) if not gastos_all.empty else 0.0
spend_all = category_spend(month_df_all)
 
all_ing = float(data.loc[data["Tipo"] == "Ingreso", "Monto"].sum()) if not data.empty else 0.0
all_gas = float(data.loc[data["Tipo"] == "Gasto", "Monto"].sum()) if not data.empty else 0.0
initial = float(settings.get("initial_balance", 0.0))
total_money = initial + all_ing - all_gas
 
top_a, top_b = st.columns([3, 2])
with top_a:
    if budget > 0:
        pct_b = spent_all / budget
        bar_color = DANGER if pct_b > 1 else P1
        left_txt = f"te quedan <b>{cop(budget - spent_all)}</b>" if pct_b <= 1 else f"te pasaste por <b>{cop(spent_all - budget)}</b>"
        st.markdown(
            f'<div class="kpi-card{" danger" if pct_b > 1 else ""}">'
            f'<div class="kpi-label">🎯 Presupuesto de {month_label(month_key)}</div>'
            f'<div style="font-size:15px;margin:8px 0 10px">Llevas <b>{cop(spent_all)}</b> de <b>{cop(budget)}</b> · {left_txt} ({pct_b:.0%})</div>'
            f'<div style="background:{CARD};border:1px solid {BORDER};border-radius:99px;height:12px;overflow:hidden">'
            f'<div style="width:{min(pct_b, 1) * 100:.0f}%;height:100%;background:{bar_color}"></div></div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("🎯 Aún no defines tu presupuesto de este mes. Hazlo en la pestaña **Presupuesto y límites**.")
with top_b:
    kpi("💼 Dinero total que tengo", cop(total_money),
        f"Inicial {cop(initial)} + ingresos {cop(all_ing)} − gastos {cop(all_gas)}", danger=total_money < 0)
 
if settings["limits"]:
    chips = []
    for cat, limit in settings["limits"].items():
        sp = float(spend_all.get(cat, 0.0))
        icon = "🚨" if sp > limit else "⚠️" if sp >= 0.8 * limit else "✅"
        chips.append(f'<span class="pill" style="margin:3px 6px 3px 0">{icon} {cat}: {cop(sp)} / {cop(limit)}</span>')
    st.markdown("".join(chips), unsafe_allow_html=True)
 
alerts = build_alerts(month_df_all, month_key, settings)
if alerts:
    render_alerts(alerts)
elif budget > 0 or settings["limits"]:
    st.markdown('<div class="alert-box ok"><h4>✅ Vas bien: estás dentro de tu presupuesto y tus límites.</h4></div>', unsafe_allow_html=True)
 
tab_panel, tab_budget, tab_moves, tab_io = st.tabs(
    ["📊 Panel", "🎯 Presupuesto y límites", "✏️ Movimientos", "📥 Excel y datos"]
)
 
# ═════════════════════ TAB: PANEL ═════════════════════
with tab_panel:
    gastos = month_df[month_df["Tipo"] == "Gasto"]
    ingresos = month_df[month_df["Tipo"] == "Ingreso"]
    total_gastos = float(gastos["Monto"].sum()) if not gastos.empty else 0.0
    total_ingresos = float(ingresos["Monto"].sum()) if not ingresos.empty else 0.0
    balance = total_ingresos - total_gastos
    available = budget - total_gastos
    over_budget = budget > 0 and total_gastos > budget
 
    section("Resumen del mes", "<b>Presupuesto:</b> lo que planeaste gastar · <b>Gastado:</b> lo que ya gastaste · <b>Disponible:</b> lo que todavía puedes gastar · <b>Ingresos:</b> lo que entró · <b>Balance:</b> ingresos menos gastos.")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi("Presupuesto del mes", cop(budget) if budget > 0 else "Sin definir", "Defínelo en la pestaña Presupuesto" if budget <= 0 else ("Definido para este mes" if budget_is_set else "Heredado del mes anterior"))
    with c2:
        kpi("Gastado", cop(total_gastos), f"{len(gastos)} gastos", danger=over_budget)
    with c3:
        if budget > 0:
            kpi("Disponible", cop(available), "Te pasaste del presupuesto" if over_budget else f"{(available / budget):.0%} del presupuesto", danger=over_budget)
        else:
            kpi("Disponible", "—", "Define un presupuesto")
    with c4:
        kpi("Ingresos", cop(total_ingresos), f"{len(ingresos)} ingresos")
    with c5:
        kpi("Balance", cop(balance), "Ingresos − gastos", danger=balance < 0)
 
    if month_df.empty:
        st.info("Este mes aún no tiene movimientos. Agrega el primero en el menú de la izquierda (➕ Agregar gasto o ingreso).")
    else:
        spend = category_spend(month_df)
        section("Gráficas", "Una mirada rápida a tu mes.")
        g1, g2 = st.columns(2)
        with g1:
            if not spend.empty:
                fig = go.Figure(go.Pie(labels=spend.index, values=spend.values, hole=0.55,
                                       marker=dict(colors=PALETTE, line=dict(color=BG, width=2)),
                                       textinfo="percent", hovertemplate="%{label}<br>$%{value:,.0f}<extra></extra>"))
                show_chart(style_fig(fig, 360, "En qué gastas"))
                st.caption("🟡 Cada color es una categoría. Mientras más grande el pedazo, más plata se fue ahí.")
            else:
                st.info("No hay gastos este mes.")
        with g2:
            if settings["limits"] or not spend.empty:
                cats = list(dict.fromkeys(list(spend.index) + list(settings["limits"].keys())))
                spent_vals = [float(spend.get(c, 0.0)) for c in cats]
                limit_vals = [settings["limits"].get(c) for c in cats]
                colors = [DANGER if (l and sv > l) else P1 for sv, l in zip(spent_vals, limit_vals)]
                fig = go.Figure()
                fig.add_trace(go.Bar(x=cats, y=spent_vals, name="Gastado", marker_color=colors, hovertemplate="%{x}<br>Gastado: $%{y:,.0f}<extra></extra>"))
                if settings["limits"]:
                    fig.add_trace(go.Scatter(x=cats, y=limit_vals, name="Límite", mode="markers",
                                             marker=dict(symbol="line-ew", size=26, line=dict(color="#fff", width=3)),
                                             hovertemplate="%{x}<br>Límite: $%{y:,.0f}<extra></extra>"))
                fig.update_yaxes(tickprefix="$", tickformat=",.0f")
                show_chart(style_fig(fig, 360, "Gastado vs límite"))
                st.caption("🟡 La barra es lo que has gastado; la raya blanca es tu límite. Si la barra se pone roja, te pasaste.")
 
        daily = gastos.groupby(gastos["Fecha"].dt.day)["Monto"].sum()
        days = list(range(1, ctx["days"] + 1))
        cum = daily.reindex(days, fill_value=0).cumsum()
        if ctx["is_current"]:
            cum = cum[cum.index <= ctx["day"]]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[int(d) for d in cum.index], y=[float(v) for v in cum.values], mode="lines", name="Gastado",
                                 line=dict(color=P1, width=3), fill="tozeroy", fillcolor="rgba(212,175,55,.18)",
                                 hovertemplate="Día %{x}<br>Llevas $%{y:,.0f}<extra></extra>"))
        if budget > 0:
            fig.add_trace(go.Scatter(x=days, y=[budget] * len(days), mode="lines", name="Presupuesto",
                                     line=dict(color=DANGER, width=2, dash="dash"),
                                     hovertemplate="Presupuesto: $%{y:,.0f}<extra></extra>"))
        fig.update_layout(xaxis_title="Día del mes")
        fig.update_xaxes(tickmode="linear", tick0=1, dtick=2, tickformat="d", range=[1, ctx["days"]])
        fig.update_yaxes(tickprefix="$", tickformat=",.0f")
        show_chart(style_fig(fig, 320, "Gasto acumulado del mes"))
        st.caption("🟡 La línea dorada suma tus gastos día a día. Si toca la línea roja punteada (tu presupuesto), ya lo agotaste.")
 
        if not gastos.empty:
            section("Estadísticas", "<b>Promedio diario:</b> cuánto gastas por día · <b>Proyección:</b> cuánto llevarás gastado a fin de mes si sigues igual · <b>Mayor gasto:</b> tu compra más grande.")
            top_move = gastos.sort_values("Monto", ascending=False).iloc[0]
            days_elapsed = ctx["day"] if ctx["day"] > 0 else ctx["days"]
            avg_day = total_gastos / max(days_elapsed, 1)
            projection = avg_day * ctx["days"] if ctx["is_current"] else total_gastos
            s1, s2, s3 = st.columns(3)
            with s1:
                kpi("Promedio diario", cop(avg_day))
            with s2:
                kpi("Proyección fin de mes", cop(projection), "Si sigues a este ritmo", danger=budget > 0 and projection > budget)
            with s3:
                kpi("Mayor gasto", cop(top_move["Monto"]), (top_move["Descripción"] or top_move["Categoría"])[:32])
 
# ═════════════════════ TAB: PRESUPUESTO ═════════════════════
with tab_budget:
    section("Dinero total que tengo", "La app suma todo: dinero inicial + todos tus ingresos − todos tus gastos (de todos los meses). Aquí pones el dinero con el que empiezas, si tienes.")
    if "init_bal" not in ss:
        ss["init_bal"] = fmt_input(initial)
    st.text_input("Dinero con el que empiezo (COP)", key="init_bal", placeholder="Ej: 2.000.000 (déjalo vacío si empiezas en cero)")
    money_preview(ss.get("init_bal"))
    st.button("Guardar dinero inicial", on_click=save_initial, key="save_initial")
    st.markdown(f"**Ahora tienes: {cop(total_money)}**")
 
    section(f"Presupuesto de {month_label(month_key)}", "Es el total que quieres gastar en el mes. Escríbelo con o sin puntos.")
    bkey = f"b_{month_key}"
    if bkey not in ss:
        ss[bkey] = fmt_input(budget)
    st.text_input("Presupuesto mensual (COP)", key=bkey, placeholder="Ej: 1.500.000")
    money_preview(ss.get(bkey))
    st.button("Guardar presupuesto", on_click=save_budget, args=(month_key,), key="save_budget")
    if budget > 0 and ctx["left"] > 0 and budget > spent_all:
        st.caption(f"Puedes gastar unos **{cop((budget - spent_all) / ctx['left'])} por día** durante los {ctx['left']} días que quedan.")
 
    section("Límites por categoría", "Un tope para una categoría. Ejemplo: Comida máximo 10.000. Si lo superas, te aviso al instante y te digo cómo corregirlo.")
    st.selectbox("Categoría", all_categories + ["➕ Otra (escribir)"], key="l_cat")
    if str(ss.get("l_cat", "")).startswith("➕"):
        st.text_input("Nombre de la categoría nueva", key="l_cat_new", placeholder="Ej: Mascotas")
    st.text_input("Límite mensual (COP)", key="l_monto", placeholder="Ej: 10.000")
    money_preview(ss.get("l_monto"))
    st.button("Guardar límite", on_click=save_limit, key="save_limit")
 
    if settings["limits"]:
        st.markdown("&nbsp;")
        for cat, limit in sorted(settings["limits"].items()):
            spent = float(spend_all.get(cat, 0.0))
            pct = spent / limit if limit else 0
            r1, r2, r3 = st.columns([5, 2, 1])
            with r1:
                icon = "🚨" if pct > 1 else "⚠️" if pct >= 0.8 else "🟡"
                st.markdown(f"**{icon} {cat}** · {cop(spent)} de {cop(limit)}")
                st.progress(min(pct, 1.0))
            with r2:
                if pct > 1:
                    st.error(f"Excedido por {cop(spent - limit)}")
                else:
                    st.caption(f"Disponible: {cop(limit - spent)}")
            with r3:
                st.button("Quitar", key=f"del_lim_{cat}", on_click=remove_limit, args=(cat,))
    else:
        st.info("Todavía no tienes límites. Crea uno arriba, por ejemplo Comida → 10.000.")
 
# ═════════════════════ TAB: MOVIMIENTOS ═════════════════════
with tab_moves:
    section("Editar, describir o eliminar", "<b>Para borrar:</b> marca la casilla «🗑 Borrar» de la fila que quieras quitar y presiona «Eliminar marcados». Puedes deshacerlo. <b>Para editar:</b> doble clic en una celda (ahí también va la descripción) y luego «Guardar cambios de la tabla».")
    view = ss["data"].copy()
    view["Fecha"] = view["Fecha"].dt.date
    view.insert(0, "Borrar", False)
    edited = st.data_editor(
        view,
        num_rows="dynamic",
        hide_index=True,
        key="editor",
        height=420,
        column_config={
            "Borrar": st.column_config.CheckboxColumn("🗑 Borrar", default=False, width="small"),
            "Fecha": st.column_config.DateColumn("Fecha", format="YYYY-MM-DD", required=True),
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=TIPOS, required=True),
            "Categoría": st.column_config.TextColumn("Categoría", required=True),
            "Descripción": st.column_config.TextColumn("Descripción", width="large"),
            "Monto": st.column_config.NumberColumn("Monto", format="localized", min_value=0, step=0.01, required=True),
        },
    )
    keep, gone = split_marked(edited)
    e1, e2 = st.columns(2)
    with e1:
        if st.button(f"🗑 Eliminar marcados ({len(gone)})", disabled=len(gone) == 0, key="del_marked"):
            ss["last_deleted"] = clean_df(gone)
            set_data(drop_empty(keep))
            ss["flash"].append(("ok", f"Se eliminaron {len(gone)} movimientos. Si fue un error, presiona «Deshacer»."))
            st.rerun()
    with e2:
        if st.button("💾 Guardar cambios de la tabla", key="save_table"):
            set_data(drop_empty(edited.drop(columns=["Borrar"])))
            ss["flash"].append(("ok", "Cambios guardados."))
            st.rerun()
    if ss.get("last_deleted") is not None and not ss["last_deleted"].empty:
        st.button(f"↩️ Deshacer eliminación ({len(ss['last_deleted'])})", on_click=undo_delete, key="undo_del")
    st.caption(f"{len(edited):,} movimientos en total. Las ediciones no se aplican hasta que presiones «Guardar cambios de la tabla».")
 
# ═════════════════════ TAB: IMPORTAR / EXPORTAR ═════════════════════
with tab_io:
    section("Cargar Excel o Google Sheets", "Sube tu archivo y presiona Importar. La app detecta las columnas sola.")
    source = st.radio("Fuente", ["Archivo Excel", "Google Sheets"], horizontal=True)
    raw = None
    if source == "Google Sheets":
        url = st.text_input("Enlace de Google Sheets (visible para quien tenga el enlace)", placeholder="https://docs.google.com/spreadsheets/d/ID/edit")
        if url:
            try:
                with st.spinner("Conectando con Google Sheets..."):
                    raw = load_google_sheet(url)
            except Exception as exc:
                st.error(f"No se pudo cargar Google Sheets: {exc}")
    else:
        uploaded = st.file_uploader("Sube tu Excel", type=["xlsx", "xls"])
        if uploaded is not None:
            fbytes = uploaded.getvalue()
            try:
                names = pd.ExcelFile(BytesIO(fbytes)).sheet_names
                sheet = st.selectbox("Hoja", names) if len(names) > 1 else names[0]
                raw = read_uploaded_file(fbytes, sheet)
            except Exception as exc:
                st.error(f"No se pudo leer el archivo: {exc}")
 
    if raw is not None and not raw.empty:
        raw = raw.copy()
        raw.columns = [str(c).strip() or f"Columna {i + 1}" for i, c in enumerate(raw.columns)]
        cols = list(raw.columns)
        none = "— ninguna —"
        guess_m = guess_col(cols, METRIC_TERMS)
        if guess_m is None:
            nums = [c for c in cols if pd.api.types.is_numeric_dtype(raw[c])]
            guess_m = nums[0] if nums else cols[0]
        guess_d = guess_col(cols, DATE_TERMS)
        if guess_d is None:
            for c in cols:
                if pd.api.types.is_datetime64_any_dtype(raw[c]):
                    guess_d = c
                    break
        guess_c = guess_col(cols, CAT_TERMS, exclude=[guess_m])
        guess_x = guess_col(cols, DESC_TERMS, exclude=[guess_m, guess_c])
        guess_t = guess_col(cols, TYPE_TERMS, exclude=[guess_m, guess_c, guess_x])
 
        st.success(f"Se leyeron {len(raw):,} filas.")
        show_df(raw.head(6))
        sel = {"monto": guess_m, "fecha": guess_d, "cat": guess_c, "desc": guess_x, "tipo": guess_t}
        with st.expander("Ajustar columnas (opcional)"):
            m1, m2 = st.columns(2)
            opts = [none] + cols
            with m1:
                sel["monto"] = st.selectbox("Monto", cols, index=cols.index(guess_m))
                sel["fecha"] = st.selectbox("Fecha", opts, index=opts.index(guess_d) if guess_d else 0)
                sel["cat"] = st.selectbox("Categoría", opts, index=opts.index(guess_c) if guess_c else 0)
            with m2:
                sel["desc"] = st.selectbox("Descripción", opts, index=opts.index(guess_x) if guess_x else 0)
                sel["tipo"] = st.selectbox("Tipo (Gasto/Ingreso)", opts, index=opts.index(guess_t) if guess_t else 0)
            tipo_def = st.radio("Si no hay columna de tipo, todo es:", TIPOS, horizontal=True)
        if "tipo_def" not in locals():
            tipo_def = "Gasto"
        mode = st.radio("¿Qué hago con lo que ya tienes?", ["Agregar", "Reemplazar todo"], horizontal=True)
        if st.button("📥 Importar"):
            try:
                pick = lambda v: None if v in (None, none) else v
                mapped = map_to_schema(raw, pick(sel["fecha"]), sel["monto"], pick(sel["cat"]), pick(sel["desc"]), pick(sel["tipo"]), tipo_def)
                if mapped.empty:
                    st.error("No encontré montos válidos. Abre «Ajustar columnas» y elige la columna correcta.")
                else:
                    new = clean_df(mapped)
                    set_data(new if mode.startswith("Reemplazar") else pd.concat([st.session_state["data"], new], ignore_index=True))
                    st.session_state["pending_month"] = new["Fecha"].max().strftime("%Y-%m")
                    st.session_state["flash"].append(("ok", f"Se importaron {len(new):,} movimientos."))
                    st.rerun()
            except Exception as exc:
                st.error(f"No se pudo importar: {exc}")
 
    section("Exportar")
    exp = st.session_state["data"].copy()
    x1, x2 = st.columns(2)
    with x1:
        try:
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                exp.to_excel(writer, index=False, sheet_name="Movimientos")
            st.download_button("⬇️ Descargar Excel", buf.getvalue(), "owlwallet_datos.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception:
            st.caption("Instala openpyxl para exportar a Excel.")
    with x2:
        if st.button("🗑 Borrar todos los datos"):
            st.session_state["confirm_wipe"] = True
    if st.session_state.get("confirm_wipe"):
        st.warning("Esto elimina todos tus movimientos. ¿Seguro?")
        w1, w2 = st.columns(2)
        with w1:
            if st.button("Sí, borrar todo"):
                set_data(empty_df())
                st.session_state["confirm_wipe"] = False
                st.rerun()
        with w2:
            if st.button("Cancelar"):
                st.session_state["confirm_wipe"] = False
                st.rerun()