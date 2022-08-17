# from graphql import query
# from path import expanduser
import json
import logging
import requests


class QueryMonster:
    """_summary_
    """

    def __init__(self, api_url=None, api_key=None):
        """_summary_

        Args:
            api_url (_type_, optional): _description_. Defaults to None.
            api_key (_type_, optional): _description_. Defaults to None.
        """
        self.jwt = None
        self.api_url = api_url
        self.api_key = api_key

    def run_query(self, query, variables):
        """
        A simple function to use requests.post to make the API call. Note the json= section.
        """

        if self.api_url is None:
            raise Exception('The API URL has not been initialized. Contact the software administrator for support.')

        if self.api_key is None:
            raise Exception('The API key has not been initialized. Contact the software administrator for support.')

        headers = {"x-api-key": self.api_key}
        request = requests.post(self.api_url, json={
            'query': query,
            'variables': variables
        }, headers=headers)

        if request.status_code == 200:
            resp_json = request.json()
            if 'errors' in resp_json and len(resp_json['errors']) > 0:
                logging.error(json.dumps(resp_json, indent=4, sort_keys=True))
                raise Exception(resp_json)
            else:
                return request.json()
        else:
            raise Exception(f"Query failed to run by returning code of {request.status_code}. {query}")
