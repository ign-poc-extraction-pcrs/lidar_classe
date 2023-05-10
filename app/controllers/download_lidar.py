from flask import Blueprint, send_file, jsonify
from distutils import extension
import json
from io import BytesIO
from zipfile import ZipFile
import os
from pathlib import Path
import urllib.request

from app.utils.create_shp import create_shp_file
from app.utils.dalle_lidar_classe import BLOCS

download_lidar = Blueprint('download_lidar', __name__, url_prefix='/download/lidar')

KEY_JSON_LIDAR = "key_lidar"
PATH_KEY = Path(__file__).parent / "../../config.json"
BLOCS = BLOCS

@download_lidar.route('/shp', methods=['GET', 'POST'])
def download_shp():
    # path and file du shp
    PATH_SHP = "/tmp/api_dispo_produit_tmp_file"
    file_shp = "TA_diff_pkk_lidarhd"
    path_prj = Path(__file__).parent / "../static/files/TA_diff_pkk_lidarhd.prj"

    # recuperation des paquets lidar
    create_shp_lidar(PATH_SHP, file_shp)  
    # chemin absolue du shp
    file = f"{PATH_SHP}/{file_shp}"
    # les extensions du shp
    extensions = ["dbf", "shp", "shx"]  
    # creation du zip
    memory_file = BytesIO()
    zip_folder =  ZipFile(memory_file, 'w')
    #  on insere chaque fichier par extension dans le zip
    for extension in extensions:
        # on ajoute le fichier dans le zip qui sera envoyé
        zip_folder.write(f"{file}.{extension}", os.path.basename(f"{file}.{extension}"))
    
    # on ajoute le fichier prj déjà existant dans le zip qui sera envoyé
    zip_folder.write(path_prj, os.path.basename(path_prj))

    zip_folder.close()
    memory_file.seek(0)
    return send_file(memory_file, download_name=f'grille.zip', as_attachment=True)

@download_lidar.route('/geojson', methods=['GET', 'POST'])
def lidar_geojson():
    geojson = create_geojson_lidar()
    return jsonify(geojson)


@download_lidar.route('/shp/classe', methods=['GET', 'POST'])
def lidar_shp_classe():

    PATH_SHP = "/tmp/api_dispo_produit_tmp_file"
    file_shp = "TA_diff_pkk_lidarhd_classe"
    path_prj = Path(__file__).parent / "../static/files/TA_diff_pkk_lidarhd_classe.prj"

    shp = create_shp_lidar_classe(PATH_SHP, file_shp)
    # chemin absolue du shp
    file = f"{PATH_SHP}/{file_shp}"
    # les extensions du shp
    extensions = ["dbf", "shp", "shx"]  
    # creation du zip
    memory_file = BytesIO()
    zip_folder =  ZipFile(memory_file, 'w')
    #  on insere chaque fichier par extension dans le zip
    for extension in extensions:
        # on ajoute le fichier dans le zip qui sera envoyé
        zip_folder.write(f"{file}.{extension}", os.path.basename(f"{file}.{extension}"))
    
    # on ajoute le fichier prj déjà existant dans le zip qui sera envoyé
    zip_folder.write(path_prj, os.path.basename(path_prj))

    zip_folder.close()
    memory_file.seek(0)
    return send_file(memory_file, download_name=f'grille.zip', as_attachment=True)

def get_paquets_lidar():
    """récupere les paquets lidar

    Returns:
        list: list des dalles lidae
    """
    script_dir = os.path.dirname(__file__)
    file_path_config = os.path.join(script_dir, "../static/json/file_path_dalle_lidar.json")
    with open(file_path_config) as json_file:
        paquets_lidar = json.load(json_file)
    # on boucle sur chaque paquet pour recuperer les coordonnées
    return paquets_lidar

def create_shp_lidar(path_shp, file_shp):
    """Creation du shapefile lidar

    Args:
        path_shp (str): chemin du shp
        file_shp (str): nom du fichier shp
    """
    SIZE = 2000
    data = []
    colonne = []
    for paquet_lidar in get_paquets_lidar():

        # on recupere le x et y du nom du paquet
        name_paquet = paquet_lidar["Name"]
        name = paquet_lidar["Name"].split("$")[-1]
        x = name.split("-")[2].split("_")[0]
        y = name.split("-")[2].split("_")[1]
        
        if isint(x) and isint(y):
            
            # on convertit les bonnes coordonnées
            x_min = int(x) * 1000
            y_min = int(y) * 1000
            x_max = x_min + SIZE
            y_max = y_min - SIZE

            # ce qui va etre envoyer dans ls shp
            name_colonne = "nom_pkk"
            colonne = [{"nom_colonne": name_colonne, "type": "C"}, {"nom_colonne": "url_telechargement", "type": "C"}]
            data.append({name_colonne: name, 
                        "url_telechargement": f"https://wxs.ign.fr/{paquet_lidar['key']}/telechargement/prepackage/{name_paquet}/file/{name}.7z" , 
                        "Geometry": {'type': 'Polygon', 'coordinates': [[(x_min, y_max), (x_max, y_max), (x_max, y_min), (x_min, y_min), (x_min, y_max)]]}})
    # creation du shapefile
    create_shp_file(f"{path_shp}/{file_shp}", colonne, data, 2154)


def create_geojson_lidar():
    """Creation du geojson lidar
    """
    
    SIZE = 2000  
    data = []
    for paquet_lidar in get_paquets_lidar():
        # on recupere le x et y du nom du paquet
        name_paquet = paquet_lidar["Name"]
        name = paquet_lidar["Name"].split("$")[-1]
        x = name.split("-")[2].split("_")[0]
        y = name.split("-")[2].split("_")[1]
        

        # on convertit les bonnes coordonnées
        if isint(x) and isint(y):
            x_min = int(x) * 1000
            y_min = int(y) * 1000
            x_max = x_min + SIZE
            y_max = y_min - SIZE

            # on creer le json
            data.append({name: {
                "Geometry": {
                    'type': 'Polygon', 
                    'coordinates': [[(x_min, y_max), (x_max, y_max), (x_max, y_min), (x_min, y_min), (x_min, y_max)]]
                    },
                "url_telechargement": f"https://wxs.ign.fr/{paquet_lidar['key']}/telechargement/prepackage/{name_paquet}/file/{name}.7z"    
                },
            })
    return data


def create_shp_lidar_classe(path_shp, file_shp):
    
    paquets = []
    
    script_dir = os.path.dirname(__file__)
    file_path_json_s3 = os.path.join(script_dir, "../static/json/dalle_lidar_classe_s3_2.geojson")
    
    with open(file_path_json_s3) as file:
        dalles_s3 = json.load(file)

    data = []
    # on parcours chaque ligne pour inserer chaque paquets dans le code concerné
    for bl in BLOCS:
        for dalle in dalles_s3["paquet_within_bloc"][bl]:

            # ce qui va etre envoyer dans ls shp
            name_colonne = "nom_pkk"
            colonne = [{"nom_colonne": name_colonne, "type": "C"}, {"nom_colonne": "url_telechargement", "type": "C"}]
            data.append({name_colonne: dalle["name"], 
                        "url_telechargement": dalle["name"] , 
                        "Geometry": {'type': 'Polygon', 'coordinates': [[(dalle["bbox"][0], dalle["bbox"][1]), (dalle["bbox"][2], dalle["bbox"][1]), (dalle["bbox"][2], dalle["bbox"][3]), (dalle["bbox"][0], dalle["bbox"][3]), (dalle["bbox"][0], dalle["bbox"][1])]]}})
    
    create_shp_file(f"{path_shp}/{file_shp}", colonne, data, 2154)


def isint(x):
    try:
        a = float(x)
        b = int(a)
    except (TypeError, ValueError):
        return False
    else:
        return a == b

