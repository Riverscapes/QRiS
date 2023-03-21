# QRiS Plugin

## [0.1.14] 2023 MAR 21

## Added
- QRave plugin dependency
- Import Riverscapes Layer from QRave into QRiS as Context layers
- Open an existing Analysis
- Automated metrics (Sinuosity, Gradient)
- Add hillshade to DEM
- Initial raster type dropdown is derived from raster tname when importing
- Limit one DEM per DCE

## Fixed
- Analysis column size on window resize
- Analysis Table read-only
- Centerline error when polygon projection is not EPSG 4326
- Not implemented message when adding transect profiles
- Raster Slider layer picker window bug
- Event layers duplicated when editing surfaces in event properties
- Event layers in project tree removed when removed from event properties

## Changed
- Symbology now coming from QRave

## [0.1.13] 2023 FEB 24

### Fixed
- bug when saving manual analysis values (schema change)
- event id incorrectly set for event layers
- bug with edit event form

## [0.1.12] 2023 FEB 21

### Added
- Generate sample frames from Cross Sections
- Inverse Value option for Raster Slider
- Centerline tool for AOI polygons
- Sample frames for context polygons
- Labels for Sample Frames

### Fixed
- Save Raster Slider polygon bug
- Centerline Reset button fix
- bug with catchments node placement in project tree
- Analysis panel bugs
- Group layers expand when adding layers to map
- bug with DCE node placement in project tree
- bug with centerline and sample frame coordinate systems

### Changed
- Map manager improvements for raster slider
- Map manager improvements for centerline tool
- Centerline tool polygon selection tool
- Centerline tool ignores interior rings in polygon
- Centerline tool only retains the continuous section between the clip lines
- Map manager improvements for Cross Sections

### Removed
- method_to_map.py
- vectorize.py

## [0.1.11] 09 FEB 2023 

### Fixed
- Desgin Form bug fixed

### Changed
- Schema updated to support design layers

## [0.1.10] 

### Added
- Most Recently Used (MRU) Project Menu
- Add Google Satellite basemap on project load if ToC is empty
- user can clip regular mask by aoi when importing existing regular mask
- double click layer adds method to Data Capture Event
- Add Representation to events (includes lookup table and event table schema update)

### Fixed
- Clip rasters with aoi mask when copying
- Spatial refrence for centerline preview layers
- Copy feature class bug when output geopackage already exists
- vertical spacing in Data Capture Events form
- added missing non-spatial tables to gpkg_contents

### Changed
- Basemaps node removed for now (will add back in with riverscapes map manager integration)
- Reorganize toc layer order
- Reorganzie Tree menu
- Mask menu order
- New project browser folder title
- Custom project file name
- Create new project as QTask, additional user feedback during new project creation
- aoi masks saved in aoi_features layer instead of mask_features layer
- user can specify single date or date range in dce

## 0.0.1

First version. Everything is new. Everything is fine.