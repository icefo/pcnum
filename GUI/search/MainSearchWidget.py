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
        search_widget = SearchWidget()
        result_widget = ResultWidget()
        edit_widget = EditWidget()

        #########
        stack = QStackedWidget()
        stack.addWidget(search_widget)
        stack.addWidget(result_widget)
        stack.addWidget(edit_widget)
        stack.setCurrentWidget(search_widget)

        #########
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(stack)

        #########
        search_widget.show_result_widget_signal.connect(partial(stack.setCurrentWidget, result_widget))

        result_widget.show_search_widget_signal.connect(partial(stack.setCurrentWidget, search_widget))
        result_widget.show_edit_widget_signal.connect(partial(stack.setCurrentWidget, edit_widget))

        edit_widget.show_result_widget_signal.connect(partial(stack.setCurrentWidget, result_widget))

        #########
        search_widget.search_transmit.connect(result_widget.receive_search_results)

        result_widget.request_refresh_signal.connect(search_widget.search)
        result_widget.show_edit_widget_signal.connect(edit_widget.reset_edit_table)
        result_widget.send_dc_identifier.connect(edit_widget.receive_data)

        edit_widget.request_refresh_signal.connect(search_widget.search)

