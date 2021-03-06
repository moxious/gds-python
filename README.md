# GDS-python

A pure python wrapper API for Neo4j GDS; permitting people in python notebook implementations to work with GDS as if it was a local library.

This is a proof of concept.

## How it works

- GDS can be used as a set of pure Cypher procedure calls.
- Metadata about procedure calls can be gotten from Neo4j via `CALL dbms.procedures()`
- When connecting, this API fetches the existing GDS API from the remote server, and builds a JSON representation of every possible
procedure call, inputs, and outputs
- The library defines a simple dynamic object that turns python API calls into functions which execute cypher on the server.
- In python, `gds.graph.list()` turns into `CALL gds.graph.list()` in Cypher, and so forth.
- Each function call in this library is exactly equivalent to a single Cypher call, run through the
standard Neo4j python driver.

## Quickstart

### Spark Notebook

```
%pip install --force-reinstall git+https://github.com/moxious/gds-python.git
```

Example spark notebook code:

```
import json
from gds_python import GDS
my_graph = "g"

gds = GDS("url", "username", "password").connect()

gds_graphs = gds.graph.list()

if any(i['graphName'] == my_graph for i in gds_graphs):
  print("Graph already exists; dropping before we continue")
  print(gds.graph.drop(my_graph))
```

### Command Line

```
poetry install

export NEO4J_URI=neo4j+s://whatever
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=secret

poetry run python3 main.py
```

Example run:

```
$ poetry run python3 main.py 
RUNNING CYPHER WITH 'This query generated by gds-python v0.01' AS disclaimer
CALL gds.graph.list()
YIELD degreeDistribution, graphName, database, memoryUsage, sizeInBytes, detailSizeInBytes, nodeProjection, relationshipProjection, nodeQuery, relationshipQuery, nodeCount, relationshipCount, density, creationTime, modificationTime, schema
RETURN degreeDistribution, graphName, database, memoryUsage, sizeInBytes, detailSizeInBytes, nodeProjection, relationshipProjection, nodeQuery, relationshipQuery, nodeCount, relationshipCount, density, creationTime, modificationTime, schema WITH PARAMS {}
[{'degreeDistribution': {'p99': 19, 'min': 1, 'max': 169, 'mean': 4.0096011816839, 'p90': 7, 'p50': 3, 'p999': 65, 'p95': 9, 'p75': 5}, 'graphName': 'g2', 'database': 'neo4j', 'memoryUsage': '429 MiB', 'sizeInBytes': 450108720, 'detailSizeInBytes': {'relationships': {'total': 808248, 'everything': 819456, 'offsets': 21720, 'adjacencyList': 786528}, 'total': 450108720, 'nodes': {'sparseLongArray': 146048, 'forwardMapping': 0, 'backwardMapping': 0, 'total': 146048, 'everything': 146632}}, 'nodeProjection': {'CORA': {'properties': {'features': {'property': 'features', 'defaultValue': None}, 'subject': {'property': 'subject', 'defaultValue': None}}, 'label': 'CORA'}}, 'relationshipProjection': {'CITES': {'orientation': 'UNDIRECTED', 'aggregation': 'DEFAULT', 'type': 'CITES', 'properties': {}}}, 'nodeQuery': None, 'relationshipQuery': None, 'nodeCount': 2708, 'relationshipCount': 10858, 'density': 0.0014811973334628368, 'creationTime': neo4j.time.DateTime(2021, 4, 1, 12, 7, 42.771461, tzinfo=<StaticTzInfo 'Etc/UTC'>), 'modificationTime': neo4j.time.DateTime(2021, 4, 1, 12, 7, 47.646481, tzinfo=<StaticTzInfo 'Etc/UTC'>), 'schema': {'relationships': {'CITES': {}}, 'nodes': {'CORA': {'features': 'List of Integer (DefaultValue(null), PERSISTENT)', 'frp': 'List of Float (DefaultValue(null), TRANSIENT)', 'subject': 'Integer (DefaultValue(-9223372036854775808), PERSISTENT)'}}}}]
```

## Example Usage

```
gds = GDS(os.environ['NEO4J_URI'], os.environ['NEO4J_USERNAME'], os.environ['NEO4J_PASSWORD']).connect()
# print(json.dumps(gds.api, indent=2))

# Example of docstrings integration
# print(help(gds.graph.list))

# Call an actual function
print(gds.graph.list())

# Example of a failing non-existent call
# print(gds.foo())
```