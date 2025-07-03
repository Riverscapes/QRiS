import os
import sys
from glob import glob
import shutil
import re
import zipfile


PLUGIN_NAME = "qris_deploy"
UI_DIR = "src/ui"

# Environment variable that specifies the path to the QGIS plugins folder
#  where the plugin will be deloyed.
PLUGIN_ENV_VAR_NAME = 'QGIS_PLUGINS'


def copy_plugin():
    rootdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    deployfolder = os.path.abspath(os.path.join(os.getenv(PLUGIN_ENV_VAR_NAME), PLUGIN_NAME))

    if rootdir == deployfolder:
        print('deploy and source folders cannot be the same!')
        sys.exit(1)

    print('Deploy to {}? (y/N)'.format(deployfolder))
    yesno('Exiting')

    if os.path.isdir(deployfolder):
        print('Folder exists \n{}\n and will be deleted? Is this ok? (y/N)'.format(deployfolder))
        yesno('Go change the __version__.py file and come back')
        shutil.rmtree(deployfolder)

    os.mkdir(deployfolder)
    keep_patterns = [
        ['__version__.py'],
        ['icon.png'],
        ['__init__.py'],
        ['CHANGELOG.md'],
        ['README.md'],
        ['LICENSE'],
        ['config.json'],
        ['secrets.json'],
        ['.env'],
        ['wheels', '**', '*.whl'],
        ['src', '**', '*.py'],
        ['src', '**', '*.json'],
        ['src', '**', '*.css'],
        ['src', '**', '*.html'],
        ['src', '**', '*.sql'],
        ['src', '**', '*.qml'],
        ['resources', '**', 'us_states.gpkg'],
        ['resources', '**', '*.json'],
    ]
    files = []
    for p in keep_patterns:
        files += glob(os.path.join(rootdir, *p), recursive=True)

    for f in files:
        dst = os.path.join(deployfolder, os.path.relpath(f, rootdir))
        dst_dir = os.path.dirname(dst)
        if not os.path.isdir(dst_dir):
            os.makedirs(dst_dir, exist_ok=True)
        shutil.copy(f, dst)
        print('\n{}\n{}\n'.format(f, dst))

    return deployfolder


def move_meta(deployfolder, version):
    # Metadata must be handled separately
    src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'metadata.txt'))
    dst = os.path.abspath(os.path.join(deployfolder, 'metadata.txt'))

    with open(src, 'r', encoding="utf8") as f, open(dst, 'w+', encoding="utf8") as wf:
        text = f.read()
        text = text.replace(' DEV_COPY', '')
        text = text.replace('version=0.0.0dev', 'version={}'.format(version))
        wf.write(text)


def zip_plugin(deployfolder: str, version: str):
    # ziph is zipfile handle
    root_dir = os.path.dirname(deployfolder)
    zipfile_name = '{}-{}'.format(PLUGIN_NAME, version.replace('.', '_'))
    zipfile_path = os.path.join(root_dir, zipfile_name)
    shutil.make_archive(zipfile_path, 'zip', root_dir=root_dir, base_dir=PLUGIN_NAME)


def deploy_plugin():
    pass


def yesno(msg):
    res = input()
    if res.lower() != "y":
        print(msg)
        sys.exit(1)


if __name__ == '__main__':
    print('Did the UI compile and you forgot to run "pb_tool compile" (y/N)')
    yesno('run "pb_tool compile" and then try again')

    vfile = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '__version__.py'))
    version = re.search(
        '^__version__\\s*=\\s*"(.*)"',
        open(vfile).read(),
        re.M
    ).group(1)

    print('Current version is: {}. Is this ok? (y/N)'.format(version))
    yesno('Go change the __version__.py file and come back')

    deployfolder = copy_plugin()

    move_meta(deployfolder, version)
    zip_plugin(deployfolder, version)

    deploy_plugin()
