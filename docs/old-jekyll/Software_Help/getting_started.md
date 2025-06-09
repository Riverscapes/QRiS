---
title: Getting Started
sidebar_position: 1
---

QRiS is based around the concepts of projects. A project is a container for all your GIS layers and tabular data. Each project pertains to a unique place. For example, you might create a project for a reach of river, or a watershed.

Note that projects are multi-temporal. A single project can contain data pertaining to historical conditions, the present as well as the future, in the form of restoration designs. The idea is that a project will contain the current state of your area of interest, together with data tracking how it is changing, or will be restored, over time. Having these multiple points in time all within one project allows QRiS to analyse the trajectory of your river's health, whther it is improving or degrading.

## Creating Your First Project

Once you have QRiS installed, use the Project menu on the toolbar to create a new project.

![new project]({{site.baseurl}}/assets/images/new_project_menu.png)

Choose a folder on your hard drive where the project will be created and then provide a name for the project.

![new project]({{site.baseurl}}/assets/images/new_project.png)

The QRiS dockable window will appear showing an empty project structure. Most actions are performed by right clicking on items in this hierarchy.

## Area of Interest

A useful first step is to draw an area of interest (AOI). This is typically a simple, single polygon that encircles your study area. Later, this polygon can be used to clip other datasets as you import them into your project.

Right click on the AOI folder icon and choose "Create New AOI". Give it a name in the window that pops up. A polygon layer will be added to your project and then displayed in the map. Use the QGiS digitizing tools to digitize the desired shape around your study area. Remember to stop editing when you are done so that the shape gets stored permanently in your QGIS project.

Remember that you can always add other layers to the current QGiS map to help guide your digitizing. Moreoever, if you already have an appropriate polygon layer that you want to use as your AOI then simply right click in the QGIS project and choose "Import Existing AOI".

## More Layers

Where you go from here depends on what you want to do! You can import raster surfaces or create data capture events to digitize more thematic layers.

## Analyses

Once you have one or more data capture events you can start recording metrics that describe the health of your riverscape. You can enter these metrics by hand or ask QRiS to analyse the geometries that you have digitized and extract the metrics for you. If you have multiple data capture events that represents different points in time (historic conditions, present day, future post restoration), then you can repeat the analysis to get a sense of how your river health is trending over time.

## Sharing

At any stage you can export sections of your QRiS project and upload them into the [Riverscapes Exchange](https://data.riverscapes.net) so that your collaborators can access them.

