# 🔍 Apollo Client Enrichment Tool

Herramienta para comparar tu base de datos de clientes contra Apollo.io y encontrar clientes factibles de telecomunicaciones.

## 🚀 Instalación Rápida

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar la app
```bash
streamlit run app.py
```

La app se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 🔑 Obtener tu Apollo API Key (Gratis)

1. Ve a [app.apollo.io](https://app.apollo.io) y crea una cuenta gratuita
2. Una vez dentro: **Settings → Integrations → API Keys**
3. Clic en **"Create New Key"**
4. Copia la key y pégala en la app

> 💡 El plan gratuito incluye acceso básico a la API. Tendrás créditos limitados,
> así que empieza probando con pocos registros.

## 📎 Formato del Excel

Tu archivo Excel o CSV debe tener al menos **una** de estas columnas:

| Columna           | Ejemplo              | Descripción                        |
|-------------------|----------------------|------------------------------------|
| Nombre de empresa | "Cemex", "BBVA"      | Nombre de la compañía              |
| Dominio/Sitio web | "cemex.com", "bbva.mx"| Dominio web (sin https://www.)    |

> **Tip:** Buscar por **dominio** es más preciso que por nombre.

## 📊 ¿Qué datos obtienes?

Para cada empresa encontrada en Apollo, obtienes:

- Industria y sub-industria
- Número de empleados estimado
- Ingresos anuales estimados
- Tecnologías que usan
- Ubicación (ciudad, estado, país)
- Teléfono corporativo
- LinkedIn de la empresa
- **Score de factibilidad telecom** (automático)

## 🎯 Score de Factibilidad Telecom

La app clasifica automáticamente cada empresa en:

- 🟢 **Alta Factibilidad** — Industria relevante, buen tamaño, usa tecnología
- 🟡 **Media Factibilidad** — Algunos indicadores positivos
- 🔴 **Baja Factibilidad** — Pocos indicadores de necesidad telecom

El score considera: industria, número de empleados, y cantidad de tecnologías que usa la empresa.

## 💰 Consumo de Créditos Apollo

Cada búsqueda (por dominio o nombre) consume **1 crédito** de Apollo.
El plan gratuito tiene créditos limitados, así que:

- Empieza con **10-25 registros** para probar
- Usa el control de "delay entre requests" para no exceder rate limits
- Exporta los resultados para no tener que repetir búsquedas

## 📁 Estructura del Proyecto

```
apollo_enrichment/
├── app.py              # Aplicación principal de Streamlit
├── requirements.txt    # Dependencias de Python
└── README.md           # Este archivo
```
