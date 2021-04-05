from gds_python import GDS
import os
import logging

logging.getLogger('GDSAPI').setLevel('DEBUG')

gds = GDS(os.environ['NEO4J_URI'], os.environ['NEO4J_USERNAME'], os.environ['NEO4J_PASSWORD']).connect()
# print(json.dumps(gds.api, indent=2))

# Example of docstrings integration
# print(help(gds.graph.list))

# Call an actual function
# print(gds.graph.list())

# Example of a failing non-existent call
# print(gds.foo())

result = gds.graph.create('g', { "Person": { "properties": [] } }, { "KNOWS": { "orientation": "UNDIRECTED" } })
print(result)
