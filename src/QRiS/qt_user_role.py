from qgis.PyQt.QtCore import Qt


item_code = {'item_type': Qt.UserRole + 1,
             # INSTANCE - Stores the class instance, the whole thing.
             'INSTANCE': Qt.UserRole + 2,
             # item_layer usually refers to display within the QGIS layer tree often for groups
             'feature_id': Qt.UserRole + 3}
