"""Qt 5 / Qt 6 (QGIS 3 / QGIS 4) enum compatibility constants.

In Qt 6 / PyQt6, enums are scoped (e.g. ``Qt.AlignmentFlag.AlignCenter``).
In Qt 5 / PyQt5, they were flat (``Qt.AlignCenter``).  Import the constants
you need from this module rather than accessing ``Qt`` directly.

All shared enum shims live here.  **Do not** duplicate ``USER_ROLE`` or
other guards in individual source files — import from this module instead.
"""

from qgis.PyQt.QtCore import QMetaType, Qt, QVariant
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QFrame,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QSizePolicy,
    QSlider,
    QStyle,
    QToolButton,
)

try:
    # ── Qt 6 / PyQt6 ──────────────────────────────────────────────────────
    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    ALIGN_LEFT = Qt.AlignmentFlag.AlignLeft
    ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
    ALIGN_TOP = Qt.AlignmentFlag.AlignTop
    ALIGN_VCENTER = Qt.AlignmentFlag.AlignVCenter
    RICH_TEXT = Qt.TextFormat.RichText
    PLAIN_TEXT = Qt.TextFormat.PlainText
    WA_QUIT_ON_CLOSE = Qt.WidgetAttribute.WA_QuitOnClose
    CHECKED = Qt.CheckState.Checked
    UNCHECKED = Qt.CheckState.Unchecked
    PARTIALLY_CHECKED = Qt.CheckState.PartiallyChecked
    ITEM_FLAG_CHECKABLE = Qt.ItemFlag.ItemIsUserCheckable
    ITEM_FLAG_ENABLED = Qt.ItemFlag.ItemIsEnabled
    ITEM_FLAG_SELECTABLE = Qt.ItemFlag.ItemIsSelectable
    HORIZONTAL = Qt.Orientation.Horizontal
    VERTICAL = Qt.Orientation.Vertical
    ASCENDING_ORDER = Qt.SortOrder.AscendingOrder
    DESCENDING_ORDER = Qt.SortOrder.DescendingOrder
    TOOL_BTN_TEXT_BESIDE = Qt.ToolButtonStyle.ToolButtonTextBesideIcon
    TOOL_BTN_TEXT_ONLY = Qt.ToolButtonStyle.ToolButtonTextOnly
    TOOL_BTN_ICON_ONLY = Qt.ToolButtonStyle.ToolButtonIconOnly
    TOOL_BTN_INSTANT_POPUP = QToolButton.ToolButtonPopupMode.InstantPopup
    TOOL_BTN_MENU_POPUP = QToolButton.ToolButtonPopupMode.MenuButtonPopup
    SLIDER_TICKS_BELOW = QSlider.TickPosition.TicksBelow
    SCROLL_BAR_ALWAYS_OFF = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    WAIT_CURSOR = Qt.CursorShape.WaitCursor
    TEXT_BROWSER_INTERACTION = Qt.TextInteractionFlag.TextBrowserInteraction
    LINKS_ACCESSIBLE_BY_KEYBOARD = Qt.TextInteractionFlag.LinksAccessibleByKeyboard
    LINKS_ACCESSIBLE_BY_MOUSE = Qt.TextInteractionFlag.LinksAccessibleByMouse
    TEXT_SELECTABLE_BY_KEYBOARD = Qt.TextInteractionFlag.TextSelectableByKeyboard
    TEXT_SELECTABLE_BY_MOUSE = Qt.TextInteractionFlag.TextSelectableByMouse
    DISPLAY_ROLE = Qt.ItemDataRole.DisplayRole
    EDIT_ROLE = Qt.ItemDataRole.EditRole
    BACKGROUND_ROLE = Qt.ItemDataRole.BackgroundRole
    CHECK_STATE_ROLE = Qt.ItemDataRole.CheckStateRole
    FOREGROUND_ROLE = Qt.ItemDataRole.ForegroundRole
    ITEM_FLAG_EDITABLE = Qt.ItemFlag.ItemIsEditable
    NO_ITEM_FLAGS = Qt.ItemFlag.NoItemFlags
    COLOR_BLUE = Qt.GlobalColor.blue
    COLOR_GRAY = Qt.GlobalColor.gray
    COLOR_TRANSPARENT = Qt.GlobalColor.transparent
    MATCH_EXACTLY = Qt.MatchFlag.MatchExactly
    MATCH_WRAP = Qt.MatchFlag.MatchWrap
    DIALOG_BTN_CLOSE = QDialogButtonBox.StandardButton.Close
    CUSTOM_CONTEXT_MENU = Qt.ContextMenuPolicy.CustomContextMenu
    USER_ROLE = Qt.ItemDataRole.UserRole
except AttributeError:
    # ── Qt 5 / PyQt5 ──────────────────────────────────────────────────────
    ALIGN_CENTER = Qt.AlignCenter  # type: ignore[attr-defined]
    ALIGN_LEFT = Qt.AlignLeft  # type: ignore[attr-defined]
    ALIGN_RIGHT = Qt.AlignRight  # type: ignore[attr-defined]
    ALIGN_TOP = Qt.AlignTop  # type: ignore[attr-defined]
    ALIGN_VCENTER = Qt.AlignVCenter  # type: ignore[attr-defined]
    RICH_TEXT = Qt.RichText  # type: ignore[attr-defined]
    PLAIN_TEXT = Qt.PlainText  # type: ignore[attr-defined]
    WA_QUIT_ON_CLOSE = Qt.WA_QuitOnClose  # type: ignore[attr-defined]
    CHECKED = Qt.Checked  # type: ignore[attr-defined]
    UNCHECKED = Qt.Unchecked  # type: ignore[attr-defined]
    PARTIALLY_CHECKED = Qt.PartiallyChecked  # type: ignore[attr-defined]
    ITEM_FLAG_CHECKABLE = Qt.ItemIsUserCheckable  # type: ignore[attr-defined]
    ITEM_FLAG_ENABLED = Qt.ItemIsEnabled  # type: ignore[attr-defined]
    ITEM_FLAG_SELECTABLE = Qt.ItemIsSelectable  # type: ignore[attr-defined]
    HORIZONTAL = Qt.Horizontal  # type: ignore[attr-defined]
    VERTICAL = Qt.Vertical  # type: ignore[attr-defined]
    ASCENDING_ORDER = Qt.AscendingOrder  # type: ignore[attr-defined]
    DESCENDING_ORDER = Qt.DescendingOrder  # type: ignore[attr-defined]
    TOOL_BTN_TEXT_BESIDE = Qt.ToolButtonTextBesideIcon  # type: ignore[attr-defined]
    TOOL_BTN_TEXT_ONLY = Qt.ToolButtonTextOnly  # type: ignore[attr-defined]
    TOOL_BTN_ICON_ONLY = Qt.ToolButtonIconOnly  # type: ignore[attr-defined]
    TOOL_BTN_INSTANT_POPUP = QToolButton.InstantPopup  # type: ignore[attr-defined]
    TOOL_BTN_MENU_POPUP = QToolButton.MenuButtonPopup  # type: ignore[attr-defined]
    SLIDER_TICKS_BELOW = QSlider.TicksBelow  # type: ignore[attr-defined]
    SCROLL_BAR_ALWAYS_OFF = Qt.ScrollBarAlwaysOff  # type: ignore[attr-defined]
    WAIT_CURSOR = Qt.WaitCursor  # type: ignore[attr-defined]
    TEXT_BROWSER_INTERACTION = Qt.TextBrowserInteraction  # type: ignore[attr-defined]
    LINKS_ACCESSIBLE_BY_KEYBOARD = Qt.LinksAccessibleByKeyboard  # type: ignore[attr-defined]
    LINKS_ACCESSIBLE_BY_MOUSE = Qt.LinksAccessibleByMouse  # type: ignore[attr-defined]
    TEXT_SELECTABLE_BY_KEYBOARD = Qt.TextSelectableByKeyboard  # type: ignore[attr-defined]
    TEXT_SELECTABLE_BY_MOUSE = Qt.TextSelectableByMouse  # type: ignore[attr-defined]
    DISPLAY_ROLE = Qt.DisplayRole  # type: ignore[attr-defined]
    EDIT_ROLE = Qt.EditRole  # type: ignore[attr-defined]
    BACKGROUND_ROLE = Qt.BackgroundRole  # type: ignore[attr-defined]
    CHECK_STATE_ROLE = Qt.CheckStateRole  # type: ignore[attr-defined]
    FOREGROUND_ROLE = Qt.ForegroundRole  # type: ignore[attr-defined]
    ITEM_FLAG_EDITABLE = Qt.ItemIsEditable  # type: ignore[attr-defined]
    NO_ITEM_FLAGS = Qt.NoItemFlags  # type: ignore[attr-defined]
    COLOR_BLUE = Qt.blue  # type: ignore[attr-defined]
    COLOR_GRAY = Qt.gray  # type: ignore[attr-defined]
    COLOR_TRANSPARENT = Qt.transparent  # type: ignore[attr-defined]
    MATCH_EXACTLY = Qt.MatchExactly  # type: ignore[attr-defined]
    MATCH_WRAP = Qt.MatchWrap  # type: ignore[attr-defined]
    DIALOG_BTN_CLOSE = QDialogButtonBox.Close  # type: ignore[attr-defined]
    CUSTOM_CONTEXT_MENU = Qt.CustomContextMenu  # type: ignore[attr-defined]
    USER_ROLE = Qt.UserRole  # type: ignore[attr-defined]


# ── Dock widget areas ─────────────────────────────────────────────────────────
# Qt.DockWidgetArea may not be on QtCore.Qt in all QGIS PyQt6 wrappers,
# so these are split into their own try/except block.
try:
    # Qt 6 / PyQt6 — scoped enum (on QDockWidget, not QtCore.Qt)
    LEFT_DOCK = Qt.DockWidgetArea.LeftDockWidgetArea
    RIGHT_DOCK = Qt.DockWidgetArea.RightDockWidgetArea
    TOP_DOCK = Qt.DockWidgetArea.TopDockWidgetArea
    BOTTOM_DOCK = Qt.DockWidgetArea.BottomDockWidgetArea
    DOCK_CLOSABLE = QDockWidget.DockWidgetFeature.DockWidgetClosable
    DOCK_MOVABLE = QDockWidget.DockWidgetFeature.DockWidgetMovable
    DOCK_FLOATABLE = QDockWidget.DockWidgetFeature.DockWidgetFloatable
except AttributeError:
    # Qt 5 / PyQt5 — flat enums
    LEFT_DOCK = Qt.LeftDockWidgetArea  # type: ignore[attr-defined]
    RIGHT_DOCK = Qt.RightDockWidgetArea  # type: ignore[attr-defined]
    TOP_DOCK = Qt.TopDockWidgetArea  # type: ignore[attr-defined]
    BOTTOM_DOCK = Qt.BottomDockWidgetArea  # type: ignore[attr-defined]
    DOCK_CLOSABLE = QDockWidget.DockWidgetClosable  # type: ignore[attr-defined]
    DOCK_MOVABLE = QDockWidget.DockWidgetMovable  # type: ignore[attr-defined]
    DOCK_FLOATABLE = QDockWidget.DockWidgetFloatable  # type: ignore[attr-defined]


# ── QVariant / QMetaType field type compatibility ───────────────────────────
try:
    # Qt 6 / PyQt6 — QVariant enum was moved under QMetaType.Type
    QMETATYPE_STRING = QMetaType.Type.QString
    QMETATYPE_INT = QMetaType.Type.Int
    QMETATYPE_DOUBLE = QMetaType.Type.Double
    QMETATYPE_BOOL = QMetaType.Type.Bool
    QMETATYPE_QURL = QMetaType.Type.QUrl
    QMETATYPE_LONGLONG = QMetaType.Type.LongLong
    QMETATYPE_UINT = QMetaType.Type.UInt
    QMETATYPE_ULONGLONG = QMetaType.Type.ULongLong
except AttributeError:
    # Qt 5 / PyQt5 — flat QVariant enum
    QMETATYPE_STRING = QVariant.String  # type: ignore[attr-defined]
    QMETATYPE_INT = QMetaType.Int  # type: ignore[attr-defined]
    QMETATYPE_DOUBLE = QMetaType.Double  # type: ignore[attr-defined]
    QMETATYPE_BOOL = QMetaType.Bool  # type: ignore[attr-defined]
    QMETATYPE_QURL = QMetaType.QUrl  # type: ignore[attr-defined]
    QMETATYPE_LONGLONG = QMetaType.LongLong  # type: ignore[attr-defined]
    QMETATYPE_UINT = QMetaType.UInt  # type: ignore[attr-defined]
    QMETATYPE_ULONGLONG = QMetaType.ULongLong  # type: ignore[attr-defined]


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
    SPSZ_MAXIMUM = QSizePolicy.Policy.Maximum
    SPSZ_PREFERRED = QSizePolicy.Policy.Preferred
    SPSZ_EXPANDING = QSizePolicy.Policy.Expanding
    SPSZ_MINIMUM_EXPANDING = QSizePolicy.Policy.MinimumExpanding
    SPSZ_IGNORED = QSizePolicy.Policy.Ignored
except AttributeError:
    SPSZ_FIXED = QSizePolicy.Fixed  # type: ignore[attr-defined]
    SPSZ_MINIMUM = QSizePolicy.Minimum  # type: ignore[attr-defined]
    SPSZ_MAXIMUM = QSizePolicy.Maximum  # type: ignore[attr-defined]
    SPSZ_PREFERRED = QSizePolicy.Preferred  # type: ignore[attr-defined]
    SPSZ_EXPANDING = QSizePolicy.Expanding  # type: ignore[attr-defined]
    SPSZ_MINIMUM_EXPANDING = QSizePolicy.MinimumExpanding  # type: ignore[attr-defined]
    SPSZ_IGNORED = QSizePolicy.Ignored  # type: ignore[attr-defined]


# ── QDialogButtonBox standard buttons and roles ───────────────────────────────
try:
    DLGBTN_OK = QDialogButtonBox.StandardButton.Ok
    DLGBTN_CANCEL = QDialogButtonBox.StandardButton.Cancel
    DLGBTN_CLOSE = QDialogButtonBox.StandardButton.Close
    DLGBTN_APPLY = QDialogButtonBox.StandardButton.Apply
    DLGBTN_RESET = QDialogButtonBox.StandardButton.Reset
    MSGBOX_ROLE_ACTION = QMessageBox.ButtonRole.ActionRole
    MSGBOX_ROLE_REJECT = QMessageBox.ButtonRole.RejectRole
    DLGBTN_ROLE_APPLY = QDialogButtonBox.ButtonRole.ApplyRole
    DLGBTN_ROLE_RESET = QDialogButtonBox.ButtonRole.ResetRole
    DLGBTN_ROLE_HELP = QDialogButtonBox.ButtonRole.HelpRole
    DLGBTN_ROLE_ACTION = QDialogButtonBox.ButtonRole.ActionRole
except AttributeError:
    DLGBTN_OK = QDialogButtonBox.Ok  # type: ignore[attr-defined]
    DLGBTN_CANCEL = QDialogButtonBox.Cancel  # type: ignore[attr-defined]
    DLGBTN_CLOSE = QDialogButtonBox.Close  # type: ignore[attr-defined]
    DLGBTN_APPLY = QDialogButtonBox.Apply  # type: ignore[attr-defined]
    DLGBTN_RESET = QDialogButtonBox.Reset  # type: ignore[attr-defined]
    MSGBOX_ROLE_ACTION = QMessageBox.ActionRole  # type: ignore[attr-defined]
    MSGBOX_ROLE_REJECT = QMessageBox.RejectRole  # type: ignore[attr-defined]
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
    QABSTRACTITEMVIEW_DOUBLE_CLICKED = QAbstractItemView.EditTrigger.DoubleClicked
    QABSTRACTITEMVIEW_SELECTED_CLICKED = QAbstractItemView.EditTrigger.SelectedClicked
    QABSTRACTITEMVIEW_EDIT_KEY_PRESSED = QAbstractItemView.EditTrigger.EditKeyPressed
    QABSTRACTITEMVIEW_SELECT_ROWS = QAbstractItemView.SelectionBehavior.SelectRows
    QABSTRACTITEMVIEW_SINGLE_SELECTION = QAbstractItemView.SelectionMode.SingleSelection
    QABSTRACTITEMVIEW_EXTENDED_SELECTION = QAbstractItemView.SelectionMode.ExtendedSelection
    QABSTRACTITEMVIEW_NO_SELECTION = QAbstractItemView.SelectionMode.NoSelection
    QABSTRACTITEMVIEW_INTERNAL_MOVE = QAbstractItemView.DragDropMode.InternalMove
    QABSTRACTITEMVIEW_SELECT_ITEMS = QAbstractItemView.SelectionBehavior.SelectItems
    MOVE_ACTION = Qt.DropAction.MoveAction
    DLG_ACCEPTED = QDialog.DialogCode.Accepted
    DLG_REJECTED = QDialog.DialogCode.Rejected
    MSGBOX_YES = QMessageBox.StandardButton.Yes
    MSGBOX_NO = QMessageBox.StandardButton.No
    MSGBOX_CANCEL = QMessageBox.StandardButton.Cancel
    MSGBOX_OK = QMessageBox.StandardButton.Ok
    MSGBOX_QUESTION = QMessageBox.Icon.Question
    SP_CRITICAL = QStyle.StandardPixmap.SP_MessageBoxCritical
    SP_WARNING = QStyle.StandardPixmap.SP_MessageBoxWarning
    SP_INFO = QStyle.StandardPixmap.SP_MessageBoxInformation
    ADJUST_TO_CONTENTS = QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
except AttributeError:
    # Qt 5 / PyQt5 — flat enum
    QABSTRACTITEMVIEW_NO_EDIT_TRIGGERS = QAbstractItemView.NoEditTriggers  # type: ignore[attr-defined]
    QABSTRACTITEMVIEW_DOUBLE_CLICKED = QAbstractItemView.DoubleClicked  # type: ignore[attr-defined]
    QABSTRACTITEMVIEW_SELECTED_CLICKED = QAbstractItemView.SelectedClicked  # type: ignore[attr-defined]
    QABSTRACTITEMVIEW_EDIT_KEY_PRESSED = QAbstractItemView.EditKeyPressed  # type: ignore[attr-defined]
    QABSTRACTITEMVIEW_SELECT_ROWS = QAbstractItemView.SelectRows  # type: ignore[attr-defined]
    QABSTRACTITEMVIEW_SINGLE_SELECTION = QAbstractItemView.SingleSelection  # type: ignore[attr-defined]
    QABSTRACTITEMVIEW_EXTENDED_SELECTION = QAbstractItemView.ExtendedSelection  # type: ignore[attr-defined]
    QABSTRACTITEMVIEW_NO_SELECTION = QAbstractItemView.NoSelection  # type: ignore[attr-defined]
    QABSTRACTITEMVIEW_INTERNAL_MOVE = QAbstractItemView.InternalMove  # type: ignore[attr-defined]
    QABSTRACTITEMVIEW_SELECT_ITEMS = QAbstractItemView.SelectItems  # type: ignore[attr-defined]
    MOVE_ACTION = Qt.MoveAction  # type: ignore[attr-defined]
    DLG_ACCEPTED = QDialog.Accepted  # type: ignore[attr-defined]
    DLG_REJECTED = QDialog.Rejected  # type: ignore[attr-defined]
    MSGBOX_YES = QMessageBox.Yes  # type: ignore[attr-defined]
    MSGBOX_NO = QMessageBox.No  # type: ignore[attr-defined]
    MSGBOX_CANCEL = QMessageBox.Cancel  # type: ignore[attr-defined]
    MSGBOX_OK = QMessageBox.Ok  # type: ignore[attr-defined]
    MSGBOX_QUESTION = QMessageBox.Question  # type: ignore[attr-defined]
    SP_CRITICAL = QStyle.SP_MessageBoxCritical  # type: ignore[attr-defined]
    SP_WARNING = QStyle.SP_MessageBoxWarning  # type: ignore[attr-defined]
    SP_INFO = QStyle.SP_MessageBoxInformation  # type: ignore[attr-defined]
    ADJUST_TO_CONTENTS = QAbstractScrollArea.AdjustToContents  # type: ignore[attr-defined]


# ── QLineEdit action positions ───────────────────────────────────────────────
try:
    LINEEDIT_TRAILING_POSITION = QLineEdit.ActionPosition.TrailingPosition
except AttributeError:
    LINEEDIT_TRAILING_POSITION = QLineEdit.TrailingPosition  # type: ignore[attr-defined]


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
    from qgis.core import Qgis

    # QGIS 4 / Qt 6 — scoped enums
    UNIT_DISTANCE_METERS = Qgis.DistanceUnit.Meters
    UNIT_DISTANCE_KILOMETERS = Qgis.DistanceUnit.Kilometers
    UNIT_DISTANCE_FEET = Qgis.DistanceUnit.Feet
    UNIT_DISTANCE_YARDS = Qgis.DistanceUnit.Yards
    UNIT_DISTANCE_MILES = Qgis.DistanceUnit.Miles
    UNIT_DISTANCE_NAUTICAL_MILES = Qgis.DistanceUnit.NauticalMiles
    UNIT_DISTANCE_MILLIMETERS = Qgis.DistanceUnit.Millimeters
    UNIT_DISTANCE_CENTIMETERS = Qgis.DistanceUnit.Centimeters

    UNIT_AREA_SQUARE_METERS = Qgis.AreaUnit.SquareMeters
    UNIT_AREA_SQUARE_KILOMETERS = Qgis.AreaUnit.SquareKilometers
    UNIT_AREA_SQUARE_FEET = Qgis.AreaUnit.SquareFeet
    UNIT_AREA_SQUARE_YARDS = Qgis.AreaUnit.SquareYards
    UNIT_AREA_SQUARE_MILES = Qgis.AreaUnit.SquareMiles
    UNIT_AREA_HECTARES = Qgis.AreaUnit.Hectares
    UNIT_AREA_ACRES = Qgis.AreaUnit.Acres
    UNIT_AREA_SQUARE_NAUTICAL_MILES = Qgis.AreaUnit.SquareNauticalMiles
    UNIT_AREA_SQUARE_CENTIMETERS = Qgis.AreaUnit.SquareCentimeters
    UNIT_AREA_SQUARE_MILLIMETERS = Qgis.AreaUnit.SquareMillimeters

    UNIT_VOLUME_CUBIC_METERS = Qgis.VolumeUnit.CubicMeters
    UNIT_VOLUME_CUBIC_FEET = Qgis.VolumeUnit.CubicFeet
    UNIT_VOLUME_CUBIC_YARDS = Qgis.VolumeUnit.CubicYards
    UNIT_VOLUME_BARREL = Qgis.VolumeUnit.Barrel
    UNIT_VOLUME_CUBIC_DECIMETER = Qgis.VolumeUnit.CubicDecimeter
    UNIT_VOLUME_LITERS = Qgis.VolumeUnit.Liters
    UNIT_VOLUME_GALLON_US = Qgis.VolumeUnit.GallonUS
    UNIT_VOLUME_CUBIC_INCH = Qgis.VolumeUnit.CubicInch
    UNIT_VOLUME_CUBIC_CENTIMETER = Qgis.VolumeUnit.CubicCentimeter
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

# ── QgisMessageLevel ─────────────────────────────────────────────────
# the Qt5→Qt6 scoped-enum change on the Result enum.

try:
    from qgis.core import Qgis

    # QGIS 4 / Qt 6 — scoped enum
    MESSAGE_LEVEL_INFO = Qgis.MessageLevel.Info  # type: ignore[attr-defined]
    MESSAGE_LEVEL_WARNING = Qgis.MessageLevel.Warning  # type: ignore[attr-defined]
    MESSAGE_LEVEL_CRITICAL = Qgis.MessageLevel.Critical  # type: ignore[attr-defined]
    MESSAGE_LEVEL_SUCCESS = Qgis.MessageLevel.Success  # type: ignore[attr-defined]
except AttributeError:
    # QGIS 3 / Qt 5 — flat enum
    MESSAGE_LEVEL_INFO = Qgis.Info  # type: ignore[attr-defined]
    MESSAGE_LEVEL_WARNING = Qgis.Warning  # type: ignore[attr-defined]
    MESSAGE_LEVEL_CRITICAL = Qgis.Critical  # type: ignore[attr-defined]
    MESSAGE_LEVEL_SUCCESS = Qgis.Success  # type: ignore[attr-defined]
except ImportError:
    # Not available in this QGIS build
    MESSAGE_LEVEL_INFO = None
    MESSAGE_LEVEL_WARNING = None
    MESSAGE_LEVEL_CRITICAL = None
    MESSAGE_LEVEL_SUCCESS = None
