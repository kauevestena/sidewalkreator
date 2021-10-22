# -*- coding: utf-8 -*-
"""
/***************************************************************************
 sidewalkreator
                                 A QGIS plugin
 Plugin designated to create the Geometries of Sidewalks (separated from streets) based on OpenStreetMap Streets, given a bounding polygon, outputting to JOSM format. It is mostly intended for acessibility Mapping.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-09-29
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Kaue de Moraes Vestena
        email                : kauemv2@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# import os.path
import os, requests, codecs, time
# from os import environ

# standard libraries
# import codecs # for osm2geojson

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.gui import QgsMapLayerComboBox, QgsMapCanvas
from qgis.PyQt.QtWidgets import QAction
# additional qgis/qt imports:
from qgis import processing
from qgis.core import QgsMapLayerProxyModel, QgsFeature, QgsCoordinateReferenceSystem, QgsVectorLayer, QgsProject


# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .osm_sidewalkreator_dialog import sidewalkreatorDialog


# for third-party libraries installation
import subprocess
import sys


def install_pypi(packagename):
    subprocess.check_call([sys.executable, "-m", "pip", "install", packagename])


# importing or installing third-party libraries
try:
    # import geopandas as gpd
    import osm2geojson
except:
    pkg_to_be_installed = ['osm2geojson'] #'geopandas'

    for packagename in pkg_to_be_installed:
        install_pypi(packagename)


# # then again, because its best to raise an error
# import geopandas as gpd
import osm2geojson

# # internal dependencies:
from .osm_fetch import *



############################
##### GLOBAL-SCOPE
###########################

# to path stuff don't get messy:

# homepath = os.environ['HOME']
homepath = os.path.expanduser('~')

user_profile = 'default' #TODO: read from session

basepathp1 = '.local/share/QGIS/QGIS3/profiles'
basepathp2 = 'python/plugins/osm_sidewalkreator'
basepath = os.path.join(homepath,basepathp1,user_profile,basepathp2)
print(basepath)
reports_path = os.path.join(basepath,'reports')


crs_4326 = QgsCoordinateReferenceSystem("EPSG:4326")


def reproject_layer(inputlayer,destination_crs='EPSG:4326',output_mode='memory:Reprojected'):
    parameter_dict = {'INPUT': inputlayer, 'TARGET_CRS': destination_crs,
                 'OUTPUT': output_mode}

    return processing.run('native:reprojectlayer', parameter_dict)['OUTPUT']



def cliplayer(inlayerpath,cliplayerpath,outputpath):
    '''
        clip a layer

        all inputs are paths!!!

        will be generated clipped layer as a file in outputpath

        source: https://opensourceoptions.com/blog/pyqgis-clip-vector-layers/ (thx!!)
    '''
    #run the clip tool
    processing.run("native:clip", {'INPUT':inlayerpath,'OVERLAY':cliplayerpath,'OUTPUT':outputpath})


def path_from_layer(inputlayer,splitcharacter='|',splitposition=0):
    return inputlayer.dataProvider().dataSourceUri().split(splitcharacter)[splitposition]

def custom_local_projection(lgt_0,lat_0=0,mode='TM',return_wkt=False):

    as_wkt = f"""PROJCRS["unknown",
    BASEGEOGCRS["WGS 84",
        DATUM["World Geodetic System 1984",
            ELLIPSOID["WGS 84",6378137,298.257223563,
                LENGTHUNIT["metre",1]],
            ID["EPSG",6326]],
        PRIMEM["Greenwich",0,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8901]]],
    CONVERSION["unknown",
        METHOD["Transverse Mercator",
            ID["EPSG",9807]],
        PARAMETER["Latitude of natural origin",{lat_0},
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8801]],
        PARAMETER["Longitude of natural origin",{lgt_0},
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8802]],
        PARAMETER["Scale factor at natural origin",1,
            SCALEUNIT["unity",1],
            ID["EPSG",8805]],
        PARAMETER["False easting",0,
            LENGTHUNIT["metre",1],
            ID["EPSG",8806]],
        PARAMETER["False northing",0,
            LENGTHUNIT["metre",1],
            ID["EPSG",8807]]],
    CS[Cartesian,2],
        AXIS["(E)",east,
            ORDER[1],
            LENGTHUNIT["metre",1,
                ID["EPSG",9001]]],
        AXIS["(N)",north,
            ORDER[2],
            LENGTHUNIT["metre",1,
                ID["EPSG",9001]]]]
    """

    # TODO: if mode != 'TM' and lat_0 != 0:
    # define as_wkt as a stereographic projection

    custom_crs = QgsCoordinateReferenceSystem()

    custom_crs.createFromWkt(as_wkt)

    if return_wkt:
        return as_wkt
    else:
        return custom_crs

def reproject_layer_localTM(inputlayer,outputpath,layername,lgt_0,lat_0=0):

    # https://docs.qgis.org/3.16/en/docs/user_manual/processing_algs/qgis/vectorgeneral.html#reproject-layer

    operation = f'+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=tmerc +lat_0=0 +lon_0={lgt_0} +k=1 +x_0=0 +y_0=0 +ellps=WGS84'


    parameter_dict = { 'INPUT' : inputlayer, 'OPERATION' : operation, 'OUTPUT' : outputpath }

    # option 1: creating from wkt
    # proj_wkt = custom_local_projection(lgt_0,return_wkt=True)
    # parameter_dict['TARGET_CRS'] = QgsCoordinateReferenceSystem(proj_wkt)

    # option 2: as a crs object, directly
    new_crs = custom_local_projection(lgt_0)
    parameter_dict['TARGET_CRS'] = new_crs


    processing.run('native:reprojectlayer', parameter_dict)

    # fixing no set layer crs:

    ret_lyr = QgsVectorLayer(outputpath,layername,'ogr')

    ret_lyr.setCrs(new_crs)

    return ret_lyr, new_crs

class sidewalkreator:
    """QGIS Plugin Implementation."""

    # to control current language:
    current_lang = 'en'

    # just for debugging events
    global_counter = 0


    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'sidewalkreator_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&OSM SidewalKreator')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None



        ###############################################
        ####    My code on __init__
        #########################################
        # language_selector
        # self.dlg.opt_ptbr.checked.connect(self.change_language)


        self.session_debugpath = os.path.join(reports_path,'session_debug.txt')

        with open(self.session_debugpath,'w+') as session_report:
            session_report.write('session_report:\n')
            # session_report.write(session_debugpath+'\n')
            # session_report.write(homepath)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('sidewalkreator', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):


        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/osm_sidewalkreator/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Create Sidewalks for OSM'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&OSM SidewalKreator'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = sidewalkreatorDialog()


            # # # THE FUNCTION CONNECTIONS
            self.dlg.datafetch.clicked.connect(self.call_get_osm_data)

            # language stuff
            self.dlg.opt_ptbr.clicked.connect(self.change_language_ptbr)
            self.dlg.opt_en.clicked.connect(self.go_back_to_english)
            self.dlg.input_layer_selector.layerChanged.connect(self.get_input_layer)


            # # # handles and modifications/ors:


            self.dlg.input_layer_selector.setFilters(QgsMapLayerProxyModel.PolygonLayer)
            self.dlg.input_layer_selector.setAllowEmptyLayer(True)
            self.dlg.input_layer_selector.setLayer(None)
            # thx: https://github.com/qgis/QGIS/issues/38472

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    ##################################
    ##### THE CLASS SCOPE
    ##################################

    def add_layer_canvas(self,layer):
        # canvas = QgsMapCanvas()
        QgsProject.instance().addMapLayer(layer)
        QgsMapCanvas().setExtent(layer.extent())
        # canvas.setLayerSet([QgsMapCanvasLayer(layer)])

    def change_language_ptbr(self):
        self.current_lang = 'ptbr'

        self.dlg.lang_label.setText("Idioma: ")
        self.dlg.input_pol_label.setText("Polígono de Entrada")

    def go_back_to_english(self):
        self.current_lang = 'en'

        self.dlg.lang_label.setText("Language: ")
        self.dlg.input_pol_label.setText("Input Polygon: ")

    def get_input_layer(self):
        # self.input_layer = QgsMapLayerComboBox.currentLayer()
        self.input_layer = self.dlg.input_layer_selector.currentLayer()

        # .next()

        if self.input_layer:
            self.write_to_debug(self.input_layer.dataProvider().dataSourceUri())


            # assuring 4326 as EPSG code for layer
            layer_4326 = reproject_layer(self.input_layer)



            input_feature = QgsFeature()


            iterat = layer_4326.getFeatures()

            iterat.nextFeature(input_feature)

            if input_feature.hasGeometry():
                # TODO: beware of qgis bugs...


                if input_feature.isValid():
                    self.input_polygon = input_feature.geometry()

                    # self.write_to_debug(self.input_polygon.toWkt())

                    bbox = self.input_polygon.boundingBox()

                    # in order to create a local custom projection
                    self.bbox_center = bbox.center()

                    self.minLgt = bbox.xMinimum()
                    self.minLat = bbox.yMinimum()
                    self.maxLgt = bbox.xMaximum()
                    self.maxLat = bbox.yMaximum()


                    if self.input_polygon.isGeosValid():
                        self.dlg.datafetch.setEnabled(True)
                        self.dlg.input_status.setText('Valid Input!')
                        self.dlg.input_status_of_data.setText('waiting for data...')


                        for item in [self.minLgt,self.minLat,self.maxLgt,self.maxLat]:
                            self.write_to_debug(item)
            else:
                self.dlg.input_status.setText('no geometries on input!!')
                self.dlg.datafetch.setEnabled(False)
        else:

            self.dlg.input_status.setText('waiting a valid for input...')
            self.dlg.datafetch.setEnabled(False)



            # self.dlg.for_tests.setText(str(self.global_counter))

            self.global_counter += 1

        # self.input_polygon_wkt = self.input_polygon.asWkt()

        # self.dlg.for_tests.setText(str())

    def call_get_osm_data(self):
        """
        Function to call the functions from "osm fetch" module
        """

        self.dlg.datafetch.setEnabled(False)


        query_string = osm_query_string_by_bbox(self.minLat,self.minLgt,self.maxLat,self.maxLgt)


        data_geojsonpath = get_osm_data(query_string,'osm_download_data')

        self.dlg.input_status_of_data.setText('data acquired!')

        # to prevent user to loop
        self.dlg.input_layer_selector.setEnabled(False)


        clipped_path = data_geojsonpath.replace('.geojson','_clipped.geojson')

        clip_polygon_path = path_from_layer(self.input_layer)

        self.write_to_debug(clip_polygon_path)

        # addinf as layer
        osm_data_layer = QgsVectorLayer(data_geojsonpath,"osm_road_data","ogr")

        cliplayer(osm_data_layer,self.input_layer,clipped_path)


        clipped_datalayer = QgsVectorLayer(clipped_path,"osm_road_data","ogr")

        # # Custom CRS, to use metric stuff with minimal distortion
        # local_crs = custom_local_projection(self.bbox_center.x(),return_wkt=True)

        # creating as a temporary file
        clipped_reproj_path = data_geojsonpath.replace('.geojson','_clipped_reproj.geojson')


        # reproject_layer_localTM(clipped_datalayer,clipped_reproj_path,lgt_0=self.bbox_center.x())

        # self.clipped_reproj_datalayer = reproject_layer(clipped_datalayer,local_crs)

        # self.clipped_reproj_datalayer = QgsVectorLayer(clipped_reproj_path,'osm_clipped_roads','ogr')

        # both the layer in the new "local" projection system and the "local" projection system
        self.clipped_reproj_datalayer, self.custom_localTM_crs = reproject_layer_localTM(clipped_datalayer,clipped_reproj_path,'osm_clipped_roads',lgt_0=self.bbox_center.x())

        # adding to canvas
        # TODO: first, we will need to clip it
        self.add_layer_canvas(self.clipped_reproj_datalayer)

        # # testing if inverse transformation is working: 
        # # self.add_layer_canvas(reproject_layer(self.clipped_reproj_datalayer))



    def write_to_debug(self,input_stringable,add_newline=True):
        with open(self.session_debugpath,'a+') as session_report:
            session_report.write(str(input_stringable))
            if add_newline:
                session_report.write('\n')


