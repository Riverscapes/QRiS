# QRiS Plugin

## [0.3.15] 2023 APR 09

### Added
- Area Proportion metric calculation
- Ablilty to delete metrics from the project

## [0.3.14] 2023 MAR 27

### Added
- First version of custom metrics tool
- JSON Schema for custom metrics
- JSON metric definition files for jam and dam densities

### Fixed
- Basemap url bug in QGIS 3.30+
- DCE Event layer text does not update when DCE layer is imported

### Changed
- Max Cross Section length changed to 5km

## [0.3.13] 2023 MAR 01

### Fixed
- Improved export RS project stability
- Bug with project bounds extents
- "No Feature Count" raster error when traversing tree
- Make sure associated hillshade is added to map if raster is a DEM
- Make sure event layer display name is not empty when copying from existing DCE
- Resize analysis column width on to fit contents
- Remove pour point and catchment from map when deleted from project
- Remove event layer and empty parent nodes from project tree when removed or deleted from the dce
- Updated save centerline to work with metadata widget and store system metadata

### Added
- Retain symbology when importing from Riverscapes Viewer
- QRIS settings menu with ability to change default dock side
- Expand and collapse child node context menus added to project tree

### Changed
- Minimum QGIS version set to 3.28
- Metadata Widget to store three different types of metadata: system, attribute and (user) metadata

### Removed
- Unused export design as rs project form and code

## [0.3.12] 2023 FEB 13

### Fixed
- Fix tuple typing bug that prevented installation on some systems

## [0.3.11] 2023 FEB 12

### Fixed
- Reenable Import Temporary Layer to aoi and sample frames
- Reenable Promote Catchments to AOI

### Added
- Promote Context Vector Polygons to Sample Frames

## [0.3.10] 2023 FEB 09

### Fixed
- Project tree layer remains "empty" after digitizing
- Pour Point symbology
- Catchment Polygon symbology folder error
- Surfaces (rasters) symbology error
- Import Existing Vector Layer to Context bugs
- Import Temporary Layer to Context bug
- Import Profile form bug
- Re-added Add Photo to Observation Points
- Copy from Existing DCE produces Coordinate Reference Error

## [0.3.9] 2023 JAN 30

### Changed
- Layer names changed to remove parentheses
- Updated user messages when importing dce feature classes

### Fixed
- Spelling error with Structure Type list
- Bug when loading surfaces in project tree prevents project from opening

## [0.3.8] 2023 JAN 25

### Added
- Dam Density Metric
- Jam Density Metric

### Changed
- Sample Frame database schema changed
- Create new Sample Frame
- Create Sample Frame from QRiS layers
- Import Sample Frame from Feature Class
- Reset schema migrations

### Fixed
- Metadata attribute editior widget bug fixed

## [0.3.7] 2023 JAN 12

### Added
- Right click menu to add all child layers to map
- Feature Count turned on for QRiS layers
- Layer in Edit Session highlighted in Project Tree
- Project Tree opens in partially collapsed state
- Project Tree layers indicate if they are empty containers (no features)
- Check that gpkg is a valid QRiS project on opening

### Fixed
- Acknowledgements Text
- Bug when adding layer to tree in hierarchy
- Bug when exporting project with an analysis
- Import DCE Layer bug with certain invalid geometries
- Null json values cause error when opening a project
- As-Built Group placement in layer ToC

### Removed
- References to old qrave plugin

## [0.3.6] 2023 DEC 21

### Changed
- Updated schema for DCE layers
- Updated schema for As-Built Surveys
- Added default Notes field to all DCE layers
- Updated qrave integration to use Riverscapes Viewer
- Map Manager finds symbology based on logical folders (project folder, qirs resources folder, shared resources folder)
- Additional icon updates

### Fixed
- Bug with importing dce features with same name in attribute table
- Check to make sure sample frame has at lease one feature before creating or opening an analysis
- Fixed attributes not updating when digitizing features
- Fixed bug when loading attributes into Metadata Widget

## [0.3.5] 2023 DEC 14

### Changed
- Updated icons
- Help page updates

### Added
- Setup hierarchy for project tree and layer TOC 

## [0.3.4] 2023 DEC 08

### Changed
- Import Feature class task restructured
- User can export sections of qris project to riverscapes project
- DCE metadata json restructured

### Added
- Success message for project export
- Refresh layer after importing dce features (to update symbology and attribute table)
- Project checks DCE metadata structure on opening (with user option to update)
- Check for duplicate output fields when importing dce feature class

## [0.3.3] 2023 NOV 22

### Changed
- Updated layer schema for LTBPR Base

### Fixed
- bug when lookkup table is empty

### Added
- Project Tags

## [0.3.2] 2023 NOV 17

### Changed
- Update import feature class tool to store attributes in metadata json

### Fixed
- Bug with exporting rs project when no photos exist

## [0.3.1] 2023 OCT 23

### Added
- Import photos to Observation Points

### Changed
- Design layers

### Fixed
- Metadata attribute form widget retains existing values when making edits

## [0.3.0] 2023 OCT 18

### Added
- Export QrIS Project to Riverscapes XML project
- Metadata widget for editing layer attributes from json

### Changed
- DCE and design now stored as three feature classes (points, lines, polygons)
- Updated icons

## [0.2.7] 2023 SEP 12

### Added
- rsxml pip module for parsing riverscapes xml
- Export LTPBRDesign Riverscapes Project

## [0.2.6] 2023 SEP 07

### Added
- Ability to create new dce from existing dce
- Ability copy dce features from existing dce
- Import temporary layers to context

### Fixed
- Bug with transforming features from temporary layer
- Bug when importing features with empty geometry
- Thalwegs missing metadata field
- Missing warning message when dce date is invalid

## [0.2.5] 2023 SEP 01

### Added
- Metadata Widget for profiles, masks, cross sections, and context vectors
- Warning and prevent user from importing vrt rasters
- Added xls format to export metrics table
- Ability to export multiple analyses as one table

### Fixed
- Bug with Import context vectors
- Bug with promote catchments to aoi
- Make geometries valid for zonal stats tool
- Better warnings for centerline tool
- Refresh map after importing dce features
- Raster layers causign bug with edit session locking
- Clean any invalid geometries when creating catchments
### Changed
- Reworked code for export metrics table


## [0.2.4] 2023 AUG 22

### Added
- Add Delete Right-Click to Watershed Catchments
- Ability to import temporary layers to qris project

### Changed
- Limit editing to only one QRiS layer at a time (does not apply to non-QRiS layers)
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