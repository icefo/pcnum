from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QApplication, QItemDelegate, QSpinBox, QTableView, QProgressBar


class SpinBoxDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QProgressBar(parent)
        editor.setMinimum(0)
        editor.setMaximum(100)

        return editor

    def setEditorData(self, spinBox, index):
        value = index.model().data(index, Qt.EditRole)

        spinBox.setValue(value)


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    model = QStandardItemModel(4, 2)
    tableView = QTableView()
    tableView.setModel(model)

    delegate = SpinBoxDelegate()
    tableView.setItemDelegate(delegate)

    for row in range(4):
        for column in range(2):
            index = model.index(row, column, QModelIndex())
            model.setData(index, (row + 1) * (column + 1))

    tableView.setWindowTitle("Spin Box Delegate")
    tableView.show()
    sys.exit(app.exec_())