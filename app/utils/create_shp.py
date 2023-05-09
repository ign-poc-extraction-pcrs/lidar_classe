import shapefile
from typing import List, Dict, Union
from pyproj import CRS

def create_shp_file(path: str, colonnes: List[Dict], data: List[Dict], epsg_code: Union[str, int], geom_colonne: str = "Geometry", geomtype: str = 'polygon'):
    """Creation d'un fichier shapefile

    Example:
        * colonnes = [{"nom_colonne": "chantier", "type": "C"}]
        * data [{"chantier": "chantier1", "Geometry": {'type': 'Polygon', 'coordinates': [[(10.0, 50.0), (50.0, 50.0), (50.0, 10.0), (30.0, 30.0), (10.0, 10.0), (10.0, 50.0)]]}}]

    Args:
        path (str): chemin vers le fichier
        colonnes (List[Dict]): liste de dictionnaire détaillant chaque colonne
        data (List[Dict]): liste des entrées, la géométrie doit être en géoJSON.
        epsg_code (Union[str, int]): code epsg des données
        geom_colonne (str, optional): nom de la colonne portant la géométrie dans les dictionnaires. Defaults to "Geometry".
        geomtype (str, optional): type de la géométrie. Defaults to 'polygon'.
    """
    if geomtype == 'point':
        type_shp = shapefile.POINT
    elif geomtype == 'line':
        type_shp = shapefile.POLYLINE
    else:
        type_shp = shapefile.POLYGON

    with shapefile.Writer(path, type_shp) as shp:
        column_key = []
        # pour chaque clé on crée une colonne
        for key_ta in colonnes:
            shp.field(key_ta["nom_colonne"], key_ta["type"], size=250)
            column_key.append(key_ta["nom_colonne"])
        # pour chaque valeur on crée une entrée
        for value_ta in data:
            shp.shape(value_ta[geom_colonne])
            column_value = [value_ta[key] for key in column_key]
            shp.record(*column_value)