import sys

from quack2tex.pyqt import (
    QUrl, QWebChannel, QApplication, QWebEngineView, QObject, Signal, Slot, Property, QWebEnginePage, QWebEngineSettings
)
from quack2tex.resources import *  # noqa: F401

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
            securityOrigin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
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
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        # Load the index.html file
        #QUrl.fromLocalFile(str(Path(__file__).parent / "files/index.html"))
        local_url = QUrl("qrc:/files/index.html")
        self.load(local_url)

    @property
    def content(self):
        """
        Get the content of the markdown viewer
        """
        return self.doc.get_content()

    @content.setter
    def content(self, content: str):
        """
        Set the content of the markdown viewer
        :param content:
        :return:
        """
        # Convert markdown to HTML
        self.doc.set_content(content)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = MarkdownViewer()
    viewer.content = "# Hi\n\nThis is a simple markdown viewer."
    viewer.show()
    sys.exit(app.exec())
