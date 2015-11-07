from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from functools import partial
from GUI.search.SearchWidget import SearchWidget
from GUI.search.ResultWidget import ResultWidget


class MainSearchWidget(QWidget):
    """
    This QWidget contain a QStackedWidget that display the SearchWidget or the ResultWidget
    """
    def __init__(self):
        """
        Init the QStackedWidget class and set signals to display SearchWidget or ResultWidget

        Returns:
            nothing
        """
        QWidget.__init__(self)

        #########
        self.search_widget = SearchWidget()
        self.result_widget = ResultWidget()

        #########
        self.stack = QStackedWidget()
        self.stack.addWidget(self.search_widget)
        self.stack.addWidget(self.result_widget)
        self.stack.setCurrentWidget(self.search_widget)

        #########
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.stack)

        #########
        self.search_widget.show_result_widget_signal.connect(partial(self.stack.setCurrentWidget, self.result_widget))
        self.result_widget.show_search_widget_signal.connect(partial(self.stack.setCurrentWidget, self.search_widget))

        self.search_widget.search_transmit.connect(self.result_widget.receive_search_results)
        self.result_widget.request_refresh.connect(self.search_widget.search)
