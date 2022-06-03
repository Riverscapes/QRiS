from .db_item import DBItem
from .assessment import Assessment


class Design(DBItem):
    def __init__(self, assessment: Assessment, id: int, name: str, description: str):
        super().__init__('assessment_methods', id, name)
        self.description = description
        self.assessement = assessment
