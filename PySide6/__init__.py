import sys
from PyQt5 import QtWidgets, QtCore, QtGui

sys.modules['PySide6.QtWidgets'] = QtWidgets
sys.modules['PySide6.QtCore'] = QtCore
sys.modules['PySide6.QtGui'] = QtGui

Qt = QtCore.Qt

try:
    from PyQt5 import QtWebChannel
    sys.modules['PySide6.QtWebChannel'] = QtWebChannel
except ImportError:
    pass

try:
    from PyQt5 import QtWebEngineWidgets
    sys.modules['PySide6.QtWebEngineWidgets'] = QtWebEngineWidgets
except ImportError:
    pass
