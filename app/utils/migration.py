import os
import json
from dalle_lidar_classe import BLOCS
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from s3 import BucketAdpater


class Migration:
    def __init__(self) -> None:
        self.script_dir = os.path.dirname(__file__)

    def connection(self):
        load_dotenv()
        # informations de connexion à la base de données
        host = os.environ.get('HOST')
        database = os.environ.get('POSTGRES_DB')
        user = os.environ.get('POSTGRES_USER')
        password = os.environ.get('POSTGRES_PASSWORD')
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
    
    def insert(self, table, column, column_not_duplicate, data):
        # try:
        for d in data:
            self.cursor.execute(f"SELECT {column_not_duplicate} FROM {table} WHERE {column_not_duplicate} = '{d[column_not_duplicate]}'")
            # si la données n'est pas déjà en base on ne l'insere pas
            if not len(self.cursor.fetchall()) > 0:
                requete = f"INSERT INTO {table} {column} VALUES (%s, %s)"
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
        bucketAdpater =BucketAdpater()
        bucketAdpater.get_all_index_json_files("index.json", "/")
        script_dir = os.path.dirname(__file__)
        file_path_json_s3 = os.path.join(script_dir, "../static/json/dalle_lidar_classe_s3_2.geojson")

        with open(file_path_json_s3) as file:
            dalles_s3 = json.load(file)

        dalles = []
        for bl in BLOCS:
            for dalle in dalles_s3["paquet_within_bloc"][bl]:
                wkt = "POLYGON(({0} {1}, {2} {1}, {2} {3}, {0} {3}, {0} {1}))".format(dalle["bbox"][0], dalle["bbox"][1], dalle["bbox"][2], dalle["bbox"][3])
                dalles.append({"name": dalle["name"], "geom": wkt})

        return dalles


if __name__ == "__main__":
    migration = Migration()
    migration.connection()
    migration.create_table("""
            CREATE EXTENSION IF NOT EXISTS postgis;
            CREATE TABLE IF NOT EXISTS dalle (
            id serial PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            geom geometry NOT NULL);
        """)
    migration.insert("dalle", "(name, geom)", "name", migration.get_dalle_json())
    migration.close_connection()
