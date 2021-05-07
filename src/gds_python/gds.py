from gds_python import APIGenerator
from neo4j import GraphDatabase
from gds_python import Neo4j_Procedural_API

class GDS:
    def __init__(self, url, username, password, **driver_kwargs):
        self.driver = GraphDatabase.driver(url, auth=(username, password), **driver_kwargs)

    def connect(self):
        """Call this method to verify connectivity to the Neo4j system, and to bootstrap the API"""
        # print("Generating GDS API")
        self.generator = APIGenerator(self.driver)

        self.api_descriptions = {
            'gds': self.generator.generate('gds'),
            'apoc': self.generator.generate('apoc'),
            'dbms': self.generator.generate('dbms'),
            'db': self.generator.generate('db'),
            'nonexist': self.generator.generate('nonexist'),
        }

        self.apis = {}
        for api in self.api_descriptions.keys():
            self.apis[api] = Neo4j_Procedural_API(self.api_descriptions[api], self.driver, api)

        return self.apis['gds']

    def get_api(self, name):
        if not name in self.apis:
            return None
        return self.apis[name]