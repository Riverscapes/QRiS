import sqlite3


class Project():

    def __init__(self, project_file: str):

        conn = sqlite3.connect(project_file)
        conn.row_factory = dict_factory
        curs = conn.cursor()

        curs.execute('SELECT name FROM projects LIMIT 1')
        self.name = curs.fetchone()['name']

        curs.execute('SELECT fid, name FROM assessments')
        self.assessments = {row['name']: row['fid'] for row in curs.fetchall()}


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
