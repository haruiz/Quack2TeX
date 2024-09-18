import sys
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Property, Signal, Slot, QFile
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication
from quack2tex.resources import resources_rc # noqa: F401


class MarkdownViewerDoc(QObject):
    """
    A simple QObject to expose the markdown viewer to the web page
    """

    contentChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._content = ""

    @Slot(str)
    def log(self, msg):
        """
        Print a message
        """
        #print(msg)
        ...

    @Slot(str)
    def send_to_clipboard(self, text):
        """
        Send text to the clipboard
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def get_content(self):
        """
        Get the content of the markdown viewer
        :return:
        """
        return self._content

    def set_content(self, content: str):
        """
        Set the content of the markdown viewer
        :param text:
        :return:
        """
        if self._content == content:
            return
        self._content = content
        self.contentChanged.emit(content)

    content = Property(str, fget=get_content, fset=set_content, notify=contentChanged)


class CustomWebEnginePage(QWebEnginePage):
    """
    A custom web engine page that automatically grants all requested
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def featurePermissionRequested(self, securityOrigin, feature):
        """
        Automatically grant all requested permissions
        :param securityOrigin:
        :param feature:
        :return:
        """
        # Automatically grant all requested permissions
        self.setFeaturePermission(
            securityOrigin, feature, QWebEnginePage.PermissionGrantedByUser
        )


class MarkdownViewer(QWebEngineView):
    """
    A simple markdown viewer widget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create a web channel
        self.channel = QWebChannel()
        # self.setPage(CustomWebEnginePage(self))
        self.page().setWebChannel(self.channel)
        # Expose the doc object to the web page
        self.doc = MarkdownViewerDoc(self)
        self.channel.registerObject("qtViewerDoc", self.doc)
        # Enable local content access
        self.page().settings().setAttribute(
            QWebEngineSettings.LocalContentCanAccessRemoteUrls, True
        )
        # Load the index.html file
        #QUrl.fromLocalFile(str(Path(__file__).parent / "files/index.html"))
        local_url = QUrl("qrc:/files/index.html")
        self.load(local_url)

    def set_content(self, content: str):
        """
        Set the content of the markdown viewer
        """
        self.doc.set_content(content)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = MarkdownViewer()
    viewer.set_content("# Hi\n\nThis is a simple markdown viewer.")
    viewer.show()
    sys.exit(app.exec())
