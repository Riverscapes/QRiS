# QRiS Plugin

## ]1.1.10] 2025 SEP 23

### Fixed
- Cannot close Analysis dock panel #793
- Fix check url if input is not a string
- Export Project with Planning Container Error #794
- Fix bug when not including analyses in export


## [1.1.9] 2025 SEP 19

### Fixed
- Error when metric has no description #763
- Some projects failing to fully export #751
- Project Bounds Not Updating When Exporting QRiS Project #764
- Problem exporting Climate Engine timeseries #731
- QRiS Basemaps should respect the Region setting from RViewer #726

### Added
- Allow Import from any non-project ToC Layer #634

### Changed
- Analysis dock panel is now locked down to avoid QGIS crash.
- Increment QRiS dependency to QViewer 1.0.4 #781


## [1.1.8] 2025 AUG 29

### Fixed
- QRiS: Critical Error when updating Plugin to 1.1.7 #750

## [1.1.7] 2025 AUG 21

### Added
- Ability to add new As-Built/Design protocols #679

### Fixed
- Fix RSViewer plugin dependency version #725
- Export failing to populate attribute fields in RSViewer #677
- Bug when trying to create new analysis and no sample frames exist in project
- QRiS Projects With Attachments Won't Export to Riverscapes Project #741

### Changed
- Change how rsxml module is imported #655
- Export improvements: include valley bottom option for bounds, set aoi option as default
- Rework export path as stopgap prior to implementing project.rs.xml file

## [1.1.6] 2025 JUL 25

### Added
- Add Link to Search Data Exchange for nearby RS Projects #664
- Add Attachments to QRiS Projects #663
- Add generic "proportion" calculation to metrics #687

### Changed
- Improve logging message when trying to load rsxml module

## [1.1.5] 2025 JUL 11

### Fixed
- Fix structure and active valley metrics #666
- Zonal Statistics error with xyz/web services; Add export function #665
- Export to Riverscapes Project bug #655
- Remove Beta phase language in About from #654

## [1.1.4] 2025 JUL 03

### Fixed
- Date Widget Bug on Climate Engine Map Tile Form #661


### Fixed
- Climate Engine Not Working due to missing manifest file #657

## [1.1.3] 2025 JUL 03

### Fixed
- Error When Trying to Update Properties for As-Builts #656, #657
- Climate Engine Not Working due to missing manifest file #657


## [1.1.2] 2025 JUN 20

### Added
- Support for importing features from geojson files #644

### Fixed
- Features not deleting when Layer is Deleted from DCE #646
- Broken documentation links

### Changed
- Better centerline error message #609
- Allow raster slider to produced non-smoothed polygons as output #628

## [1.1.1] 2025 JUN 09

### Fixed
- Import DCE Attribute Mangement improvements and bug fix #579, #566
- Error if metadata field for a feature is null in 'Batch Edit QRiS Attributes' #630
- Error when deleting empty layer from DCE #616
- Raster Source Appears as Numeric Values When Exporting from Riverscapes Viewer to QRiS #645
- Default event representation should be None, not 0


## [1.1.0] 2025 JUN 02

### Added
- Protocol Library for adding DCE layers and metrics to a project
- Add Logical Attribute Fields to Metadata Widget #285
- Slider Widget for DCE Layer Attributes #571
- Allow mulitple values for list fields (as checkbox) and support for field visibility #572
- Re-added Brat CIS Protocol #569 
- Beaver Census Protocol #551
- Added Climate Engine XYZ Map Tiles
- DCE Layer Details
- Local Folder for Protocols
- Added additonal pathways to get to analysis summary #624
- Label DCE Points in Time on Climate Engine Graphs #626
- Add Warning when Calculating Sinuosity if lines run outside of sample frame #516
- Add metric details form to metrics #637
- Allow multiple count fields in metrics #637

### Fixed
- Unable to import existing valley bottom shapefile #568
- Error When Trying to Import Temporary Layers as a Valley Bottom #580
- Misspelling of 'Geomorphic Unit Extents' under DCE #577
- Fixed valley bottom id for analyses on migration
- Add To Map error for Analysis and Planning Containers
- Fix new project path when browsing to different folder.
- Analysis properties form not displaying and metric calculation errors if valley bottom is None
- Bug when event rasters not in project (i.e. from export)

### Changed
- Migrations for protocols, layers, metrics to support protocol library
- Making Input Values and Channel Type match for 'Active Channel Lines' when Importing into QRiS #578
- Issues with manual metric entry #557
- Climate Engine API Update #612
- Prevent metric calculations when required layers are missing from DCE


## [1.0.11] 2025 APR 10

### Added
- hand symbology for detrended surfaces

### Fixed
- Unstable RSXML module import causes QGIS to crash
- Prevent project bounds consisting of a single point or line during export #610

### Changed
- Riverscapes Viewer dependency updated to >= 1.0.3


## [1.0.10] 2025 MAR 12

### Fixed
- Import features error when clip geom is of type multipolygon #589 #531
- Error opening DCE properties with migrated valley bottoms #573
- Import Valley Bottom from Temporary Layer or Shapefile Bug #568, #580
- Cleaned up aoi and valley bottom views for exported projects
- Fixed error with valley bottom migration if vb_features does not exist

### Changed
- Use RS Layer name instead of fc name for Import to QRiS #590

### Removed
- Removed old unused dce layer configuration functions


## [1.0.9] 2025 JAN 24

### Added
- Allow clip to AOI when importing existing feature class into DCE layer #562

### Fixed
- Bugs with AOI properties form (unique name constraints)
- Promote to Valley Bottom Icon
- Fix Virtual Area Fields and VB,AOI field fixes #564
- Mapping multiple fields in an existing feature class to DCE Layer causes error #552

### Changed
- Analysis allow for metrics to be calculated for AOI's and Valley Bottoms #561
- Add AOI's and Valley Bottoms to Climate Engine #561
- Import Field Mapping Form improvements #552


## [1.0.8] 2025 JAN 14

### Added
- Add Clip Option when importing valley bottom features from temporary layer #555

### Fixed
- Resizing Analysis Window Causes Crash #535
- Promote watershed delineation to AOI bug #554
- Bug with message log when exporting project #558
- Bug with plotting non-numeric values in stream gage data #553

### Changed
- AOIs and VBs now stored in db as Sample Frames to support future metric capability #550
- Clean up migration code so it rolls back properly if an error occurs
- Do not recreate legacy layers when opening an existing project


## [1.0.7] 2024 DEC 13

### Fixed
- Added Missing Valley Bottom Symbology #548
- Fix First Time Creating New Project Bug #545
- Adding WMS as Surface Throws Error #544

## [1.0.6] 2024 DEC 06

### Added
- Specify a default export folder in settings #537

### Fixed
- Bug with missing DCE Layer Features in project export #539
- Update Project path on browse to path button on New Project Form #538
- Bug with Ignore Fields radio button on Import Features Form #542


## [1.0.5] 2024 NOV 15

### Added
- Ability to sort rasters by type or metadata tags #523

### Changed
- Climate Engine API changes #532


## [1.0.4] 2024 NOV 01

### Added
- Added transactions to speed up import feature classes

### Fixed
- Promote to AOI metadata bug
- Metadata bug fixes (promote to aoi, import from RS project)
- Bug with import feature class if source and dest DataSource are the same.

### Changed
- Change "Watershed Catchments" to "Catchment Delineation(s)" and add layer group when adding to map #527
- Promote catchment to AOI as single feature instead of exploding geometry.


## [1.0.3] 2024 OCT 25

### Fixed
- QRIS plugin fails to load for older versions of QGiS #522

### Changed
- Switch Create Project Workflow #514
- QRiS System metadata visible by default


## [1.0.2] 2024 OCT 23

### Added
- Show "System" metadata to the user. #498
- Batch edit feature attributes #480

### Fixed
- Bug with analysis in project export
- Limit metric selection to only what metrics are selected for analysis in the Analysis Explorer #510
- Analysis Properties form not loading metric/indicator status

### Changed
- Climate Engine Explorer Improvements #515


## [1.0.1] 2024 OCT 08

### Added
- Mirror properties/metadata when automatically creating hillshade #470
- Move metadata along with layer when the layer is promoted to another feature #439

### Fixed
- Raster slider export polygon not working #511
- Riverscapes logo on plugin #280
- Allow importing features from File Geodatabases #502
- Metadata tab stability improvements


## [1.0.0] 2024 SEPT 19

### Added
- Additional Tool Tips #200

### Fixed
- Create Sample Frames form bugs #506
- Analysis over Time not working in Analysis Explorer #463
- Better display of date labels in Analysis Exlorer #464

### Changed
- Better Aquisition Date usability for Import Raster Form #469

### Removed
- Experimental plugin designation #496


## [0.9.5] 2024 SEPT 18

### Added
- Clickable metadata hyperlinks #250
- Source Project URL added when a layer is imported from Riverscapes Viewer #349

### Fixed
- Structural Elements attribute form logic #304
- Wrong Unit Conversions for Analyses Metrics table #503

### Changed
- Modified Export Project form to enhance user experience when exporting an existing project #363

### Removed
- Brat Vegtation Suitability Layer #455


## [0.9.4] 2024 SEPT 17

### Added
- Added the generate centerline tool to Riverscapes Valley Bottoms #440
- Allow cross section clipping to be VB Polygon from Riverscapes Node #441
- Structural Elements form updated to include attributes based on logic #304
- Ability to update existing project export #363

### Fixed
- Error importing existing profiles when using mask/AOI clip #472
- Metrics Failing to update due to Unique name constraint #491
- Error when trying to edit properties of DCE (As Built) #451

### Changed
- Moved QRiS Symbology folder to RiverscapesStudio resources folder #487
- Changes to Vegetation Extents layer #455
- Changes to Geomorphic Units Layers #466
- Make Sample Frames 'create from QRIS features' defualt polygon layer to Riverscapes node Valley Bottom #443

### Removed
- Removed the generate centerline tool from Context Polygons #440
- Temporarily disbale BRAT CIS layers #454


## [0.9.3] 2024 SEPT 11

### Fixed
- Metrics fail to update due to Unique Constraint Violation #491
- Missing Sample Frame Features in project export
- Delete unused event rasters in project export

### Changed
- Improved environment loading
- RS Viewer dependency updated to 0.9.4

### Removed
- RSXML Module (replaced with Riverscapes Viewer dependency)

## [0.9.2] 2024 SEPT 05

### Added
- Valley Bottoms to project export

### Fixed
- Project Export Bug with Pour Points in project
- Bug when opening project when a context raster is associated with an event
- Added missing tables to gpkg_contents

## [0.9.1] 2024 AUG 30

### Added
- Metric Calculations for Riverscape Length and Area (ability to calculate metrics from user selected 'inputs' layers) #478

### Fixed
- Centerline not appearing in 'Create Sample Frame from QRIS features' until closing and reopening project #444
- Cannot import temporary layer into Sample Frame #471

### Changed
- Change "Calculate All" text to "Calculate" in Analysis #465
- Better DCE chooser for Basis for Design on Designs Form #482
- Uncalculated metrics now show up as null in the analysis table #477


## [0.9.0] 2024 AUG 23

### Added
- Planning Container for DCEs #473
- Date Label attribute for DCEs #479
- New layers for Beaver Dam Censusing #448

### Fixed
- Don't collapse Data Capture Events node on project tree after every 'Add DCE' event #474
- Overlapping checkboxes on Import Surfaces From #468

### Changed
- Risk Potential Layers moved to DCE's #473
- Several Layer updates for upcoming LTPBR 2.0:
  - Vegetation Extents #455
  - Dam Crests #457
  - Centerlines #458
  - Active Channels #459
  - Inundation #461
  - Geomorphic Units Layers #460, #466
  - Risk Potential Layers #467
  - CEM Layer #332
  - Structure Types #297

### Removed
- Planning DCEs #473
- Representation attribute in DCEs #479


## [0.3.27] 2024 AUG 09

### Fixed
- Attribute Bug on New DCE Layer Feature Creation #442
- Fix bug when exporting project for upload to Riverscapes Data Exchange #419

### Changed
- Update rsxml to 2.0.6
- Housekeeping: Move metadata widget to widgets folder

## [0.3.26] 2024 JUL 02

### Added
- Promote Line Scratch Vector to Profile #424

### Fixed
- Attribute values not reseting to default when changing between features in DCE feature form
- Migration Error for MacOS #432
- Error when exporting all Metric Values from Analysis #430
- Edit DCE Properties Error #321
- Sample Frame Form bugs #421 and #422

### Changed
- Metadata Field Widget now uses MultiLineText for notes #429
- Do not include Planning Layers in a Data Capture Event


## [0.3.25] 2024 JUN 28

### Added
- Riverscapes Valley Bottoms as new Input type
- DCE Properties form allows for specifying associated valley bottoms #398
- Initial Analysis Summary Explorer

### Changed
- Allow for metric definitions to be updated
- Provide modifications to design as-built form #268
- Provide modifications to design properties form #267


## [0.3.24] 2024 JUN 20

### Added
- User friendly variable descriptions for Climate Engine Explorer #383
- Import Metric Definitions using Riverscapes Viewer #426

### Fixed
- Missing Planning layers for Planing DCE

## [0.3.23] 2024 JUN 10

### Added
- Planning Layers and DCE type #391
- Select all / none buttons for metrics on create analysis form #414
- Add select all/none button for layers in Export Project form
- Metric units and unit conversions #415

### Fixed
- Fix type for Remove Layer setting on project close #418
- Analysis Bugs #417
- Export project bug with sample frames #308
- Error when trying to go to properties of a watershed catchment #420
- Error promoting context polygon to Sample Frame #423
- Bug when opening Sample Frame Properties Form

### Changed
- Ignore stream gages during project export
- Better descriptions for Analysis Icons #386
- Improved signal/slot connections for Analysis Form


## [0.3.22] 2024 MAY 30

### Added
- Add a source dropdown in surfaces properties. #395

### Fixed
- Adding a Null geometry to envelope causes null envelope error when exporting project #308

### Changed
- Skip empty DCE layers when exporting QRIS project #409

## [0.3.21] 2024 MAY 24

### Added
- Sort by Date for DCE's in Project Tree #392
- Sort by Date and Raster Type for Surfaces in Project Tree #393
- Remove all project layers on project close option in settings #314
- Add associated surfaces when layer is added to map #387
- Attribute Value Mapping when importing from Temporary Layer #323
- Populate Climate Engine Metadata Tab #400
- Full Date Range button for Climate Engine Explorer chart
- Add Orthomosaic and Satellite as Raster Types #384

### Fixed
- Export Project bug when no metrics are in analysis
- Bug when importing temporary layers #226
- Error When Trying to Import Existing Feature Layer as Sample Frame #362
- Metadata DCE type in project.rs.xml is wrong for AsBuilts #406
- Visualization issues for some Climate Engine timeseries #382
- Fix project export spatial views for symbology #40-5

### Changed
- Refactored ImportTemporaryLayer to better match ImportFeatureClass


## [0.3.20] 2024 MAY 17

### Added
- Right Click delete for downloaded stream gages and climate engine metrics
- Provide descriptions of Climate Engine variables as url link #383
- Add edit button to left of metric calculations in Analysis #255
- Add 'Remove All' button to regular DCE #388
- Double click layer in project tree adds to map #390
- Sort DCE and surfaces by name

### Fixed
- Bug preventing Climate Engine data export
- Error when no Stream Gages found to download #376
- Stream Gage error if map layer not in map #377
- Watershed Cachements/StreamStats Error #378
- Error When Generating Sample Frames from Cross Sections #361

### Changed
- Better stream gage download messages
- Make Sample Frames appear above Surfaces when Added to QGIS #381
- Specify geometry type for duplicates in available layers for regular DCE #389
- update project export project type to Riverscapes Studio

### Removed
- Remove gpkg references to old lookup tables


## [0.3.19] 2024 MAY 09

### Added
- Climate Engine Explorer

## [0.3.18] 2024 MAY 01

### Added
- Stream Gage Explorer

## [0.3.17] 2024 APR 17

### Fixed
 - Bug when creating manual cross sections
 - Duplicate Metadata warning when imorting Riverscapes layers from Viewer
 - Bug when importing temporary layer to cross sections
 - Update Zonal statistics tool help url link

### Changed
- Temporarily disabled Zonal Statistics Tool settings (units not currently implemented)

### Added
- Re-added length and area virtual fields to dce layers

## [0.3.16] 2024 APR 11

### Fixed
- Better handling of RS project metadata
- Failure adding metadata to surface on import

### Changed
- initialize MetadataWidget on toolbar load

## [0.3.15] 2024 APR 09

### Added
- Area Proportion metric calculation
- Ablilty to delete metrics from the project

## [0.3.14] 2024 MAR 27

### Added
- First version of custom metrics tool
- JSON Schema for custom metrics
- JSON metric definition files for jam and dam densities

### Fixed
- Basemap url bug in QGIS 3.30+
- DCE Event layer text does not update when DCE layer is imported

### Changed
- Max Cross Section length changed to 5km

## [0.3.13] 2024 MAR 01

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

## [0.3.12] 2024 FEB 13

### Fixed
- Fix tuple typing bug that prevented installation on some systems

## [0.3.11] 2024 FEB 12

### Fixed
- Reenable Import Temporary Layer to aoi and sample frames
- Reenable Promote Catchments to AOI

### Added
- Promote Context Vector Polygons to Sample Frames

## [0.3.10] 2024 FEB 09

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

## [0.3.9] 2024 JAN 30

### Changed
- Layer names changed to remove parentheses
- Updated user messages when importing dce feature classes

### Fixed
- Spelling error with Structure Type list
- Bug when loading surfaces in project tree prevents project from opening

## [0.3.8] 2024 JAN 25

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

## [0.3.7] 2024 JAN 12

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