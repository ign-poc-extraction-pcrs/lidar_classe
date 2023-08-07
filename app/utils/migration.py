import os
import json
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from tqdm import tqdm
from shapely.geometry import box, MultiPolygon, Polygon
from shapely.ops import unary_union
from shapely import area, to_geojson
from shapely.wkb import dumps

from s3 import BucketAdpater
from dalle_lidar_classe import BLOCS


class Migration:
    def __init__(self) -> None:
        self.script_dir = os.path.dirname(__file__)
        self.tables = ["dalle", "bloc"]

    def connection(self):
        load_dotenv()
        # informations de connexion à la base de données
        host = os.environ.get('PGHOST')
        database = os.environ.get('PGDATABASE')
        user = os.environ.get('PGUSER')
        password = os.environ.get('PGPASSWORD')
        port = os.environ.get('PGPORT')
        # connexion à la base de données
        try:
            self.connection = psycopg2.connect(user=user, password=password, host=host, database=database, port=port)
            
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        except (Exception, Error) as error:
            print("Erreur lors de la connexion à la base de données :", error)


    def create_table(self, requete):
        self.cursor.execute(requete)
        self.connection.commit()
    
    def insert(self, table, column, column_not_duplicate, data, type_data):
        # try:
        for d in data:
            self.cursor.execute(f"SELECT {column_not_duplicate} FROM {table} WHERE {column_not_duplicate} = '{d[column_not_duplicate]}'")
            # si la données n'est pas déjà en base on ne l'insere pas
            if not len(self.cursor.fetchall()) > 0:
                requete = f"INSERT INTO {table} {column} VALUES {type_data}"
                content = tuple(d.values())
                self.cursor.execute(requete, content)
        self.connection.commit()
        # except (Exception, Error) as error:
        #     print("Erreur lors de l'insertion de données :", error)
    
    def close_connection(self):
        # fermeture de la connexion à la base de données
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("Connexion à la base de données fermée")
    
    def get_dalle_json(self):
        """Recupere les dalles du json

        Returns:
            dict: recupere les dalles
        """
        script_dir = os.path.dirname(__file__)
        file_path_json_s3 = os.path.join(script_dir, "../static/json/dalle_lidar_classe_s3_2.geojson")

        with open(file_path_json_s3) as file:
            dalles_s3 = json.load(file)

        dalles = []
        print("insertion..")
        for bl in tqdm(BLOCS):
            if bl in dalles_s3["paquet_within_bloc"] and dalles_s3["paquet_within_bloc"][bl]:
                for dalle in dalles_s3["paquet_within_bloc"][bl]:
                    wkt = "POLYGON(({0} {1}, {2} {1}, {2} {3}, {0} {3}, {0} {1}))".format(dalle["bbox"][0], dalle["bbox"][1], dalle["bbox"][2], dalle["bbox"][3])
                    dalles.append({"name": dalle["name"], "geom": wkt, "bloc": bl})

        return dalles
    
    def export_bloc_extent(self):
        bucketAdpater =BucketAdpater()
        bucketAdpater.get_all_index_json_files("index.json", "/")
        script_dir = os.path.dirname(__file__)
        file_path_json = os.path.join(script_dir, "../static/json/dalle_lidar_classe_s3_2.geojson")
        with open(file_path_json, 'r') as f:
            index_json_files = json.load(f)

        blocs = []
        # pour chaque bloc
        for bloc, dalles in index_json_files['paquet_within_bloc'].items():
            polygon = unary_union([box(*dalle['bbox']) for dalle in dalles])
            new_polygon = Polygon(polygon.exterior.coords).normalize()
            multi_polygon = MultiPolygon([new_polygon])
            geom_binary = dumps(multi_polygon)
            

            blocs.append({"name": bloc, "geom": geom_binary})
        
        return blocs

    def drop_data(self):
        """fonction qui supprime les tables de la base"""
        for table in self.tables:
            sql = f"DROP TABLE {table};"
            try:
                # Exécution de la requête SQL
                self.cursor.execute(sql)
                # Valider les changements dans la base de données
                self.connection.commit()
                print(f"La table {table} a été supprimée avec succès.")
            except psycopg2.Error as e:
                # En cas d'erreur, annuler les changements et afficher l'erreur
                self.connection.rollback()
                print("Erreur lors de la suppression de la table :", e)


if __name__ == "__main__":
    migration = Migration()
    migration.connection()
    migration.create_table("""
            CREATE EXTENSION IF NOT EXISTS postgis;
            CREATE TABLE IF NOT EXISTS bloc (
            id serial PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            geom geometry NOT NULL);
        """)
    migration.create_table("""
            CREATE EXTENSION IF NOT EXISTS postgis;
            CREATE TABLE IF NOT EXISTS dalle (
            id serial PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            geom geometry NOT NULL,
            bloc_id INTEGER NOT NULL,
            FOREIGN KEY (bloc_id) REFERENCES bloc(id));
        """)
    migration.insert("bloc", "(name, geom)", "name", migration.export_bloc_extent(), f"(%s, %s)")
    migration.insert("dalle", "(name, geom, bloc)", "name", migration.get_dalle_json(), f"(%s, %s, %s)")
    migration.close_connection()
