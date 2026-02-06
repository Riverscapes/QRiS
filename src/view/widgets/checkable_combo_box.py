from qgis.PyQt import QtCore, QtGui, QtWidgets

class CheckableComboBox(QtWidgets.QComboBox):
    # Custom signal to notify when the popup is closed (edit finished)
    popupClosed = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super(CheckableComboBox, self).__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
        self.setModel(QtGui.QStandardItemModel(self))
        self.view().viewport().installEventFilter(self)
        self.model().dataChanged.connect(self.updateText)
        self.is_batch_mode = False # Flag to suppress updates
        self.all_checked_text = "All"
        self.none_checked_text = "None"
        self.empty_text = "No Options"

    def setPlaceholderText(self, text):
        super().setPlaceholderText(text)
        self.all_checked_text = text
        self.updateText()
        
    def setNoneCheckedText(self, text):
        self.none_checked_text = text
        self.updateText()
        
    def setEmptyText(self, text):
        self.empty_text = text
        self.updateText()

    def eventFilter(self, obj, event):
        if obj == self.view().viewport() and event.type() == QtCore.QEvent.MouseButtonRelease:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                item = self.model().itemFromIndex(index)
                
                # Check for commands
                data = item.data()
                if data == "SELECT_ALL":
                    self.set_all_check_state(QtCore.Qt.Checked)
                elif data == "SELECT_NONE":
                    self.set_all_check_state(QtCore.Qt.Unchecked)
                elif item.isCheckable():
                    # Normal toggle
                    if item.checkState() == QtCore.Qt.Checked:
                        item.setCheckState(QtCore.Qt.Unchecked)
                    else:
                        item.setCheckState(QtCore.Qt.Checked)
            return True # Consume event to prevent popup close
        return super(CheckableComboBox, self).eventFilter(obj, event)

    def set_all_check_state(self, state):
        self.is_batch_mode = True
        self.model().blockSignals(True)
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.isCheckable():
                item.setCheckState(state)
        self.model().blockSignals(False)
        self.is_batch_mode = False
        self.updateText() 
        
    def hidePopup(self):
        super(CheckableComboBox, self).hidePopup()
        self.popupClosed.emit()

    def addItem(self, text, data=None):
        item = QtGui.QStandardItem(text)
        item.setToolTip(text)
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        item.setData(QtCore.Qt.Checked, QtCore.Qt.CheckStateRole) # Default checked
        if data is not None:
             item.setData(data)
        self.model().appendRow(item)
        if not self.is_batch_mode:
            self.updateText()

    def addBatchItems(self, items):
        """Adds multiple items efficiently. items = list of (text, data) tuples."""
        self.is_batch_mode = True
        self.model().blockSignals(True)
        for text, data in items:
            self.addItem(text, data)
        self.model().blockSignals(False)
        self.is_batch_mode = False
        self.updateText()

    def add_command_item(self, text, data):
        item = QtGui.QStandardItem(text)
        item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        item.setData(data)
        font = item.font()
        font.setItalic(True)
        item.setFont(font)
        self.model().appendRow(item)

    def updateText(self, *args):
        items = self.get_checked_items()
        
        # Count checkable items only
        total_checkable = 0
        for i in range(self.model().rowCount()):
            if self.model().item(i).isCheckable():
                total_checkable += 1
                
        text = ", ".join(items)
        self.setToolTip(text)
        
        if total_checkable == 0:
            text = self.empty_text
            self.setEnabled(False)
        else:
            self.setEnabled(True)
            if len(items) == total_checkable:
                text = self.all_checked_text
            elif len(items) == 0:
                text = self.none_checked_text
            elif len(items) > 3:
                text = f"{len(items)} selected"

        self.lineEdit().setText(text)
    
    def get_checked_items(self):
        checkedItems = []
        for i in range(self.count()):
            item = self.model().item(i)
            if item.checkState() == QtCore.Qt.Checked:
                checkedItems.append(item.text())
        return checkedItems
        
    def get_checked_data(self):
        checkedData = []
        for i in range(self.count()):
            item = self.model().item(i)
            if item.checkState() == QtCore.Qt.Checked:
                checkedData.append(item.data())
        return checkedData
