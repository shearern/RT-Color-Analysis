import sys

from PySide.QtGui import QApplication, QIcon
from PySide.QtCore import QCoreApplication

from PIL import Image, ImageDraw

from rtcolor import RTCA_MainWindow

if __name__ == '__main__':
    app=QApplication(sys.argv)

    # Set app parameters
    QCoreApplication.setOrganizationName("SBC")
    QCoreApplication.setOrganizationDomain("spokanebaptist.org")
    QCoreApplication.setApplicationName("RT Color Analysis")

    # Set Icon
    app.setWindowIcon(QIcon(":/assets/images/app_icon.png"))

    # Tell Windows our APP ID
    # http://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
    try:
        import ctypes
        myappid = u'SBC-Video-Trim.' + QCoreApplication.organizationDomain()
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception, e:
        print "Failed to set Windows App ID: " + str(e)

	# Create root window
    root_win = RTCA_MainWindow()

    # Begin the main thread event queue
    root_win.show()
    app.exec_()