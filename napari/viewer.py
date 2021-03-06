import platform
import sys
from os.path import dirname, join

from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication

from ._qt.qt_update_ui import QtUpdateUI
from ._qt.qt_main_window import Window
from ._qt.qt_viewer import QtViewer
from .components import ViewerModel
from . import __version__


class Viewer(ViewerModel):
    """Napari ndarray viewer.

    Parameters
    ----------
    title : string, optional
        The title of the viewer window. by default 'napari'.
    ndisplay : {2, 3}, optional
        Number of displayed dimensions. by default 2.
    order : tuple of int, optional
        Order in which dimensions are displayed where the last two or last
        three dimensions correspond to row x column or plane x row x column if
        ndisplay is 2 or 3. by default None
    axis_labels : list of str, optional
        Dimension names. by default they are labeled with sequential numbers
    show : bool, optional
        Whether to show the viewer after instantiation. by default True.
    """

    # set _napari_app_id to False to avoid overwriting dock icon on windows
    # set _napari_app_id to custom string to prevent grouping different base viewer
    _napari_app_id = 'napari.napari.viewer.' + str(__version__)

    def __init__(
        self,
        title='napari',
        ndisplay=2,
        order=None,
        axis_labels=None,
        show=True,
    ):
        # instance() returns the singleton instance if it exists, or None
        app = QApplication.instance()
        # if None, raise a RuntimeError with the appropriate message
        if app is None:
            message = (
                "napari requires a Qt event loop to run. To create one, "
                "try one of the following: \n"
                "  - use the `napari.gui_qt()` context manager. See "
                "https://github.com/napari/napari/tree/master/examples for"
                " usage examples.\n"
                "  - In IPython or a local Jupyter instance, use the "
                "`%gui qt` magic command.\n"
                "  - Launch IPython with the option `--gui=qt`.\n"
                "  - (recommended) in your IPython configuration file, add"
                " or uncomment the line `c.TerminalIPythonApp.gui = 'qt'`."
                " Then, restart IPython."
            )
            raise RuntimeError(message)

        if (
            platform.system() == "Windows"
            and not getattr(sys, 'frozen', False)
            and self._napari_app_id
        ):
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                self._napari_app_id
            )

        logopath = join(dirname(__file__), 'resources', 'logo.png')
        app.setWindowIcon(QIcon(logopath))

        super().__init__(
            title=title,
            ndisplay=ndisplay,
            order=order,
            axis_labels=axis_labels,
        )
        qt_viewer = QtViewer(self)
        self.window = Window(qt_viewer, show=show)

    def update_console(self, variables):
        """Update console's namespace with desired variables.

        Parameters
        ----------
        variables : dict, str or list/tuple of str
            The variables to inject into the console's namespace.  If a dict, a
            simple update is done.  If a str, the string is assumed to have
            variable names separated by spaces.  A list/tuple of str can also
            be used to give the variable names.  If just the variable names are
            give (list/tuple/str) then the variable values looked up in the
            callers frame.
        """
        if self.window.qt_viewer.console is None:
            return
        else:
            self.window.qt_viewer.console.push(variables)

    def screenshot(self, path=None, *, with_viewer=False):
        """Take currently displayed screen and convert to an image array.

        Parameters
        ----------
        path : str
            Filename for saving screenshot image.
        with_viewer : bool
            If True includes the napari viewer, otherwise just includes the
            canvas.

        Returns
        -------
        image : array
            Numpy array of type ubyte and shape (h, w, 4). Index [0, 0] is the
            upper-left corner of the rendered region.
        """
        if with_viewer:
            image = self.window.screenshot(path=path)
        else:
            image = self.window.qt_viewer.screenshot(path=path)
        return image

    def update(self, func, *args, **kwargs):
        t = QtUpdateUI(func, *args, **kwargs)
        self.window.qt_viewer.pool.start(t)
        return self.window.qt_viewer.pool  # returns threadpool object

    def show(self):
        """Resize, show, and raise the viewer window."""
        self.window.show()

    def close(self):
        """Close the viewer window."""
        self.window.close()
