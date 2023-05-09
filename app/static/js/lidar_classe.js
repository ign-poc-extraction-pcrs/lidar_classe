// Paramètres
const REGEX_X_Y = new RegExp('([0-9]{4})_([0-9]{4}_LA93)');
const REGEX_X_Y_s3 = new RegExp('(IGN69_[0-9]{4})-([0-9]{4})')
;
// const REGEX_DEP = new RegExp('D[0-9AB]{3}'); // TODO : R93, R94, R01-06, FRA, FRX, FXX, GLP, MTQ, SBA, SMA, MYT, REU, SPM, GUF
const SIZE = 1000;
const DESIGN = {
    "base": {
        "fillColor": "white",
        "weight": 2,
        "opacity": 1,
        "color": "#000",
        "dashArray": "0",
        "fillOpacity": 0.2
    },
    "fly_over": {
        "fillColor": "white",
        "weight": 1,
        "opacity": 0,
        "color": '',
        "dashArray": "4",
        "fillOpacity": 0.7
    }
}
// Source : https://epsg.io/2154.proj4
const proj4_2154 = "+proj=lcc +lat_1=49 +lat_2=44 +lat_0=46.5 +lon_0=3 +x_0=700000 +y_0=6600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs";
const bounds = L.bounds([-378305.81, 6093283.21], [1212610.74, 7186901.68]);
// Source : https://github.com/IGNF/geoportal-extensions/blob/c606b749e060c5efc1a30137a1ed1d6d4ef47bfe/src/Leaflet/CRS/EPSG2154.js
const resolutions = [104579.22454989408, 52277.53235379051, 26135.487078595408, 13066.891381800004, 6533.228604113456, 3266.5595244626675, 1633.2660045974187, 816.6295549860224, 408.31391467683596, 204.15674151090204, 102.07831678324082, 51.0391448966112, 25.519569074269395, 12.759783693647506, 6.379891635966491, 3.18994576530532, 1.5949728694977277, .7974864315474559, .398743214900604, .19937160727567999, .099685803696052, .049842901818919996];
const origin = [0, 12000000];
// Création du converter
proj4.defs("EPSG:2154", proj4_2154);
const converter = proj4("EPSG:2154");
// Param en dur
const DATA_TYPE = "lidarhd";
var map, key;


document.addEventListener("DOMContentLoaded", function () {
    // Création du crs_2154
    var crs_2154 = new L.Proj.CRS('EPSG:2154', proj4_2154, {
        resolutions: resolutions,
        origin: origin,
        bounds: bounds
    });

    // Création d'une carte en 2154
    map = L.map('map', {
        crs: crs_2154,
        continuousWorld: true,
        center: [44.503264422561784, 1.586937060953668],
        zoom: 8,
    });

    // Création et ajout des fonds de carte en 2154
    var orthoImage = L.tileLayer('https://wxs.ign.fr/lambert93/geoportail/wmts?layer={layer}&style=normal&tilematrixset=LAMB93&Service=WMTS&Request=GetTile&VERSION=1.0.0&format=image/jpeg&TileMatrix={z}&TileCol={x}&TileRow={y}', {
        layer: "ORTHOIMAGERY.ORTHOPHOTOS.BDORTHO.L93",
        continuousWorld: true,
    }).addTo(map);
    var planIgnV2 = L.tileLayer.wms('https://wxs.ign.fr/essentiels/geoportail/r/wms?', {
        layers: 'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2',
        continuousWorld: true,
    }).addTo(map);

    // Ajout d'un control pour choisir le fond de carte
    var baseMaps = {
        "OrthoImage": orthoImage,
        "Plan IGN": planIgnV2,
    };
    L.control.layers(baseMaps).addTo(map);

    // Ajout échelle et géocodage
    L.control.scale().addTo(map);
    L.Control.geocoder().addTo(map);

    // Pour le debug
    map.on('click', function (e) {
        var coord = e.latlng;
        console.log("You clicked the map at: [" + coord.lat + ", " + coord.lng + "]");
    });

    geojson = []
    geojson_blocs = []
    create_dallage_blocs(map.getZoom())
    map.on('moveend', function() {
        var northEast = map.getBounds()._northEast
        var southWest = map.getBounds()._southWest

        northEast = converter.forward([northEast.lng, northEast.lat])
        southWest = converter.forward([southWest.lng, southWest.lat])
        zoom = map.getZoom()
        listData(zoom, northEast, southWest);
     });
    
});

function get_serveur() {
    // requete ajax pour recuperer les differentes clé lidar
    const xhr = new XMLHttpRequest();
    xhr.open("GET", "api/get/config/serveur", false);
    xhr.getResponseHeader("Content-type", "application/json");
    xhr.onload = function() {
        const obj = JSON.parse(this.responseText);
        serveur = obj.result
    } 
    xhr.send()
    return serveur
}

function listData(zoom, northEast, southWest) {
    old_geojson = geojson
    map.removeLayer(old_geojson)
    if (zoom >= 10) {
    // On affiche la div de chargement
    document.getElementById("loading_div").style.display = "block";
    // On masque les div d'erreur et de formulaire
    document.getElementById("key_error_div").style.display = "none";
    serveur = get_serveur(); 
    // getFeature info
    fetch(`${serveur}/api/version5/get/dalle/${northEast[0]}/${southWest[1]}/${southWest[0]}/${northEast[1]}`)
        .then(function (response) {
            if (response.ok) {
                return response.json();
                
            } else {
                throw Error(response.statusText);
            }
        })
        .then(function (data) {
            // Récupération des ressources LidarHD
            var lidarHdResources = get_resources(data["result"]);
            // On affiche text
            document.getElementById("text_div").style.display = "block";
            nb_dalle = lidarHdResources.length;
            document.getElementById("nb_dalles").textContent = nb_dalle;
            document.getElementById("nb_dalles_find").textContent = data["count_dalle"];

            // Création du dallage
            var dallage = create_dallage(lidarHdResources);

            // Ajout du dallage
            geojson = add_dallage(dallage);
        }).finally(function () {
            // On masque loading
            document.getElementById("loading_div").style.display = "none";
        })
        ;
    }else{
        // On cache le text
        document.getElementById("text_div").style.display = "none";
        create_dallage_blocs(zoom)
    }
    
}


function get_resources(data) {
    // Récupération des ressources LidarHD
    var lidarHdResources = [];
    for (const [key, value] of Object.entries(data)) {
        if (value.length !== 0){
            lidarHdResources = lidarHdResources.concat(value)
        }
    }
    return lidarHdResources;
}

function get_files(data) {
    // Récupération des fichiers
    var files = [];
    var domFiles = data.getElementsByTagName("files")[0].getElementsByTagName("file");
    for (let domFile of domFiles) {
        var keyValue = {};
        for (let child of domFile.childNodes) {
            if (child.tagName) {
                keyValue[child.tagName] = child.textContent;
            }
        }
        files.push(keyValue);
    }
    return files;
}

function create_dallage(resources) {
    let dallage = {
        "type": "FeatureCollection",
        "features": [],
    }

    for (let resource of resources) {

        name_dalle = resource["name"]

        var match_x_y = REGEX_X_Y.exec(name_dalle);
        if(match_x_y == null){
            match_x_y = REGEX_X_Y_s3.exec(name_dalle)
            match_x_y[1] = match_x_y[1].split("_")[1]
            match_x_y[2] = match_x_y[2] + "_LA93"
        }

        if (match_x_y) {
            var x_min = parseInt(match_x_y[1]) * 1000;
            var y_max = parseInt(match_x_y[2].split("_")[0]) * 1000;
            var x_max = x_min + SIZE;
            var y_min = y_max - SIZE;
            var dalle = name_dalle.split("/")
            var bloc = dalle[dalle.length -2]
            var dalle_name = dalle[dalle.length -1]
            var year = dalle_name.split("_")[1]

            dallage["features"].push({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            // on change la projection les coordonnées
                            converter.inverse([x_min, y_min]),
                            converter.inverse([x_max, y_min]),
                            converter.inverse([x_max, y_max]),
                            converter.inverse([x_min, y_max]),
                            converter.inverse([x_min, y_min]),
                        ]
                    ]
                },
                "properties": {
                    "url" : resource,
                    "bloc": bloc,
                    "dalle_name": `LHD_C_LA93-IGN69_${x_min / 1000}-${y_max / 1000}_${year}_v1.laz`
                }
            });
        } else {
            console.error(resource.Name);
        }
    }
    return dallage;
}

function add_dallage(dallage) {
    // Add layer
    var geojson = L.geoJson(dallage, {
        style: DESIGN.base,
        onEachFeature: function (feature, layer) {
            layer.on({
                mouseover: highlightFeature,
                mouseout: resetHighlightFeature,
                click: clickFeature,
            });
        }
    }).addTo(map);
    // Set view
    // map.fitBounds(geojson.getBounds());
    return geojson;
}

function show_popup(layer, type = "open") {
    "Fonction qui affiche une popup, au survol d'une dalle son nom."
    var target = layer.feature["properties"]
    var dalle_name = target.dalle_name;
    template = `<p>${dalle_name}</p>`

    if (type == "open") {
        layer.bindPopup(template).openPopup()
    } else {
        layer.closePopup()
    }
}

function highlightFeature(e) {
    "Changement de design des dalles quant on survole une dalle."
    var layer = e.target;
    layer.setStyle(DESIGN.fly_over);
    show_popup(layer);
}
function resetHighlightFeature(e) {
    "Remet le design normal."
    var layer = e.target;
    layer.setStyle(DESIGN.base);
    show_popup(layer, "close");
}
function clickFeature(e) {
    // On affiche la div de chargement
    document.getElementById("loading_div").style.display = "block";
    // On masque la div de dalle
    document.getElementById("dalle_div").style.display = "none";
    // On récupère l'élément cliqué
    var layer = e.target;
    var dalle = layer.feature["properties"]

    // Affichage des fichiers
    show_files(dalle);

    // On monte la div dalle
    document.getElementById("dalle_div").style.display = "block";
    // On masque la div de chargement
    document.getElementById("loading_div").style.display = "none";
        
}

function show_files(dalle) {
    // Récupération de la liste de fichiers
    var ulFiles = document.getElementById('files');

    // Suppression des enfants
    for (let child of ulFiles.childNodes) {
        ulFiles.removeChild(child);
    }

    var li = document.createElement('li');
    var a = document.createElement('a');
    a.textContent = `${dalle.dalle_name}`;
    a.setAttribute('href', dalle.url.name);
    li.appendChild(a);
    ulFiles.appendChild(li);
}

function bytesToSize(bytes) {
    var sizes = ['o', 'ko', 'mo', 'go', 'to'];
    if (bytes == 0) return '0 o';
    var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    var size = (bytes / Math.pow(1024, i)).toFixed(2).replace('.', ',');
    return `${size} ${sizes[i]}`;
};

function create_dallage_blocs(zoom, geojson_blocs) {
    if (zoom < 10){
        var old_geojson_blocs = geojson_blocs
        
        serveur = get_serveur(); 
        // getFeature info
        fetch(`${serveur}/api/version5/get/blocs`)
            .then(function (response) {
                if (response.ok) {
                    return response.json();
                    
                } else {
                    throw Error(response.statusText);
                }
            })
            .then(function (data) {
                let dallage = {
                    "type": "FeatureCollection",
                    "features": [],
                }

                data["result"].forEach(bloc => {
                    coordinates = []
                    bloc.geometry.coordinates[0][0].forEach(geom => {
                        coordinates.push(converter.inverse([geom[0], geom[1]]))
                    });

                    dallage["features"].push({
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [coordinates]
                        },
                        "properties": {
                            "bloc": bloc.properties.Nom_bloc,
                        }
                    });
                });
                // map.removeLayer(old_geojson_blocs)
                // Add layer
                var geojson_blocs = L.geoJson(dallage, {
                    style: DESIGN.base,
                }).addTo(map);

                document.getElementById("nb_bloc").textContent = data["count_bloc"];
            })
            ;
    }
}
