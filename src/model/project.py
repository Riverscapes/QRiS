import sqlite3

from .assessment import Assessment


class Project():

    def __init__(self, project_file: str):

        self.project_file = project_file
        conn = sqlite3.connect(project_file)
        conn.row_factory = dict_factory
        curs = conn.cursor()

        curs.execute('SELECT name FROM projects LIMIT 1')
        self.name = curs.fetchone()['name']

        curs.execute('SELECT fid, name FROM assessments')
        self.assessments = {row['name']: row['fid'] for row in curs.fetchall()}

    def add_assessment(self, name: str, description: str, methods: list) -> Assessment:

        conn = sqlite3.connect(self.project_file)
        conn.row_factory = dict_factory
        curs = conn.cursor()
        curs.execute('INSERT INTO assessments (name, description) VALUES (?, ?)', [name, description if len(description) > 1 else None])
        assessment_id = curs.lastrowid

        assessment_methods = [(assessment_id, method_id) for method_id in methods]
        curs.executemany("""INSERT INTO assessment_methods (assessment_id, method_id)
                    SELECT ?, fid FROM methods WHERE name = ?""", assessment_methods)
        conn.commit()

        # Hack because listview only stores the method strings
        curs.execute('SELECT am.fid, m.name FROM assessment_methods am INNER JOIN methods m ON am.method_id = m.fid WHERE assessment_id = ?', [assessment_id])
        methods = {row['fid']: row['name'] for row in curs.fetchall()}

        return Assessment(assessment_id, name, description, methods)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
