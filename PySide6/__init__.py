import sys
from PyQt5 import QtWidgets, QtCore, QtGui

QtCore.Signal = QtCore.pyqtSignal
QtCore.QPropertyAnimation = QtCore.QPropertyAnimation
QtCore.QEasingCurve = QtCore.QEasingCurve
QtCore.QTimer = QtCore.QTimer
QtGui.QKeySequence = QtGui.QKeySequence
QtGui.QShortcut = QtWidgets.QShortcut
QtGui.QUndoStack = QtWidgets.QUndoStack
QtGui.QUndoCommand = QtWidgets.QUndoCommand
QtWidgets.QShortcut = QtWidgets.QShortcut

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
