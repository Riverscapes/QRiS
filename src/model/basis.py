from .db_item import DBItem


BASIS_MACHINE_CODE = 'BASIS'
BASIS_PARENT_FOLDER = 'basis'


class Basis(DBItem):

    def __init__(self, id: int, name: str, relative_project_path: str, description: str):
        super(Basis, self).__init__(id, name)
        self.path = relative_project_path
        self.description = description
