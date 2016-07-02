from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QItemDelegate, QStyle, QStyleOptionProgressBar


class ProgressBarDelegate(QItemDelegate):
    def __init__(self):
        QItemDelegate.__init__(self)

    def paint(self, QPainter, QStyleOptionViewItem, QModelIndex):
        opts = QStyleOptionProgressBar()
        opts.rect = QStyleOptionViewItem.rect
        opts.minimum = 0
        opts.maximum = 100

        percent = QModelIndex.model().data(QModelIndex, QtCore.Qt.DisplayRole)
        if not isinstance(percent, int):
            percent = 0
        opts.progress = percent

        if percent == 0:
            opts.textVisible = False
        else:
            opts.textVisible = True

        opts.text = str(percent) + "%"
        QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, QPainter)
