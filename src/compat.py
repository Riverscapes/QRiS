"""Qt 5 / Qt 6 (QGIS 3 / QGIS 4) enum compatibility constants.

In Qt 6 / PyQt6, enums are scoped (e.g. ``Qt.AlignmentFlag.AlignCenter``).
In Qt 5 / PyQt5, they were flat (``Qt.AlignCenter``).  Import the constants
you need from this module rather than accessing ``Qt`` directly.

All shared enum shims live here.  **Do not** duplicate ``USER_ROLE`` or
other guards in individual source files — import from this module instead.
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QDialogButtonBox,
    QFrame,
    QHeaderView,
    QMessageBox,
    QSizePolicy,
)

try:
    # ── Qt 6 / PyQt6 ──────────────────────────────────────────────────────
    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    ALIGN_LEFT = Qt.AlignmentFlag.AlignLeft
    ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
    ALIGN_VCENTER = Qt.AlignmentFlag.AlignVCenter
    RICH_TEXT = Qt.TextFormat.RichText
    CHECKED = Qt.CheckState.Checked
    UNCHECKED = Qt.CheckState.Unchecked
    ITEM_FLAG_CHECKABLE = Qt.ItemFlag.ItemIsUserCheckable
    ITEM_FLAG_ENABLED = Qt.ItemFlag.ItemIsEnabled
    HORIZONTAL = Qt.Orientation.Horizontal
    VERTICAL = Qt.Orientation.Vertical
    ASCENDING_ORDER = Qt.SortOrder.AscendingOrder
    LEFT_DOCK = Qt.DockWidgetArea.LeftDockWidgetArea
    RIGHT_DOCK = Qt.DockWidgetArea.RightDockWidgetArea
    TOOL_BTN_TEXT_BESIDE = Qt.ToolButtonStyle.ToolButtonTextBesideIcon
    TOOL_BTN_TEXT_ONLY = Qt.ToolButtonStyle.ToolButtonTextOnly
    SCROLL_BAR_ALWAYS_OFF = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    TEXT_BROWSER_INTERACTION = Qt.TextInteractionFlag.TextBrowserInteraction
    FOREGROUND_ROLE = Qt.ItemDataRole.ForegroundRole
    COLOR_BLUE = Qt.GlobalColor.blue
    COLOR_GRAY = Qt.GlobalColor.gray
    DIALOG_BTN_CLOSE = QDialogButtonBox.StandardButton.Close
    CUSTOM_CONTEXT_MENU = Qt.ContextMenuPolicy.CustomContextMenu
    USER_ROLE = Qt.ItemDataRole.UserRole
except AttributeError:
    # ── Qt 5 / PyQt5 ──────────────────────────────────────────────────────
    ALIGN_CENTER = Qt.AlignCenter  # type: ignore[attr-defined]
    ALIGN_LEFT = Qt.AlignLeft  # type: ignore[attr-defined]
    ALIGN_RIGHT = Qt.AlignRight  # type: ignore[attr-defined]
    ALIGN_VCENTER = Qt.AlignVCenter  # type: ignore[attr-defined]
    RICH_TEXT = Qt.RichText  # type: ignore[attr-defined]
    CHECKED = Qt.Checked  # type: ignore[attr-defined]
    UNCHECKED = Qt.Unchecked  # type: ignore[attr-defined]
    ITEM_FLAG_CHECKABLE = Qt.ItemIsUserCheckable  # type: ignore[attr-defined]
    ITEM_FLAG_ENABLED = Qt.ItemIsEnabled  # type: ignore[attr-defined]
    HORIZONTAL = Qt.Horizontal  # type: ignore[attr-defined]
    VERTICAL = Qt.Vertical  # type: ignore[attr-defined]
    ASCENDING_ORDER = Qt.AscendingOrder  # type: ignore[attr-defined]
    LEFT_DOCK = Qt.LeftDockWidgetArea  # type: ignore[attr-defined]
    RIGHT_DOCK = Qt.RightDockWidgetArea  # type: ignore[attr-defined]
    TOOL_BTN_TEXT_BESIDE = Qt.ToolButtonTextBesideIcon  # type: ignore[attr-defined]
    TOOL_BTN_TEXT_ONLY = Qt.ToolButtonTextOnly  # type: ignore[attr-defined]
    SCROLL_BAR_ALWAYS_OFF = Qt.ScrollBarAlwaysOff  # type: ignore[attr-defined]
    TEXT_BROWSER_INTERACTION = Qt.TextBrowserInteraction  # type: ignore[attr-defined]
    FOREGROUND_ROLE = Qt.ForegroundRole  # type: ignore[attr-defined]
    COLOR_BLUE = Qt.blue  # type: ignore[attr-defined]
    COLOR_GRAY = Qt.gray  # type: ignore[attr-defined]
    DIALOG_BTN_CLOSE = QDialogButtonBox.Close  # type: ignore[attr-defined]
    CUSTOM_CONTEXT_MENU = Qt.CustomContextMenu  # type: ignore[attr-defined]
    USER_ROLE = Qt.UserRole  # type: ignore[attr-defined]


# ── QFrame shape / shadow ────────────────────────────────────────────────────
try:
    # Qt 6 / PyQt6 — scoped enums
    QFRAME_NO_FRAME = QFrame.Shape.NoFrame
    QFRAME_BOX = QFrame.Shape.Box
    QFRAME_PANEL = QFrame.Shape.Panel
    QFRAME_STYLED_PANEL = QFrame.Shape.StyledPanel
    QFRAME_HLINE = QFrame.Shape.HLine
    QFRAME_VLINE = QFrame.Shape.VLine
    QFRAME_WIN_PANEL = QFrame.Shape.WinPanel
    QFRAME_RAISED = QFrame.Shadow.Raised
    QFRAME_SUNKEN = QFrame.Shadow.Sunken
    QFRAME_PLAIN = QFrame.Shadow.Plain
except AttributeError:
    # Qt 5 / PyQt5 — flat enums
    QFRAME_NO_FRAME = QFrame.NoFrame  # type: ignore[attr-defined]
    QFRAME_BOX = QFrame.Box  # type: ignore[attr-defined]
    QFRAME_PANEL = QFrame.Panel  # type: ignore[attr-defined]
    QFRAME_STYLED_PANEL = QFrame.StyledPanel  # type: ignore[attr-defined]
    QFRAME_HLINE = QFrame.HLine  # type: ignore[attr-defined]
    QFRAME_VLINE = QFrame.VLine  # type: ignore[attr-defined]
    QFRAME_WIN_PANEL = QFrame.WinPanel  # type: ignore[attr-defined]
    QFRAME_RAISED = QFrame.Raised  # type: ignore[attr-defined]
    QFRAME_SUNKEN = QFrame.Sunken  # type: ignore[attr-defined]
    QFRAME_PLAIN = QFrame.Plain  # type: ignore[attr-defined]


# ── QSizePolicy ───────────────────────────────────────────────────────────────
try:
    SPSZ_FIXED = QSizePolicy.Policy.Fixed
    SPSZ_MINIMUM = QSizePolicy.Policy.Minimum
    SPSZ_PREFERRED = QSizePolicy.Policy.Preferred
    SPSZ_EXPANDING = QSizePolicy.Policy.Expanding
    SPSZ_MINIMUM_EXPANDING = QSizePolicy.Policy.MinimumExpanding
    SPSZ_IGNORED = QSizePolicy.Policy.Ignored
except AttributeError:
    SPSZ_FIXED = QSizePolicy.Fixed  # type: ignore[attr-defined]
    SPSZ_MINIMUM = QSizePolicy.Minimum  # type: ignore[attr-defined]
    SPSZ_PREFERRED = QSizePolicy.Preferred  # type: ignore[attr-defined]
    SPSZ_EXPANDING = QSizePolicy.Expanding  # type: ignore[attr-defined]
    SPSZ_MINIMUM_EXPANDING = QSizePolicy.MinimumExpanding  # type: ignore[attr-defined]
    SPSZ_IGNORED = QSizePolicy.Ignored  # type: ignore[attr-defined]


# ── QDialogButtonBox standard buttons and roles ───────────────────────────────
try:
    DLGBTN_OK = QDialogButtonBox.StandardButton.Ok
    DLGBTN_CANCEL = QDialogButtonBox.StandardButton.Cancel
    DLGBTN_APPLY = QDialogButtonBox.StandardButton.Apply
    DLGBTN_RESET = QDialogButtonBox.StandardButton.Reset
    DLGBTN_ROLE_APPLY = QDialogButtonBox.ButtonRole.ApplyRole
    DLGBTN_ROLE_RESET = QDialogButtonBox.ButtonRole.ResetRole
    DLGBTN_ROLE_HELP = QDialogButtonBox.ButtonRole.HelpRole
    DLGBTN_ROLE_ACTION = QDialogButtonBox.ButtonRole.ActionRole
except AttributeError:
    DLGBTN_OK = QDialogButtonBox.Ok  # type: ignore[attr-defined]
    DLGBTN_CANCEL = QDialogButtonBox.Cancel  # type: ignore[attr-defined]
    DLGBTN_APPLY = QDialogButtonBox.Apply  # type: ignore[attr-defined]
    DLGBTN_RESET = QDialogButtonBox.Reset  # type: ignore[attr-defined]
    DLGBTN_ROLE_APPLY = QDialogButtonBox.ApplyRole  # type: ignore[attr-defined]
    DLGBTN_ROLE_RESET = QDialogButtonBox.ResetRole  # type: ignore[attr-defined]
    DLGBTN_ROLE_HELP = QDialogButtonBox.HelpRole  # type: ignore[attr-defined]
    DLGBTN_ROLE_ACTION = QDialogButtonBox.ActionRole  # type: ignore[attr-defined]


# ── QMessageBox standard buttons and icons ────────────────────────────────────
try:
    MSGBOX_BTN_YES = QMessageBox.StandardButton.Yes
    MSGBOX_BTN_NO = QMessageBox.StandardButton.No
    MSGBOX_ICON_QUESTION = QMessageBox.Icon.Question
    MSGBOX_ICON_WARNING = QMessageBox.Icon.Warning
    MSGBOX_ICON_CRITICAL = QMessageBox.Icon.Critical
    MSGBOX_ICON_INFORMATION = QMessageBox.Icon.Information
except AttributeError:
    MSGBOX_BTN_YES = QMessageBox.Yes  # type: ignore[attr-defined]
    MSGBOX_BTN_NO = QMessageBox.No  # type: ignore[attr-defined]
    MSGBOX_ICON_QUESTION = QMessageBox.Question  # type: ignore[attr-defined]
    MSGBOX_ICON_WARNING = QMessageBox.Warning  # type: ignore[attr-defined]
    MSGBOX_ICON_CRITICAL = QMessageBox.Critical  # type: ignore[attr-defined]
    MSGBOX_ICON_INFORMATION = QMessageBox.Information  # type: ignore[attr-defined]


# ── QHeaderView resize modes ──────────────────────────────────────────────────
try:
    HEADER_STRETCH = QHeaderView.ResizeMode.Stretch
    HEADER_RESIZE_TO_CONTENTS = QHeaderView.ResizeMode.ResizeToContents
    HEADER_INTERACTIVE = QHeaderView.ResizeMode.Interactive
    HEADER_FIXED = QHeaderView.ResizeMode.Fixed
except AttributeError:
    HEADER_STRETCH = QHeaderView.Stretch  # type: ignore[attr-defined]
    HEADER_RESIZE_TO_CONTENTS = QHeaderView.ResizeToContents  # type: ignore[attr-defined]
    HEADER_INTERACTIVE = QHeaderView.Interactive  # type: ignore[attr-defined]
    HEADER_FIXED = QHeaderView.Fixed  # type: ignore[attr-defined]


# ── QAbstractItemView edit triggers ──────────────────────────────────────────
try:
    # Qt 6 / PyQt6 — scoped enum
    QABSTRACTITEMVIEW_NO_EDIT_TRIGGERS = QAbstractItemView.EditTrigger.NoEditTriggers
except AttributeError:
    # Qt 5 / PyQt5 — flat enum
    QABSTRACTITEMVIEW_NO_EDIT_TRIGGERS = QAbstractItemView.NoEditTriggers  # type: ignore[attr-defined]


from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest

try:
    # Qt 6 / PyQt6
    NET_CONTENT_LENGTH_HEADER = QNetworkRequest.KnownHeaders.ContentLengthHeader
    NET_OP_CANCELED_ERROR = QNetworkReply.NetworkError.OperationCanceledError
    NET_NO_ERROR = QNetworkReply.NetworkError.NoError
except AttributeError:
    # Qt 5 / PyQt5
    NET_CONTENT_LENGTH_HEADER = QNetworkRequest.ContentLengthHeader  # type: ignore[attr-defined]
    NET_OP_CANCELED_ERROR = QNetworkReply.OperationCanceledError  # type: ignore[attr-defined]
    NET_NO_ERROR = QNetworkReply.NoError  # type: ignore[attr-defined]


# ── QGIS API compatibility ────────────────────────────────────────────────────
from qgis.core import Qgis, QgsMapLayer, QgsTask, QgsUnitTypes, QgsVectorFileWriter

try:
    # QGIS 4 / PyQt6 — scoped flag form
    QGSTASK_CAN_CANCEL = QgsTask.Flag.CanCancel
except AttributeError:
    # QGIS 3 / PyQt5 — flat flag form
    QGSTASK_CAN_CANCEL = QgsTask.CanCancel  # type: ignore[attr-defined]

try:
    # QGIS 4 / PyQt6 — suppresses OS-level completion notifications
    QGSTASK_SILENT = QgsTask.Flag.Silent
except AttributeError:
    # QGIS 3 does not have this flag; fall back to zero (no-op OR)
    QGSTASK_SILENT = 0  # type: ignore[assignment]

try:
    # QGIS 4 / PyQt6
    QGSTASK_COMPLETE = QgsTask.TaskStatus.Complete
except AttributeError:
    # QGIS 3 / PyQt5
    QGSTASK_COMPLETE = QgsTask.Complete  # type: ignore[attr-defined]

try:
    # QGIS 4 / PyQt6
    VFW_NO_ERROR = QgsVectorFileWriter.WriterError.NoError
except AttributeError:
    # QGIS 3 / PyQt5
    VFW_NO_ERROR = QgsVectorFileWriter.NoError  # type: ignore[attr-defined]

try:
    # QGIS 3.26+ and QGIS 4+: canonical Qgis namespace.
    # ``Qgis::LayerType`` was introduced in QGIS 3.26 and is the *only*
    # reliable form in QGIS 4.  The old ``QgsMapLayer.LayerType.VectorLayer``
    # path relied on a SIP_MONKEYPATCH_SCOPEENUM_UNNEST macro that is
    # deprecated in QGIS 4 and must NOT be used.
    # Note: the redundant "Layer" suffix is intentionally absent in Qt6/QGIS4
    #   (i.e. Qgis.LayerType.Vector, NOT Qgis.LayerType.VectorLayer).
    MAPLAYER_VECTOR = Qgis.LayerType.Vector
    MAPLAYER_RASTER = Qgis.LayerType.Raster
except AttributeError:
    # QGIS < 3.26: Qgis.LayerType does not exist yet; use the legacy flat
    # QgsMapLayer enum which was the only form available before 3.26.
    MAPLAYER_VECTOR = QgsMapLayer.VectorLayer  # type: ignore[attr-defined]
    MAPLAYER_RASTER = QgsMapLayer.RasterLayer  # type: ignore[attr-defined]


# ── QgsUnitTypes enum compatibility ──────────────────────────────────────────
try:
    # QGIS 4 / Qt 6 — scoped enums
    UNIT_DISTANCE_METERS = QgsUnitTypes.DistanceUnit.DistanceMeters
    UNIT_DISTANCE_KILOMETERS = QgsUnitTypes.DistanceUnit.DistanceKilometers
    UNIT_DISTANCE_FEET = QgsUnitTypes.DistanceUnit.DistanceFeet
    UNIT_DISTANCE_YARDS = QgsUnitTypes.DistanceUnit.DistanceYards
    UNIT_DISTANCE_MILES = QgsUnitTypes.DistanceUnit.DistanceMiles
    UNIT_DISTANCE_NAUTICAL_MILES = QgsUnitTypes.DistanceUnit.DistanceNauticalMiles
    UNIT_DISTANCE_MILLIMETERS = QgsUnitTypes.DistanceUnit.DistanceMillimeters
    UNIT_DISTANCE_CENTIMETERS = QgsUnitTypes.DistanceUnit.DistanceCentimeters

    UNIT_AREA_SQUARE_METERS = QgsUnitTypes.AreaUnit.AreaSquareMeters
    UNIT_AREA_SQUARE_KILOMETERS = QgsUnitTypes.AreaUnit.AreaSquareKilometers
    UNIT_AREA_SQUARE_FEET = QgsUnitTypes.AreaUnit.AreaSquareFeet
    UNIT_AREA_SQUARE_YARDS = QgsUnitTypes.AreaUnit.AreaSquareYards
    UNIT_AREA_SQUARE_MILES = QgsUnitTypes.AreaUnit.AreaSquareMiles
    UNIT_AREA_HECTARES = QgsUnitTypes.AreaUnit.AreaHectares
    UNIT_AREA_ACRES = QgsUnitTypes.AreaUnit.AreaAcres
    UNIT_AREA_SQUARE_NAUTICAL_MILES = QgsUnitTypes.AreaUnit.AreaSquareNauticalMiles
    UNIT_AREA_SQUARE_CENTIMETERS = QgsUnitTypes.AreaUnit.AreaSquareCentimeters
    UNIT_AREA_SQUARE_MILLIMETERS = QgsUnitTypes.AreaUnit.AreaSquareMillimeters

    UNIT_VOLUME_CUBIC_METERS = QgsUnitTypes.VolumeUnit.VolumeCubicMeters
    UNIT_VOLUME_CUBIC_FEET = QgsUnitTypes.VolumeUnit.VolumeCubicFeet
    UNIT_VOLUME_CUBIC_YARDS = QgsUnitTypes.VolumeUnit.VolumeCubicYards
    UNIT_VOLUME_BARREL = QgsUnitTypes.VolumeUnit.VolumeBarrel
    UNIT_VOLUME_CUBIC_DECIMETER = QgsUnitTypes.VolumeUnit.VolumeCubicDecimeter
    UNIT_VOLUME_LITERS = QgsUnitTypes.VolumeUnit.VolumeLiters
    UNIT_VOLUME_GALLON_US = QgsUnitTypes.VolumeUnit.VolumeGallonUS
    UNIT_VOLUME_CUBIC_INCH = QgsUnitTypes.VolumeUnit.VolumeCubicInch
    UNIT_VOLUME_CUBIC_CENTIMETER = QgsUnitTypes.VolumeUnit.VolumeCubicCentimeter
except AttributeError:
    # QGIS 3 / Qt 5 — flat enums
    UNIT_DISTANCE_METERS = QgsUnitTypes.DistanceMeters  # type: ignore[attr-defined]
    UNIT_DISTANCE_KILOMETERS = QgsUnitTypes.DistanceKilometers  # type: ignore[attr-defined]
    UNIT_DISTANCE_FEET = QgsUnitTypes.DistanceFeet  # type: ignore[attr-defined]
    UNIT_DISTANCE_YARDS = QgsUnitTypes.DistanceYards  # type: ignore[attr-defined]
    UNIT_DISTANCE_MILES = QgsUnitTypes.DistanceMiles  # type: ignore[attr-defined]
    UNIT_DISTANCE_NAUTICAL_MILES = QgsUnitTypes.DistanceNauticalMiles  # type: ignore[attr-defined]
    UNIT_DISTANCE_MILLIMETERS = QgsUnitTypes.DistanceMillimeters  # type: ignore[attr-defined]
    UNIT_DISTANCE_CENTIMETERS = QgsUnitTypes.DistanceCentimeters  # type: ignore[attr-defined]

    UNIT_AREA_SQUARE_METERS = QgsUnitTypes.AreaSquareMeters  # type: ignore[attr-defined]
    UNIT_AREA_SQUARE_KILOMETERS = QgsUnitTypes.AreaSquareKilometers  # type: ignore[attr-defined]
    UNIT_AREA_SQUARE_FEET = QgsUnitTypes.AreaSquareFeet  # type: ignore[attr-defined]
    UNIT_AREA_SQUARE_YARDS = QgsUnitTypes.AreaSquareYards  # type: ignore[attr-defined]
    UNIT_AREA_SQUARE_MILES = QgsUnitTypes.AreaSquareMiles  # type: ignore[attr-defined]
    UNIT_AREA_HECTARES = QgsUnitTypes.AreaHectares  # type: ignore[attr-defined]
    UNIT_AREA_ACRES = QgsUnitTypes.AreaAcres  # type: ignore[attr-defined]
    UNIT_AREA_SQUARE_NAUTICAL_MILES = QgsUnitTypes.AreaSquareNauticalMiles  # type: ignore[attr-defined]
    UNIT_AREA_SQUARE_CENTIMETERS = QgsUnitTypes.AreaSquareCentimeters  # type: ignore[attr-defined]
    UNIT_AREA_SQUARE_MILLIMETERS = QgsUnitTypes.AreaSquareMillimeters  # type: ignore[attr-defined]

    UNIT_VOLUME_CUBIC_METERS = QgsUnitTypes.VolumeCubicMeters  # type: ignore[attr-defined]
    UNIT_VOLUME_CUBIC_FEET = QgsUnitTypes.VolumeCubicFeet  # type: ignore[attr-defined]
    UNIT_VOLUME_CUBIC_YARDS = QgsUnitTypes.VolumeCubicYards  # type: ignore[attr-defined]
    UNIT_VOLUME_BARREL = QgsUnitTypes.VolumeBarrel  # type: ignore[attr-defined]
    UNIT_VOLUME_CUBIC_DECIMETER = QgsUnitTypes.VolumeCubicDecimeter  # type: ignore[attr-defined]
    UNIT_VOLUME_LITERS = QgsUnitTypes.VolumeLiters  # type: ignore[attr-defined]
    UNIT_VOLUME_GALLON_US = QgsUnitTypes.VolumeGallonUS  # type: ignore[attr-defined]
    UNIT_VOLUME_CUBIC_INCH = QgsUnitTypes.VolumeCubicInch  # type: ignore[attr-defined]
    UNIT_VOLUME_CUBIC_CENTIMETER = QgsUnitTypes.VolumeCubicCentimeter  # type: ignore[attr-defined]


# ── QClipboard ───────────────────────────────────────────────────────────────
from qgis.PyQt.QtGui import QClipboard

try:
    # Qt 6 / PyQt6 — scoped enum
    CLIPBOARD_MODE = QClipboard.Mode.Clipboard
except AttributeError:
    # Qt 5 / PyQt5 — flat enum
    CLIPBOARD_MODE = QClipboard.Clipboard  # type: ignore[attr-defined]


# ── QgsMapBoxGlStyleConverter ─────────────────────────────────────────────────
# Some QGIS builds omit this class entirely; guard with ImportError as well as
# the Qt5→Qt6 scoped-enum change on the Result enum.
try:
    from qgis.core import (
        QgsMapBoxGlStyleConverter as _QgsMapBoxGlStyleConverter,
    )

    try:
        # QGIS 4 / Qt 6 — scoped enum
        MAPBOX_GL_SUCCESS = _QgsMapBoxGlStyleConverter.Result.Success
    except AttributeError:
        # QGIS 3 / Qt 5 — flat enum
        MAPBOX_GL_SUCCESS = _QgsMapBoxGlStyleConverter.Success  # type: ignore[attr-defined]
except ImportError:
    # Not available in this QGIS build
    MAPBOX_GL_SUCCESS = None
