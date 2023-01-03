from .db_item import DBItem


class DBItemVector(DBItem):

    def __init__(self, db_table_name: str, id: int, name: str, fc_name: str):
        super().__init__(db_table_name, id, name)

        self.fc_name = fc_name

    def get_layer_path(self, project_db_path: str) -> str:
        return 'f{project_db_path}|layername={self.fc_name}'
