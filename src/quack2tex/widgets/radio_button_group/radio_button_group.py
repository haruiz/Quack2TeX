import typing

from PySide6.QtCore import Signal, Property
from PySide6.QtWidgets import QWidget, QButtonGroup, QRadioButton, QVBoxLayout, QLabel, QHBoxLayout
from scipy.linalg import pinvh


class RadioButtonGroup(QWidget):
    """
    A group of radio buttons
    """

    on_radio_button_clicked = Signal(object)


    def __init__(self, parent=None):
        super(RadioButtonGroup, self).__init__(parent)
        # Create the layout

        # Create the layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Create a button group
        self.radio_group = QButtonGroup(self)
        self.radio_group.buttonClicked.connect(self.handler_on_radio_button_clicked)

        # Set the layout of the window
        self.setLayout(layout)

    @Property(str)
    def selected_option(self):
        """
        Get the selected option
        :return: the selected option
        """
        selected_button = self.radio_group.checkedButton()
        return selected_button.property("value") if selected_button else "None"

    def set_select_option(self, value):
        """
        Select an option
        :param value: the value to select
        :return: None
        """
        for button in self.radio_group.buttons():
            if button.property("value") == value:
                print("Setting button")
                button.setChecked(True)
                break

    def handler_on_radio_button_clicked(self, button):
        """
        Handler for when a radio button is clicked
        :param button: the button that was clicked
        :return: None
        """
        self.on_radio_button_clicked.emit(button.property("value"))

    def add_option(self, text_value : str,checked:bool = False, value: typing.Any =None):
        """
        Add a new radio button to the group
        :param text_value: the text value to display
        :param checked: whether the radio button should be checked
        :param value: the data to associate with the radio button
        :return: None
        """
        radio_button = QRadioButton(text_value)
        radio_button.setChecked(checked)
        radio_button.setProperty("value", value)
        self.radio_group.addButton(radio_button)
        self.layout().addWidget(radio_button)

