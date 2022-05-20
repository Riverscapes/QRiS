from .db_item import DBItem

ASSESSMENT_MACHINE_CODE = 'Assessment'


class Assessment(DBItem):

    def __init__(self, id, name, description, methods, bases):
        super().__init__(id, name)
        self.description = description
        self.methods = methods
        self.bases = bases
