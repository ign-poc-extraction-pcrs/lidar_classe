from flask import Blueprint, jsonify
import json
import os
import shapely.geometry
from app.utils.dalle_lidar_classe import BLOCS, get_blocs_classe, get_dalle_classe


api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/get/config/serveur')
def get_config_serveur():
    # recupere le serveur
    statut = "failure"
    host = os.environ.get('HOST_SERVEUR')
    if host :
        statut = "success"

    return jsonify({"statut": statut, "result": host})


@api.route('/version5/get/dalle/<float(signed=True):x_min>/<float(signed=True):y_min>/<float(signed=True):x_max>/<float(signed=True):y_max>', methods=['GET', 'POST'])
def get_dalle_lidar_classe(x_min=None, y_min=None, x_max=None, y_max=None):
    bbox_windows = (x_min, y_min, x_max, y_max)
    paquets = get_dalle_in_bloc(bbox_windows)

    return jsonify({"result": paquets["paquet_within_bloc"], "count_dalle": paquets["count_dalle"] })


@api.route('/version5/get/blocs', methods=['GET', 'POST'])
def get_blocs_lidar_classe():
    blocs = get_blocs_classe()

    return jsonify({"result": blocs, "count_bloc":len(blocs)})


def get_dalle_in_bloc(bbox_windows):
    """Recupere les dalles dans les blocs (on enleve ceux qui dépasse)

    Args:
        bbox_windows (tuple): bbox de la fenetre, va permettre de ne recuperer seulement que les dalles qui sont dans la fenetre

    Returns:
        dict: Dalles dans les blocs + nombre de dalle en tout
    """
    script_dir = os.path.dirname(__file__)
    file_path_json_s3 = os.path.join(script_dir, "../static/json/dalle_lidar_classe_s3_2.geojson")
    paquet_within_bloc = {}
    
    with open(file_path_json_s3) as file:
        dalles_s3 = json.load(file)
    
    dalles_s3 = dalles_s3["paquet_within_bloc"]
    count = 0
    
    for bloc in dalles_s3:
        if bloc not in paquet_within_bloc:
            paquet_within_bloc[bloc] = []

        for dalle in dalles_s3[bloc]:
            count += 1
            if get_bboxes_within_bboxes(tuple(dalle["bbox"]), bbox_windows):
                paquet_within_bloc[bloc].append(dalle)
    return {"paquet_within_bloc": paquet_within_bloc, "count_dalle": count}



def get_bboxes_within_bboxes(bbox, bbox_windows):
    """_summary_

    Args:
        bbox (tuple): bbox -> (x_min, y_min, x_max, y_max)
        bbox_windows (tuple): bbox fenetre

    Returns:
        bool: on retourne True si la bbbox est dans le polygon
    """
    # on transforme notre polygon en geometry
    bbox_windows = shapely.geometry.box(*bbox_windows)
    # on transforme notre bbox en geometry
    bbox_polygon = shapely.geometry.box(*bbox)
    # on regarde si la bbox est dans le polygon
    if bbox_windows.contains(bbox_polygon):
        return True
    return False
