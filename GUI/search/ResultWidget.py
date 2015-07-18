__author__ = 'adrien'

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QLineEdit, QGridLayout, QTextBrowser

# use html settext fo the Qtextedit module
# mauvaise idee, utilise qtableview---> pas editable mais c'est pas grave

class ResultWidget(QWidget):
    show_search_widget_signal = QtCore.pyqtSignal()
    receive_list = QtCore.pyqtSignal([list])

    def __init__(self):
        super().__init__()
        widget_layout = QGridLayout()
        self.setLayout(widget_layout)

        textwidget = QTextBrowser()
        html = """
<!DOCTYPE html>
<html>
<head>
<style type="text/css">
*
{
    margin: 0px;
    padding: 0px;
}
html, body
{
    height: 100%;
}
</style>
</head>

<body>

<table border="1" style="width:100%;height:100%;">
  <tr>
    <td>Jill</td>
    <td>
<ul>
  <li>Coffee</li>
  <li>Tea</li>
  <li>Milk</li>
</ul>
    </td>
    <td>50</td>
  </tr>
  <tr>
    <td>Eve</td>
    <td>Jackson</td>
    <td>94</td>
  </tr>
  <tr>
    <td>John</td>
    <td>Doe</td>
    <td>80</td>
  </tr>
</table>

</body>
</html>
"""
        textwidget.setHtml(html)
        # self.receive_text.connect(line_edit.setText)
        widget_layout.addWidget(textwidget, 0, 0, 3, 2)
        self.button = QPushButton('Back')
        widget_layout.addWidget(self.button, 4, 2)
        self.button.clicked.connect(self.show_search_widget_signal.emit)
        self.receive_list.connect(self.search_done)

    def search_done(self, argu):
        self.search_results = argu
        print("hehehe it rocks !")
        print(argu)