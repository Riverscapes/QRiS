# Non dotenv way to load environment variables from a file
#
# https://stackoverflow.com/questions/40216311/reading-in-environment-variables-from-an-environment-file

import os

env_file = os.path.join(os.path.dirname(__file__), '..','..', '.env')

def load_env_vars():
    with open(env_file, 'r') as fh:
        vars_dict = dict(
            tuple(line.replace('\n', '').split('='))
            for line in fh.readlines() if not line.startswith('#')
        )

    os.environ.update(vars_dict)
