def classFactory(iface):
    from .plugin import EarthDataDownloaderPlugin
    return EarthDataDownloaderPlugin(iface)