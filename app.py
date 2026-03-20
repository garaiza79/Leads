"""
🔍 Apollo Client Enrichment Tool
Compara tu base de datos de clientes contra Apollo.io
para encontrar clientes factibles de telecomunicaciones.

Autor: Generado con Claude para Flō Networks
"""

import streamlit as st
import pandas as pd
import requests
import time
import json
import os
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ─── Configuración de página ───────────────────────────────────────────────
st.set_page_config(
    page_title="Apollo Client Enrichment",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS personalizado ─────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Colores principales */
    :root {
        --primary: #6366f1;
        --success: #22c55e;
        --warning: #f59e0b;
        --danger: #ef4444;
        --bg-card: rgba(255,255,255,0.05);
    }
    
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .metric-card {
        background: var(--bg-card);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
    }
    
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.7;
        margin-top: 0.3rem;
    }
    
    .status-found { color: #22c55e; }
    .status-not-found { color: #ef4444; }
    .status-partial { color: #f59e0b; }
    
    .telecom-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .telecom-yes {
        background: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .telecom-maybe {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .telecom-no {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    div[data-testid="stSidebar"] {
        padding-top: 1rem;
    }
    
    .step-box {
        background: rgba(99, 102, 241, 0.08);
        border-left: 3px solid #6366f1;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── Funciones de Apollo API ───────────────────────────────────────────────

def enrich_organization(domain: str, api_key: str) -> dict:
    """Enriquece una organización usando el dominio."""
    url = "https://api.apollo.io/api/v1/organizations/enrich"
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "x-api-key": api_key,
    }
    params = {"domain": domain}
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            org = data.get("organization", {})
            if org:
                return {
                    "status": "found",
                    "name": org.get("name", ""),
                    "domain": org.get("primary_domain", domain),
                    "industry": org.get("industry", "N/A"),
                    "sub_industry": org.get("subindustry", "N/A"),
                    "keywords": ", ".join(org.get("keywords", [])[:5]),
                    "employees": org.get("estimated_num_employees", "N/A"),
                    "revenue": org.get("annual_revenue_printed", "N/A"),
                    "city": org.get("city", "N/A"),
                    "state": org.get("state", "N/A"),
                    "country": org.get("country", "N/A"),
                    "phone": org.get("phone", "N/A"),
                    "linkedin_url": org.get("linkedin_url", "N/A"),
                    "founded_year": org.get("founded_year", "N/A"),
                    "technologies": ", ".join(org.get("technology_names", [])[:8]),
                    "raw": org,
                }
            else:
                return {"status": "not_found", "domain": domain}
        elif resp.status_code == 401:
            return {"status": "error", "domain": domain, "error": "API Key inválida"}
        elif resp.status_code == 429:
            return {"status": "rate_limit", "domain": domain, "error": "Límite de requests alcanzado, espera un momento"}
        else:
            return {"status": "error", "domain": domain, "error": f"HTTP {resp.status_code}"}
    except requests.exceptions.Timeout:
        return {"status": "error", "domain": domain, "error": "Timeout - el servidor tardó demasiado"}
    except Exception as e:
        return {"status": "error", "domain": domain, "error": str(e)}


def search_organization(name: str, api_key: str) -> dict:
    """Busca una organización por nombre."""
    url = "https://api.apollo.io/api/v1/mixed_companies/search"
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "x-api-key": api_key,
    }
    payload = {
        "q_organization_name": name,
        "page": 1,
        "per_page": 1,
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            accounts = data.get("accounts", [])
            if accounts:
                org = accounts[0]
                return {
                    "status": "found",
                    "name": org.get("name", ""),
                    "domain": org.get("domain", "N/A"),
                    "industry": org.get("industry", "N/A"),
                    "sub_industry": org.get("subindustry", "N/A"),
                    "keywords": ", ".join(org.get("keywords", [])[:5]) if org.get("keywords") else "N/A",
                    "employees": org.get("estimated_num_employees", "N/A"),
                    "revenue": org.get("annual_revenue_printed", "N/A"),
                    "city": org.get("city", "N/A"),
                    "state": org.get("state", "N/A"),
                    "country": org.get("country", "N/A"),
                    "phone": org.get("phone", "N/A"),
                    "linkedin_url": org.get("linkedin_url", "N/A"),
                    "founded_year": org.get("founded_year", "N/A"),
                    "technologies": ", ".join(org.get("technology_names", [])[:8]) if org.get("technology_names") else "N/A",
                    "raw": org,
                }
            else:
                return {"status": "not_found", "name": name}
        elif resp.status_code == 401:
            return {"status": "error", "name": name, "error": "API Key inválida"}
        elif resp.status_code == 429:
            return {"status": "rate_limit", "name": name, "error": "Rate limit"}
        else:
            return {"status": "error", "name": name, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "name": name, "error": str(e)}


def classify_telecom_fit(result: dict) -> str:
    """Clasifica si una empresa es buen candidato para telecomunicaciones."""
    if result.get("status") != "found":
        return "unknown"
    
    # Keywords que indican buen fit para telecom
    telecom_positive = [
        "technology", "tech", "software", "saas", "cloud", "data center",
        "internet", "it services", "information technology", "telecommunications",
        "computer", "digital", "hosting", "network", "enterprise", "fintech",
        "manufacturing", "logistics", "healthcare", "hospital", "education",
        "university", "government", "retail", "banking", "finance", "insurance",
        "media", "real estate", "construction", "energy", "mining",
        "oil", "gas", "pharmaceutical", "automotive",
    ]
    
    # Indicadores de tamaño suficiente
    employees = result.get("employees", 0)
    if isinstance(employees, str):
        try:
            employees = int(employees.replace(",", ""))
        except (ValueError, AttributeError):
            employees = 0
    
    industry = str(result.get("industry", "")).lower()
    sub_industry = str(result.get("sub_industry", "")).lower()
    keywords = str(result.get("keywords", "")).lower()
    technologies = str(result.get("technologies", "")).lower()
    combined = f"{industry} {sub_industry} {keywords} {technologies}"
    
    score = 0
    
    # Industria relevante
    for kw in telecom_positive:
        if kw in combined:
            score += 1
    
    # Tamaño de empresa
    if employees >= 200:
        score += 3
    elif employees >= 50:
        score += 2
    elif employees >= 10:
        score += 1
    
    # Usa muchas tecnologías (indica madurez digital)
    tech_count = len(result.get("technologies", "").split(","))
    if tech_count >= 5:
        score += 2
    elif tech_count >= 2:
        score += 1
    
    if score >= 5:
        return "high"
    elif score >= 2:
        return "medium"
    else:
        return "low"


def telecom_badge(fit: str) -> str:
    """Retorna HTML badge para el nivel de fit."""
    labels = {
        "high": ("Alta Factibilidad", "telecom-yes"),
        "medium": ("Media Factibilidad", "telecom-maybe"),
        "low": ("Baja Factibilidad", "telecom-no"),
        "unknown": ("Sin Datos", "telecom-no"),
    }
    label, css_class = labels.get(fit, ("?", "telecom-no"))
    return f'<span class="telecom-badge {css_class}">{label}</span>'


# ─── Sidebar ───────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    
    # Buscar API key en este orden:
    # 1. Streamlit Cloud Secrets (para deploy en streamlit.io)
    # 2. Variable de entorno / .env (para uso local)
    # 3. Input manual (fallback)
    
    env_key = ""
    key_source = ""
    
    # Opción 1: Streamlit Secrets (para Streamlit Cloud)
    try:
        env_key = st.secrets["APOLLO_API_KEY"]
        key_source = "Streamlit Secrets"
    except (KeyError, FileNotFoundError):
        pass
    
    # Opción 2: Variable de entorno / .env (para local)
    if not env_key:
        env_key = os.getenv("APOLLO_API_KEY", "")
        if env_key:
            key_source = "archivo .env"
    
    if env_key:
        api_key = env_key
        st.success(f"🔑 API Key cargada desde {key_source}")
        if st.checkbox("Mostrar/cambiar API Key"):
            custom_key = st.text_input(
                "API Key",
                value=env_key,
                type="password",
            )
            if custom_key != env_key:
                api_key = custom_key
    else:
        api_key = st.text_input(
            "🔑 Apollo API Key",
            type="password",
            help="Tu API key de Apollo.io",
            placeholder="Pega tu API key aquí..."
        )
        with st.expander("📖 ¿Cómo obtener tu API Key?", expanded=True):
            st.markdown("""
<div class="step-box">
<strong>Paso 1:</strong> Ve a <a href="https://app.apollo.io" target="_blank">app.apollo.io</a> y crea una cuenta (gratis)
</div>
<div class="step-box">
<strong>Paso 2:</strong> Una vez dentro, ve a <strong>Settings → Integrations → API Keys</strong>
</div>
<div class="step-box">
<strong>Paso 3:</strong> Clic en <strong>"Create New Key"</strong> y copia la key generada
</div>
<div class="step-box">
<strong>Paso 4:</strong> Crea un archivo <code>.env</code> junto a <code>app.py</code> con:<br>
<code>APOLLO_API_KEY=tu_key_aqui</code>
</div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 📊 Opciones de Búsqueda")
    
    search_method = st.radio(
        "Método de búsqueda principal:",
        ["🌐 Por Dominio (recomendado)", "🏢 Por Nombre de Empresa"],
        help="Buscar por dominio es más preciso"
    )
    
    delay_seconds = st.slider(
        "⏱️ Delay entre requests (seg)",
        min_value=0.5,
        max_value=5.0,
        value=1.0,
        step=0.5,
        help="Para no exceder el rate limit de Apollo"
    )
    
    st.divider()
    st.markdown("### 📋 Formato del Excel")
    st.markdown("""
    Tu archivo debe tener al menos una de estas columnas:
    - **Nombre de empresa** (o similar)
    - **Dominio / Sitio Web** (ej: empresa.com)
    
    La app detectará las columnas automáticamente.
    """)


# ─── Contenido Principal ──────────────────────────────────────────────────

st.markdown('<p class="main-header">🔍 Apollo Client Enrichment</p>', unsafe_allow_html=True)
st.markdown("Compara tu base de clientes contra Apollo.io para identificar clientes factibles de telecomunicaciones.")
st.markdown("---")

# ─── Upload de archivo ─────────────────────────────────────────────────────

uploaded_file = st.file_uploader(
    "📎 Sube tu archivo Excel o CSV con la lista de clientes",
    type=["xlsx", "xls", "csv"],
    help="Debe contener columnas de nombre de empresa y/o dominio web"
)

if uploaded_file:
    # Leer archivo
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ Archivo cargado: **{uploaded_file.name}** — {len(df)} registros, {len(df.columns)} columnas")
        
        # Mostrar preview
        with st.expander("👀 Vista previa de los datos", expanded=True):
            st.dataframe(df.head(10), use_container_width=True)
        
        # ─── Mapeo de columnas ─────────────────────────────────────────
        st.markdown("### 🗂️ Mapeo de Columnas")
        st.markdown("Selecciona cuál columna corresponde a cada campo:")
        
        cols = ["— No disponible —"] + list(df.columns)
        
        col1, col2 = st.columns(2)
        with col1:
            company_col = st.selectbox("🏢 Columna de Nombre de Empresa", cols, index=0)
        with col2:
            domain_col = st.selectbox("🌐 Columna de Dominio/Sitio Web", cols, index=0)
        
        # Validar que al menos uno está seleccionado
        has_company = company_col != "— No disponible —"
        has_domain = domain_col != "— No disponible —"
        
        if not has_company and not has_domain:
            st.warning("⚠️ Selecciona al menos una columna (empresa o dominio) para continuar.")
        
        elif not api_key:
            st.warning("⚠️ Ingresa tu Apollo API Key en la barra lateral para iniciar la búsqueda.")
        
        else:
            # ─── Botón de ejecución ────────────────────────────────────
            use_domain = "Dominio" in search_method
            
            # Determinar cuántos registros procesar
            total_records = len(df)
            max_records = st.slider(
                "🔢 ¿Cuántos registros procesar?",
                min_value=1,
                max_value=min(total_records, 500),
                value=min(total_records, 25),
                help="Empieza con pocos para probar. Cada registro consume 1 crédito de Apollo."
            )
            
            st.info(f"💰 Esto consumirá aproximadamente **{max_records} créditos** de Apollo.")
            
            if st.button("🚀 Iniciar Enriquecimiento", type="primary", use_container_width=True):
                
                results = []
                progress_bar = st.progress(0, text="Preparando...")
                status_text = st.empty()
                
                subset = df.head(max_records).copy()
                
                for idx, row in subset.iterrows():
                    i = len(results)
                    pct = (i + 1) / max_records
                    
                    # Obtener identificador de la empresa
                    company_name = str(row[company_col]).strip() if has_company else ""
                    domain = str(row[domain_col]).strip() if has_domain else ""
                    
                    # Limpiar dominio (quitar http://, https://, www.)
                    if domain:
                        domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
                    
                    display_name = company_name or domain or f"Registro {i+1}"
                    progress_bar.progress(pct, text=f"Buscando: {display_name} ({i+1}/{max_records})")
                    
                    # Hacer la búsqueda
                    result = None
                    if use_domain and domain and domain != "nan":
                        result = enrich_organization(domain, api_key)
                    
                    # Si no se encontró por dominio, intentar por nombre
                    if (result is None or result.get("status") == "not_found") and company_name and company_name != "nan":
                        result = search_organization(company_name, api_key)
                    
                    # Si no hay resultado
                    if result is None:
                        result = {"status": "not_found"}
                    
                    # Agregar datos originales
                    result["original_company"] = company_name
                    result["original_domain"] = domain
                    result["telecom_fit"] = classify_telecom_fit(result)
                    
                    results.append(result)
                    
                    # Check for errors
                    if result.get("status") == "error" and "API Key inválida" in result.get("error", ""):
                        st.error("❌ API Key inválida. Verifica tu key en la barra lateral.")
                        break
                    
                    if result.get("status") == "rate_limit":
                        status_text.warning("⏳ Rate limit alcanzado, esperando 10 segundos...")
                        time.sleep(10)
                    else:
                        time.sleep(delay_seconds)
                
                progress_bar.progress(1.0, text="✅ ¡Completado!")
                
                # ─── Guardar resultados en session_state ───────────────
                st.session_state["results"] = results
    
    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {str(e)}")


# ─── Mostrar Resultados ───────────────────────────────────────────────────

if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    
    st.markdown("---")
    st.markdown("## 📊 Resultados del Enriquecimiento")
    
    # Métricas resumen
    total = len(results)
    found = sum(1 for r in results if r.get("status") == "found")
    not_found = sum(1 for r in results if r.get("status") == "not_found")
    errors = sum(1 for r in results if r.get("status") == "error")
    
    high_fit = sum(1 for r in results if r.get("telecom_fit") == "high")
    medium_fit = sum(1 for r in results if r.get("telecom_fit") == "medium")
    low_fit = sum(1 for r in results if r.get("telecom_fit") == "low")
    
    # Cards de métricas
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.metric("Total Procesados", total)
    with mc2:
        st.metric("Encontrados en Apollo", found, delta=f"{found/total*100:.0f}%" if total > 0 else "0%")
    with mc3:
        st.metric("No Encontrados", not_found)
    with mc4:
        st.metric("Errores", errors)
    
    st.markdown("")
    
    # Cards de factibilidad telecom
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value status-found">{high_fit}</div>
            <div class="metric-label">🟢 Alta Factibilidad Telecom</div>
        </div>
        """, unsafe_allow_html=True)
    with fc2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value status-partial">{medium_fit}</div>
            <div class="metric-label">🟡 Media Factibilidad Telecom</div>
        </div>
        """, unsafe_allow_html=True)
    with fc3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value status-not-found">{low_fit}</div>
            <div class="metric-label">🔴 Baja Factibilidad Telecom</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # ─── Tabla de resultados ───────────────────────────────────────────
    st.markdown("### 📋 Detalle por Empresa")
    
    # Filtro por factibilidad
    filter_col1, filter_col2 = st.columns([1, 3])
    with filter_col1:
        fit_filter = st.multiselect(
            "Filtrar por factibilidad:",
            ["high", "medium", "low", "unknown"],
            default=["high", "medium", "low", "unknown"],
            format_func=lambda x: {"high": "🟢 Alta", "medium": "🟡 Media", "low": "🔴 Baja", "unknown": "⚪ Sin datos"}[x]
        )
    
    # Construir DataFrame de resultados
    rows = []
    for r in results:
        if r.get("telecom_fit") not in fit_filter:
            continue
        rows.append({
            "Cliente Original": r.get("original_company", ""),
            "Dominio Original": r.get("original_domain", ""),
            "Status": "✅ Encontrado" if r.get("status") == "found" else "❌ No encontrado" if r.get("status") == "not_found" else f"⚠️ {r.get('error', 'Error')}",
            "Nombre en Apollo": r.get("name", ""),
            "Industria": r.get("industry", ""),
            "Sub-industria": r.get("sub_industry", ""),
            "Empleados": r.get("employees", ""),
            "Ingresos": r.get("revenue", ""),
            "Ciudad": r.get("city", ""),
            "País": r.get("country", ""),
            "Teléfono": r.get("phone", ""),
            "Tecnologías": r.get("technologies", ""),
            "LinkedIn": r.get("linkedin_url", ""),
            "Factibilidad Telecom": r.get("telecom_fit", "unknown"),
        })
    
    df_results = pd.DataFrame(rows)
    
    if not df_results.empty:
        # Ordenar: high primero, luego medium, etc.
        fit_order = {"high": 0, "medium": 1, "low": 2, "unknown": 3}
        df_results["_sort"] = df_results["Factibilidad Telecom"].map(fit_order)
        df_results = df_results.sort_values("_sort").drop(columns=["_sort"])
        
        # Reemplazar labels
        df_results["Factibilidad Telecom"] = df_results["Factibilidad Telecom"].map({
            "high": "🟢 Alta",
            "medium": "🟡 Media",
            "low": "🔴 Baja",
            "unknown": "⚪ Sin datos",
        })
        
        st.dataframe(
            df_results,
            use_container_width=True,
            height=400,
            column_config={
                "LinkedIn": st.column_config.LinkColumn("LinkedIn"),
            }
        )
        
        # ─── Exportar resultados ───────────────────────────────────────
        st.markdown("### 💾 Exportar Resultados")
        
        exp1, exp2 = st.columns(2)
        
        with exp1:
            # Excel
            buffer = BytesIO()
            df_results.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)
            st.download_button(
                "📥 Descargar Excel",
                data=buffer,
                file_name=f"apollo_enrichment_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        
        with exp2:
            # CSV
            csv_data = df_results.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Descargar CSV",
                data=csv_data,
                file_name=f"apollo_enrichment_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("No hay resultados que mostrar con los filtros seleccionados.")

else:
    # Estado vacío - mostrar instrucciones
    if not uploaded_file:
        st.markdown("")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 2rem;">📎</div>
                <div class="metric-label"><strong>Paso 1</strong><br>Sube tu Excel de clientes</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 2rem;">🔑</div>
                <div class="metric-label"><strong>Paso 2</strong><br>Configura tu API Key de Apollo</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 2rem;">🚀</div>
                <div class="metric-label"><strong>Paso 3</strong><br>Ejecuta el enriquecimiento</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        st.markdown("### 💡 ¿Qué hace esta herramienta?")
        st.markdown("""
        Esta app toma tu lista de clientes (Excel/CSV) y la cruza contra la base de datos de **Apollo.io** para obtener información enriquecida sobre cada empresa:
        
        - **Industria y sub-industria** — Para saber si son relevantes para telecomunicaciones
        - **Tamaño de empresa** — Número de empleados e ingresos estimados
        - **Tecnologías que usan** — Indicador de madurez digital
        - **Ubicación** — Ciudad y país
        - **Datos de contacto** — Teléfono corporativo y LinkedIn
        - **Score de factibilidad telecom** — Clasificación automática de qué tan buen candidato es para servicios de telecomunicaciones
        """)


# ─── Footer ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align: center; opacity: 0.5; font-size: 0.8rem;">'
    '🔍 Apollo Client Enrichment Tool — Flō Networks'
    '</div>',
    unsafe_allow_html=True,
)
