import streamlit as st
import pandas as pd

def buscar_factura(row, fact_df, pagos_df):
    descripcion = str(row["Descripción"]) if pd.notnull(row["Descripción"]) else ""
    current_monto = row["Monto"]
    
    # Buscar facturas cuyo número aparezca en la descripción
    posibles_facturas = []
    for _, f in fact_df.iterrows():
        if str(f["Nro Factura"]) in descripcion:
            posibles_facturas.append(f)
    
    # Para cada factura posible, verificar si hay pagos que sumen el monto
    for factura in posibles_facturas:
        # Sumar todos los pagos no asignados que mencionen esta factura
        total_pagos = pagos_df[
            (pagos_df["Descripción"].str.contains(str(factura["Nro Factura"]), na=False) &
            (pagos_df["Factura Relacionada"].isna())
        ]["Monto"].sum()
        
        # Verificar si el pago actual completa el monto de la factura
        if abs(factura["Monto"] - (total_pagos + current_monto)) <= 0.02:
            return factura["Nro Factura"]
    
    return None

st.title("🤖 Conciliador de Facturas y Pagos Mejorado")

facturas_file = st.file_uploader("📄 Subí archivo de facturas (.xlsx)", type=["xlsx"])
pagos_file = st.file_uploader("🏦 Subí archivo de pagos (.xlsx o .csv)", type=["xlsx", "csv"])

if facturas_file and pagos_file:
    # Cargar los archivos
    facturas = pd.read_excel(facturas_file)
    pagos = pd.read_csv(pagos_file) if pagos_file.name.endswith(".csv") else pd.read_excel(pagos_file)
    
    # Ordenar pagos por monto descendente para procesar los más grandes primero
    pagos = pagos.sort_values("Monto", ascending=False)
    pagos["Factura Relacionada"] = None
    
    # Procesar cada pago
    for idx, row in pagos.iterrows():
        if pd.isna(row["Factura Relacionada"]):
            factura_num = buscar_factura(row, facturas, pagos)
            if factura_num:
                pagos.at[idx, "Factura Relacionada"] = factura_num
    
    # Determinar el estado de cada factura
    facturas["Estado"] = "PENDIENTE"
    for _, factura in facturas.iterrows():
        total_pagado = pagos[pagos["Factura Relacionada"] == factura["Nro Factura"]]["Monto"].sum()
        if abs(total_pagado - factura["Monto"]) <= 0.02:
            facturas.loc[facturas["Nro Factura"] == factura["Nro Factura"], "Estado"] = "PAGADA"
        elif total_pagado > 0:
            facturas.loc[facturas["Nro Factura"] == factura["Nro Factura"], "Estado"] = f"PARCIAL ({total_pagado:.2f}/{factura['Monto']:.2f})"
    
    # Mostrar resultados
    st.subheader("📋 Resultado: Facturas")
    st.dataframe(facturas)
    
    st.subheader("🏷️ Resultado: Pagos")
    st.dataframe(pagos)
    
    # Botones de descarga
    st.download_button(
        "⬇️ Descargar conciliación de facturas",
        facturas.to_csv(index=False, sep=";"),
        "facturas_conciliadas.csv",
        "text/csv"
    )
    st.download_button(
        "⬇️ Descargar conciliación de pagos",
        pagos.to_csv(index=False, sep=";"),
        "pagos_conciliados.csv",
        "text/csv"
    )
