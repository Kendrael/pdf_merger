import json
import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RUTA_CONFIG = os.path.join(BASE_DIR, "config.json")

def cargar_config():
    """Lee el archivo de configuración y retorna el diccionario."""
    with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_config(config):
    """Guarda el diccionario de configuración en el archivo."""
    with open(RUTA_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def obtener_centro_activo():
    """Retorna el diccionario del centro activo."""
    config = cargar_config()
    nombre_activo = config["centro_activo"]
    return config["centros"][nombre_activo]

def cambiar_centro(nombre_centro):
    """Cambia el centro activo en la configuración."""
    config = cargar_config()
    if nombre_centro in config["centros"]:
        config["centro_activo"] = nombre_centro
        guardar_config(config)
        return True
    return False

def listar_centros():
    """Retorna la lista de nombres de centros disponibles."""
    config = cargar_config()
    return list(config["centros"].keys())