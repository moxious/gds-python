from gds_python import GDS
import os
import logging
import json

logging.getLogger('GDSAPI').setLevel('DEBUG')

neo4j = GDS(os.environ['NEO4J_URI'], os.environ['NEO4J_USERNAME'], os.environ['NEO4J_PASSWORD'])
neo4j.connect()

gds = neo4j.get_api('gds')
apoc = neo4j.get_api('apoc')
db = neo4j.get_api('db')

print(apoc.periodic.submit('job', 'RETURN 1'))

# print(json.dumps(apoc.api, indent=2))
# print(json.dumps(gds.api, indent=2))

# Example of docstrings integration
# print(help(gds.graph.list))

# Call an actual function
print(gds.graph.list())

apoc.periodic.submit('jobName', 'RETURN 1')

# Example of a failing non-existent call
# print(gds.foo())
