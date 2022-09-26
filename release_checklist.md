# Release Checklist

1. Turn off development copy of QRiS in QGIS.
2. Close QGIS.
3. DOUBLE CHECK that QgsTasks have `run()` commented out and are asynchronous.
4. Increment `__version__.py`.
5. Navigate to QGIS plugin folder and delete existing deployment copy of plugin.
6. Run `deploy.py` using `Python: Current File (QRiS) debug menu.
7. Open QGIS.
8. Turn on deployment copy of QRiS.
9. Test!
10. Commit and push all changes.
11. push dev.
12. tag and push tag.
13. Create and comment pre-release.