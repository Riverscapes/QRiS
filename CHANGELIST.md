# QRiS Plugin

## [0.2.4] 2023 AUG 13

### Added
- Add Delete Right-Click to Watershed Catchments
- Ability to import temporary layers to qris project

### Changed
- Disabled exporting metrics table to excel format (temporary)
- Right Click "Edit" menu changed to "Properties" and associated window titles fixed

## [0.2.3] 2023 AUG 15

### Added
- Export Metrics Table to csv, json, or xlsx

### Fixed
- Bug when saving DCE properties
- Window title for Calculate All Metrics Form
- Analysis table column size depreication warning.

## [0.2.2] 2023 AUG 4

### Added
- Promote scratch vector to AOI

### Fixed
- Bug with missing json import when creating new project

### Changed
- Dockable window improvements and form updates
- Copy Feature Class Task depreciated in favor of using the updated import feature class task
- First cross section is now at the at the first interval of the spacing distance, not the start of centerline.

## [0.2.1] 2023 JUL 28

### Added
- Import Feature Class to Data Capture Event
- Promote Watershed Catchment to AOI mask
- View and edit project metadata in project properties form

### Fixed
- Window does not close when editing project properties

### Changed
- Depricated import mask function (replaced with import feature class task)
- Relaxed rules for empty values in suggested metadata

## [0.2.0] 2023 JUL 14

### Added
- Compression for copy rasters
- Tool Tips for analysis, centerlines and cross sections
- Metadata widget for raster import

### Fixed
- Bug with path utilities import
- Able to change raster type after import

## [0.5.0] 2023 APR 21

### Added
- Help button and description for Metrics
- Units to metric values (as lookup table)
- Status icons for analysis table
- Calcuate all button and logic form
- Metric vs Indicator filter on analysis Form
- Tolerance and display settings for metric values
- Brat CIS schema and model
- Import Riverscapes Metadata from QRave
- Documentation buttons added to Metric selection from 
- metadata field added to all tables in gpkg
- QRIS project Database migration versioning
- Raster Symbology added to qris

### Changed
- Qrave (QRV) integration
- Moved analysis table to the right side dock
- More explicit closing of dock widgets
- Added orphaned layers and hid design layers from DCE form
- All forms have help button with web documentation stubbed out
- Remove 'mask' terminology from qrs
- Basemaps now derived from QRave
- zoom to layer extent if no other layers are in map (other than basemap)
- Disabled Stream Flow Stats (temporarily)
- Adding DEM to map will automatically add hillshade if it exists

### Fixed
- Clip raster to AOI when importing
- Analysis Frame and event fixes
- Clear metic values when sample frame is changed 
- Gradient metric bug with spatial reference
- Bug when importing sampling frame with aoi mask
- Saving and Loading metric value uncertainty
- Cleaned up windows paths
- Improved Brat CIS context buffer
- bug when rejecting export raster slider

## [0.1.15] 2023 MAR 22

### Fixed
- Clipping vector on import bug
- Set Qrave dependency in metatdata.txt

## [0.1.14] 2023 MAR 21

### Added
- QRave plugin dependency
- Import Riverscapes Layer from QRave into QRiS as Context layers
- Open an existing Analysis
- Automated metrics (Sinuosity, Gradient)
- Add hillshade to DEM
- Initial raster type dropdown is derived from raster tname when importing
- Limit one DEM per DCE

### Fixed
- Analysis column size on window resize
- Analysis Table read-only
- Centerline error when polygon projection is not EPSG 4326
- Not implemented message when adding transect profiles
- Raster Slider layer picker window bug
- Event layers duplicated when editing surfaces in event properties
- Event layers in project tree removed when removed from event properties

### Changed
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