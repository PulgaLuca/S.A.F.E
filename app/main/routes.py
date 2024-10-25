from flask import render_template
import folium
from . import main

@main.route('/')
def index():
    # Crea una mappa centrata su una posizione specifica (latitudine e longitudine del centro della Terra)
    mappa = folium.Map(location=[0, 0], zoom_start=2)
    
    # Salva la mappa come HTML in una stringa
    mappa_html = mappa._repr_html_()

    return render_template('main/index.html', mappa_html=mappa_html)
