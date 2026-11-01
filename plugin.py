"""QGIS plugin entry point for Earth Data Downloader."""
import importlib
import os
import sys

from qgis.PyQt.QtCore import QProcess, Qt

try:  # Qt6
    from qgis.PyQt.QtGui import QAction
except ImportError:  # Qt5
    from qgis.PyQt.QtWidgets import QAction

from qgis.PyQt.QtGui import QIcon


def _qt_member(owner, group, name):
    """Read a Qt6 scoped enum or its Qt5 unscoped equivalent."""
    enum_group = getattr(owner, group, None)
    if enum_group is not None and hasattr(enum_group, name):
        return getattr(enum_group, name)
    return getattr(owner, name)


class EarthDataDownloaderPlugin:
    MENU = "&Earth Data Downloader"

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None
        self._dependency_process = None
        self._dependency_progress = None
        self._dependency_packages = []
        self._dependency_python = ""

    def initGui(self):
        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))
        self.action = QAction(icon, "Earth Data Downloader\u2026", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.MENU, self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        if self.action is not None:
            self.iface.removePluginMenu(self.MENU, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None
        if self.dialog is not None:
            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None

    def run(self):
        missing = self._missing_dependencies()
        if missing:
            from qgis.PyQt.QtWidgets import QMessageBox, QProgressDialog

            packages = "\n".join(f"• {package}" for package in missing)
            python_exe = os.path.join(sys.prefix, "python.exe")
            if not os.path.isfile(python_exe):
                python_exe = sys.executable
            prompt = QMessageBox(self.iface.mainWindow())
            prompt.setIcon(_qt_member(QMessageBox, "Icon", "Warning"))
            prompt.setWindowTitle("GeoToolkit dependencies missing")
            prompt.setText(
                "These required Python packages are missing from the QGIS environment:\n\n"
                f"{packages}\n\nInstall the missing packages now?"
            )
            prompt.setInformativeText(
                "GeoToolkit will run pip with the QGIS Python interpreter. "
                "Restart QGIS after installation completes."
            )
            yes = _qt_member(QMessageBox, "StandardButton", "Yes")
            no = _qt_member(QMessageBox, "StandardButton", "No")
            prompt.setStandardButtons(yes | no)
            prompt.setDefaultButton(yes)
            execute = getattr(prompt, "exec", None) or prompt.exec_
            if execute() == yes:
                self._install_dependencies(missing, python_exe, QProgressDialog)
            return
        from qgis.PyQt.QtCore import QSettings
        from qgis.PyQt.QtWidgets import QCheckBox, QMessageBox
        settings = QSettings()
        if not settings.value("GeoToolkit/dependenciesSuccessNotified", False, type=bool):
            message = QMessageBox(self.iface.mainWindow())
            message.setIcon(QMessageBox.Icon.Information)
            message.setWindowTitle("GeoToolkit libraries ready")
            message.setText("All required GeoToolkit libraries are installed and working.")
            suppress = QCheckBox("Don't show this message again")
            message.setCheckBox(suppress)
            message.exec()
            if suppress.isChecked():
                settings.setValue("GeoToolkit/dependenciesSuccessNotified", True)
        if self.dialog is None:
            from .ui.main_dialog import MainDialog
            self.dialog = MainDialog(self.iface, self.iface.mainWindow())
        elif not self.dialog.isVisible():
            download_active = self.dialog._download_thread is not None and self.dialog._download_thread.isRunning()
            auth_active = self.dialog._ee_thread is not None and self.dialog._ee_thread.isRunning()
            if not download_active and not auth_active:
                self.dialog._new_session()
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    @staticmethod
    def _missing_dependencies():
        """Return required pip package names whose import modules are absent."""
        required_modules = {
            "earthengine-api": "ee",
            "requests": "requests",
        }
        return [
            package
            for package, module in required_modules.items()
            if not EarthDataDownloaderPlugin._can_import(module)
        ]

    @staticmethod
    def _can_import(module):
        try:
            importlib.import_module(module)
            return True
        except ImportError:
            return False

    def _install_dependencies(self, packages, python_exe, progress_dialog_class):
        """Install only missing packages into the Python used by this QGIS."""
        not_running = _qt_member(QProcess, "ProcessState", "NotRunning")
        if self._dependency_process is not None and self._dependency_process.state() != not_running:
            return

        self._dependency_packages = list(packages)
        self._dependency_python = python_exe
        progress = progress_dialog_class(
            "Installing missing GeoToolkit packages into the QGIS Python environment…",
            None, 0, 0, self.iface.mainWindow(),
        )
        progress.setWindowTitle("Installing GeoToolkit dependencies")
        progress.setWindowModality(_qt_member(Qt, "WindowModality", "WindowModal"))
        progress.setMinimumDuration(0)
        progress.show()

        process = QProcess(self.iface.mainWindow())
        process.setProgram(python_exe)
        process.setArguments([
            "-m", "pip", "install", "--disable-pip-version-check", *self._dependency_packages
        ])
        process.setProcessChannelMode(_qt_member(QProcess, "ProcessChannelMode", "MergedChannels"))
        process.finished.connect(self._dependency_install_finished)
        process.errorOccurred.connect(self._dependency_process_error)
        self._dependency_process = process
        self._dependency_progress = progress
        process.start()

    def _dependency_process_error(self, error):
        failed_to_start = _qt_member(QProcess, "ProcessError", "FailedToStart")
        if error != failed_to_start:
            return
        detail = self._dependency_process.errorString() if self._dependency_process else "Could not start pip."
        if self._dependency_progress is not None:
            self._dependency_progress.close()
            self._dependency_progress = None
        from qgis.PyQt.QtWidgets import QMessageBox
        command = f'"{self._dependency_python}" -m pip install ' + " ".join(self._dependency_packages)
        QMessageBox.critical(
            self.iface.mainWindow(),
            "Could not start package installation",
            f"{detail}\n\nYou can run this in the QGIS Python terminal:\n{command}",
        )

    def _dependency_install_finished(self, exit_code, _exit_status):
        process = self._dependency_process
        output = bytes(process.readAllStandardOutput()).decode("utf-8", errors="replace") if process else ""
        if self._dependency_progress is not None:
            self._dependency_progress.close()
            self._dependency_progress = None

        still_missing = self._missing_dependencies()
        from qgis.PyQt.QtWidgets import QMessageBox
        if exit_code == 0 and not still_missing:
            QMessageBox.information(
                self.iface.mainWindow(),
                "GeoToolkit dependencies installed",
                "The missing packages were installed successfully. Restart QGIS, then open GeoToolkit again.",
            )
            return

        missing_text = ", ".join(still_missing or self._dependency_packages)
        output = output.strip()
        if len(output) > 2400:
            output = output[-2400:]
        command = f'"{self._dependency_python}" -m pip install ' + " ".join(still_missing or self._dependency_packages)
        detail = f"pip exited with code {exit_code}. Still missing: {missing_text}."
        if output:
            detail += f"\n\nInstaller output:\n{output}"
        detail += f"\n\nYou can retry in the QGIS Python terminal:\n{command}"
        QMessageBox.warning(self.iface.mainWindow(), "Package installation incomplete", detail)
