#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 18:21:48 2026

@author: lucho
"""

# =========================================================================== #

import os
import h5py
import datetime
import numpy as np
import urllib.request
from pathlib import Path
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature

logo_path = Path('./smn_logo.png')
smn_logo = mpimg.imread(logo_path) if logo_path.exists() else None

# =========================================================================== #

# Configuración inicial de la página
st.set_page_config(
                   page_title="Monitor de Tormentas ENGLN - Argentina", 
                   layout="wide"
                  )
st.image("smn_horizontal_arg-01.jpg", width=400) # Ajusta el ancho según prefieras

# =========================================================================== #

@st.cache_data(show_spinner=False)
def descargar_datos(fecha_str, anio) :
    
    """Descarga el archivo HDF5 simulando ser un navegador web para evitar bloqueos."""
    
    url = f"http://thunderhours.earthnetworks.com/data/{anio}/thunderhours_{fecha_str}.hdf5"
    archivo_local = f"thunderhours_{fecha_str}.hdf5"
    
    if not os.path.exists(archivo_local):
        try:
            # Creamos una petición con un User-Agent falso (simulando Google Chrome en Windows)
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            )
            
            # Abrimos la URL con un límite de tiempo (timeout) y guardamos el archivo
            with urllib.request.urlopen(req, timeout=15) as respuesta, open(archivo_local, 'wb') as archivo_salida:
                archivo_salida.write(respuesta.read())
                
        except Exception as e:
            return None, str(e)
            
    return archivo_local, None

# =========================================================================== #

@st.cache_data(show_spinner=False)
def procesar_datos(archivo_local) :
    
    """Abre el archivo HDF5, extrae coordenadas y suma las 24 matrices horarias."""
    
    try:
        f = h5py.File(archivo_local, 'r')
        lats = f.attrs['edges_latitude']
        lons = f.attrs['edges_longitude']
        
        # Inicializar matriz para sumar las 24 horas
        thCounts = np.zeros([len(lats)-1, len(lons)-1])
        
        for i in range(24):
            thCounts += f[f'{i:02d}UT']
            
        f.close()
        return lons, lats, thCounts, None
    except Exception as e:
        return None, None, None, str(e)

# =========================================================================== #

def graficar_mapa_argentina(lons, lats, thCounts, fecha_str) :
    
    """Genera la figura de Matplotlib/Cartopy centrada en Argentina."""
    
    fig = plt.figure(figsize=(6, 10))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    
    # Límites aproximados de Argentina
    ax.set_extent([-74.0, -53.0, -56.0, -21.0], crs=ccrs.PlateCarree())
    
    # Reemplazar los valores 0 por np.nan para que sean transparentes
    thCounts_grafico = np.where(thCounts == 0, np.nan, thCounts)
    
    # 1. Crear un mapa de colores discreto de exactamente 24 colores
    cmap_discreto = plt.get_cmap('gist_ncar', 24)
    
    # 2. Definir los límites de cada bloque de color (de 0 a 24, saltando de 1 en 1)
    norm = mcolors.BoundaryNorm(np.arange(0, 25), cmap_discreto.N)
    
    # Generar el mapa usando el colormap discreto y la normalización
    img = ax.pcolormesh(
                        lons, lats, thCounts_grafico, 
                        cmap=cmap_discreto, norm=norm, transform=ccrs.PlateCarree()
                       )
    
    # Capas cartográficas
    ax.add_feature(cfeature.BORDERS, linewidth=1.5, edgecolor='black')
    ax.add_feature(cfeature.COASTLINE, linewidth=1.0, edgecolor='black')
    ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor='gray')
    
    # 3. Configurar la barra de color con marcas (ticks) cada 2 horas arrancando de 0
    marcas_colorbar = np.arange(0, 25, 2)
    cbar = plt.colorbar(
                        img, pad=0.02, aspect=40, shrink=0.6, 
                        label='Horas Acumuladas con Tormenta',
                        ticks=marcas_colorbar
                       )
    
    plt.title(f'Horas de Tormenta en Argentina - {fecha_str}', fontsize=12)
    
    return fig

# =========================================================================== #

# --- Interfaz de Streamlit ---
# st.title("⚡ Horas de Tormenta en Argentina")
# st.markdown("Visualizador de datos del repositorio global de **Earth Networks**.")

st.markdown('<h1 style="margin-top: -12px; color: #242C4F; ">⛈️ Horas de Tormenta en Argentina | Dashboard Interactivo</h1>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 20px; color: #0090D0; ">Dirección de Productos de Modelación Ambiental y de Sensores Remotos - DNCIPS</p>', unsafe_allow_html=True)


# Selector de fecha
fecha_seleccionada = st.date_input(
                                   "Selecciona una fecha:",
                                    datetime.date(2024, 3, 19), # Fecha por defecto sugerida en el código original
                                    min_value=datetime.date(2014, 1, 1),
                                    max_value=datetime.date.today()
                                  )

if st.button("Generar Mapa") :
    
    fecha_str = fecha_seleccionada.strftime("%Y%m%d")
    anio = fecha_seleccionada.strftime("%Y")
    
    with st.spinner('Descargando y procesando datos (esto puede tomar unos segundos)...') :
        
        # 1. Descarga
        archivo_local, error_descarga = descargar_datos(fecha_str, anio)
        
        if error_descarga :
            st.error(f"No se pudieron descargar los datos para esta fecha. Detalle: {error_descarga}")
        else :
            
            # 2. Procesamiento
            lons, lats, thCounts, error_proceso = procesar_datos(archivo_local)
            
            if error_proceso :
                st.error(f"Error procesando el archivo: {error_proceso}")
            else :
                
                # 3. Visualización
                figura = graficar_mapa_argentina(lons, lats, thCounts, fecha_str)
                st.pyplot(figura)
                
                # Opcional: mostrar un resumen estadístico básico
                max_horas = int(np.max(thCounts))
                if max_horas == 0 :
                    st.info("No se registraron horas con tormenta a nivel global para esta fecha.")
                else :
                    st.success(f"Mapa generado con éxito. El valor máximo detectado globalmente fue de {max_horas} horas de tormenta.")
                    
# =========================================================================== #
