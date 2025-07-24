import os
from shutil import copyfile

from qgis.core import QgsTask

class FileCopyTask(QgsTask):

    def __init__(self, source_path, dest_path, callback, mode='copy'):
        super().__init__("Copy Attachment File", QgsTask.CanCancel)
        self.source_path = source_path
        self.dest_path = dest_path
        self.callback = callback
        self.mode = mode  # 'copy' or 'rename'
        self.success = False
        self.error = None

    def run(self):
        try:
            # Ensure the destination directory exists
            dest_dir = os.path.dirname(self.dest_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            if self.mode == 'rename':
                os.rename(self.source_path, self.dest_path)
            else:
                copyfile(self.source_path, self.dest_path)
            self.success = True
        except Exception as ex:
            self.error = str(ex)
            self.success = False
        return self.success

    def finished(self, result):
        if self.callback:
            self.callback(self.success, self.error)