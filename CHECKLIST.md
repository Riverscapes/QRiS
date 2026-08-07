# Deployment Checklist

There are a number of steps that have to be performed in the correct order for this plugin to deploy correctly.

NEVER WORK DIRECTLY ON THE MASTER BRANCH

1. Turn off the development copy of QRiS in QGIS.
2. Close QGIS.
3. DOUBLE CHECK that QgsTasks are asynchronous and any direct `run()` calls are commented out for deployment.
4. Increment the version number in `__version__.py`.
5. Compile resources with `scripts\\compile_resources.bat` (or run the `🔨 Compile Resources` VS Code task) and commit generated outputs.
6. Commit and push everything to git (development branch only).
7. Navigate to QGIS plugin folder and delete the existing deployment copy of the plugin.
8. Run `deploy.py` once and test the local deployment copy of the plugin.
9. Open QGIS.
10. Turn on the deployment copy of QRiS.
11. Test again.
12. Do a code review and create a pull request to merge to master.
13. Tag the release commit in git with the version number and push the tag.
14. Push `dev`.
15. Run `deploy.py` again to produce the zip file for upload.
16. Go to https://plugins.qgis.org/plugins/qris_deploy/ and upload the new version.
17. Create a GitHub pre-release/release and add release notes/comments.
