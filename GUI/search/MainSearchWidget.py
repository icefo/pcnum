from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from functools import partial
from GUI.search.SearchWidget import SearchWidget
from GUI.search.ResultWidget import ResultWidget
from GUI.search.EditWidget import EditWidget


class MainSearchWidget(QWidget):
    """
    This QWidget contain a QStackedWidget that display the SearchWidget or the ResultWidget
    """
    def __init__(self):
        """
        Init the QStackedWidget class and set signals to display SearchWidget or ResultWidget
        """
        # Initialize the parent class QWidget
        # this allow the use of the parent's methods when needed
        super(MainSearchWidget, self).__init__()

        #########
        self.search_widget = SearchWidget()
        self.result_widget = ResultWidget()
        self.edit_widget = EditWidget()

        #########
        self.stack = QStackedWidget()
        self.stack.addWidget(self.search_widget)
        self.stack.addWidget(self.result_widget)
        self.stack.addWidget(self.edit_widget)
        self.stack.setCurrentWidget(self.search_widget)

        #########
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.stack)

        #########
        self.search_widget.show_result_widget_signal.connect(partial(self.stack.setCurrentWidget, self.result_widget))

        self.result_widget.show_search_widget_signal.connect(partial(self.stack.setCurrentWidget, self.search_widget))
        self.result_widget.show_edit_widget_signal.connect(partial(self.stack.setCurrentWidget, self.edit_widget))

        self.edit_widget.show_result_widget_signal.connect(partial(self.stack.setCurrentWidget, self.result_widget))

        #########
        self.search_widget.search_transmit.connect(self.result_widget.receive_search_results)

        self.result_widget.request_refresh_signal.connect(self.search_widget.search)
        self.result_widget.show_edit_widget_signal.connect(self.edit_widget.reset_edit_table)
        self.result_widget.send_dc_identifier.connect(self.edit_widget.receive_data)

        self.edit_widget.request_refresh_signal.connect(self.search_widget.search)

