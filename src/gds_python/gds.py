from gds_python import APIGenerator
from neo4j import GraphDatabase
from gds_python import GDSAPI

class GDS:
    def __init__(self, url, username, password):
        self.driver = GraphDatabase.driver(url, auth=(username, password))

    def connect(self):
        """Call this method to verify connectivity to the Neo4j system, and to bootstrap the API"""
        self.generator = APIGenerator(self.driver)
        self.api = self.generator.generate()
        return GDSAPI(self.api, self.driver)
