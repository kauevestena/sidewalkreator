# OSM SIDEWALKREATOR

[A Qgis plugin, officialy available at the official Plugin Repository!](https://plugins.qgis.org/plugins/osm_sidewalkreator/)


<img src="assets/logos/sidewalkreator_logo.png" alt="Image" width="400">


## Scientific Publication is now Available!!

[Since 12/12/2023, in the European Journal of Geography:](https://eurogeojournal.eu/index.php/egj/article/view/553)

> de Moraes Vestena, Kauê, Silvana Philippi Camboim, and Daniel Rodrigues dos Santos. 2023. “OSM Sidewalkreator: A QGIS Plugin for an Automated Drawing of Sidewalk Networks for OpenStreetMap”. European Journal of Geography 14 (4):66-84. https://doi.org/10.48088/ejg.k.ves.14.4.066.084.

The experiments for the publication were carried out in a separate repository: https://github.com/kauevestena/sidewalk_analysis

## Article on OSM Wiki:

Please check it at: https://wiki.openstreetmap.org/wiki/OSM_SidewalKreator 

The wiki will speak about the workflow in a deep level of detail (still in progress).

## Presented at State of the Map 2022!
Abstract at the proceedings: https://zenodo.org/record/7004523

[Presentation slides](https://rebrand.ly/kauevestena_sotm22) 

[Recording](https://www.youtube.com/watch?v=B--1ge42UHY)

## sidewalkreator
Plugin designated to create the Geometries of Sidewalks (separated from streets) based on OpenStreetMap Streets.


[there's a tutorial with the basics on youtube:](https://www.youtube.com/watch?v=jq-K3Ixx0IM)

[and a mute video about the first importing at JOSM](https://www.youtube.com/watch?v=Apqdb73lNvY)

The summary of what the plugin does is what follows:

  - Download and prepare the data (highways and optionally buildings) for a polygon of interest;
  - Provide some tools for highway selection and sidewalk parametrization;
  - Effectively draw the sidewalks
  - Draw the crossings (as sidewalks are required to be integrated to other highways in order to do routing) and kerb-crossing points (where the access ramp information may be filled)
  - Split sidewalk geometries into segments (including the option to not split at all), since in Brazil, and some other places, is very common that in front of each house there's a completely different sidewalk in comparison to the adjacent neighbors 😥.
  - Export the generated sidewalks, crossings and kerb points to a JOSM ready format, where all the importing into OSM shall be done.

It is mostly intended for Acessibility Mapping.

Though the data was generated thinking on the usage for OSM, one may use it for pedestrian network analysis out-of-the-box, or even for other purposes inside or outside QGIS.

## Known Issues:

The only dependency (osm2geojson) have shapely as dependency, but sadly it doesn't come bundled with QGIS, 
so you can install it manually with:

    <qgis_python_path> -m pip install shapely

### For Flatpak QGIS:

1) Open the flatpak shell for the qgis package:


    flatpak run --command=sh org.qgis.qgis
   
3) Within the shell, type:


    curl https://bootstrap.pypa.io/pip/pip.pyz -o pip.pyz
   
5) Install shapely:


    python3 pip.pyz install shapely

In a future release, from [this branch]([https://eurogeojournal.eu/index.php/egj/article/view/553](https://github.com/kauevestena/osm_sidewalkreator/tree/remove_dependencies)) this dependency shall be removed.

