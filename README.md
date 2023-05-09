# POC PCRS

Ce dépôt a pour but de faire un poc sur l'extraction d'une/des dalles(s) pcrs à l'aide d'une carte.

## Arborescence des fichiers

* app/ : dossier où se situent tous les fichiers de l'application web

    * controllers/ dossier contenant les scripts python pour les routes (toutes les actions pour une route)
        * pcrs.py : fichier contenant toutes les routes (pcrs, lidar, osc-ge)
        * api.py : fichier contenant tous les envoies api (dalles, chantiers, config)
        * Config.py : classe contenant la recuperation des différents fichiers de configuration
        * download_lidar.py : fichier contenant toutes les fonctions pour télécharger les dalles lidar en shp ou géojson
    
    * static/ : dossier contenant les fichiers appelés (css, js, img) dans les routes ou fichier html
        * css/ : dossier contenant les différents fichiers css (design)
        * js/ : dossier contenant les différents fichiers js (affichage dynamique)
            * carteTest.js et params.js : fichier pour version2 qui s'occupe de l'affichage
            * dalles_download.js : fichier pour version2 qui s'occupe du téléchargement
            * design.js : fichier qui s'occupe du design des dalles la version2
            * lidar.js : fichier qui s'occupe du lidar
            * osg-ge.js : fichier s'occupant de l'osge
            * proj4.js et proj4leaflet.js : librairies pour faire fonctionner leaflet
        * img/ : dossier contenant les différentes dalles qui sont téléchargées (dalles temporaire peut être dans le futur)
        * files/ : contiens different type de fichier requis (.prj)
        * icon/ : contient différentes icon à afficher dans le html
        * json/ : contient different fichier json
    
    * utils : script utilitaire
    
    * template/ : dossier qui contient tous les fichiers html appelé par les routes
        * layout/ : dossier contenant la barre de navigation et le footer d'une page html (peut être vide)
        * pages/ : dossier contenant les différentes pages appelés par les routes (en l'occurrence version1 et version2 pour le PCRS et version3 pour le LIDAR)
        * base : fichier contenant tout le haut commun de toutes les pages html
    
    * __init__.py : fichier qui initialise l'app + configure les différents fichiers de routes

* plugin_pas_utilise/ : dossier où se situe des plugins js qui pourraient être utile dans le futur

* .gitignore : on ignore certains fichiers(venv, __pycache__, plugin_pas_utilise, img, run.py) aux commit

* config.json : fichier de config qui peut servir pour tout

* config_serveur.json (à creer voir plus bas) : contient les différentes infos du serveur

* requirements.txt : fichier contenant toutes les librairies python à installer (pip install -r requirements.txt)

* run.py, run_prod.py : script qui appelle le dossier app et qui lance l'application web


## Installation projet (serveur prod)

Installer
```sh
sudo apt update && sudo apt install -y git cron screen proj-bin gdal-bin python3 python3-pip python3-venv python-gdal nginx libpq-dev postgresql postgis postgresql-postgis
```

Ajouter les proxy !
```sh
vi ~/.bashrc
```
```sh
export http_proxy=http://proxy.fwcloud.ign.fr:3128
export https_proxy=http://proxy.fwcloud.ign.fr:3128
export HTTP_PROXY=$http_proxy
export HTTPS_PROXY=$https_proxy
```
```sh
source ~/.bashrc
git config --global http.proxy $http_proxy
git config --global https.proxy $https_proxy
```
```sh
pip3 install --upgrade pip
```
```sh
git clone https://github.com/ign-poc-extraction-pcrs/test.git
```


## Run projet

Se mettre à la racine du projet
Création et activation de l'environnement virtuel (si besoin) :

Windows :
```
py -3 -m venv venv
```
```
venv\Scripts\activate
```

Linux:
```sh
python3 -m venv venv
```
```sh
. venv/bin/activate
```

Installation des librairies :
```sh
pip install -r requirements.txt
```

Création de run.py pour lancer le serveur\
Dans run.py (mettre votre "host", si c'est en local enlever "host") :
```py
from app import app

if __name__ == "__main__":
    app.run(host="diffusion05-vm.ign.fr", debug=True)
```

Lancer le serveur :

En dev :
```
python3 run.py
```

En prod :
```sh
screen -S pcrs
cd ~/test
. venv/bin/activate
python3 run_prod.py
```
Puis Ctrl + A + D.

## Autres installations à effectuer en prod

### Configuration de nginx

```sh
sudo nano /etc/nginx/sites-available/pcrs
sudo ln -s /etc/nginx/sites-available/pcrs /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
```

```
server {
    listen 80;

#    server_name     *;

    access_log      /var/log/nginx/pcrs.access.log;

    proxy_request_buffering off;
    proxy_buffering off;
    proxy_buffer_size 4k;
    proxy_read_timeout 10m;
    proxy_send_timeout 10m;
    keepalive_timeout 10m;

    location / {

        proxy_set_header        Client-IP $remote_addr;
        proxy_set_header        Host $host;
        proxy_set_header        X-Forwarded-For $remote_addr;
        proxy_set_header        X-Forwarded-Proto $scheme;

        proxy_pass          http://localhost:5000/;
        proxy_read_timeout  120;
    }
}
```

```sh
sudo systemctl restart nginx
```

### Fichier configuration serveur

Creer fichier de config à la racine du projet (config_serveur.json) :
```
{
    "host_serveur": "https://pcrs-dev.ign.fr",
    "bdd" : {
        "database": "test", 
        "user": "postgres", 
        "host": "localhost", 
        "password": "root", 
        "port": "",
        "schema_dalle": "dalle",
        "schema_chantier": "chantier"
    }
}
```

### installation de kakadu

Récupérer kakadu sur gitlab (kakadu.7z) : http://gitlab.dev-arch-diff.ign.fr/tools/binaires/tree/master 
Déplacer le zip dans un dossier kakadu 

``` 
cd ~
mdkir kakadu
```

Extraire le zip 
```
cd kakadu
apt install p7zip-full
7z x kakadu.7z
```

Installation de quoi le complier
```
apt install default-jre default-jdk build-essential make gcc
```

Compilation
```
cd /kakadu/make
export JAVA_HOME=/usr/lib/jvm/default-java
make -f Makefile-Linux-x86-64-gcc
```

ajouter variable environnement dans le bashrc bashrc (vi ~/.bashrc)
```
export PATH=/home/pcrs-admin/kakadu/kakadu/bin/Linux-x86-64-gcc:$PATH
export LD_LIBRARY_PATH=/home/pcrs-admin/kakadu/kakadu/lib/Linux-x86-64-gcc:$LD_LIBRARY_PATH
```

On relance le bashrc
```
source ~/.bashrc 
```

### Creation du cron

```sh
crontab -e
```

Ajouter :
```
00 02 * * * rm chemin/absolu/test/app/static/img/*
```

### Procédure pour recharger les données Lidar (version3)

Se connecter avec son compte sur cegedim 
```
user@ftp-cegedim
```

Se connecter à la machine de prod 
```
ssh pcrs-admin@extraction_wms_pcrs
```

Lancer la commande pour recharger les dalles lidar et prier pour que les getcap marchent
```
python3 /home/pcrs-admin/test/app/utils/dalle_lidar.py
```

### Mise à jour en prod

Il faut aller dans le depot git, puis git pull et redémarrer le serveur dans le screen
```
cd test/
git pull
screen -r prod_pcrs
ctrl + c
python run.py
ctrl + a
ctrl + d
```
