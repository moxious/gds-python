# GDS-python

A pure python wrapper API for Neo4j GDS; permitting people in python notebook implementations to work with GDS as if it was a local library.

This is a POC only at this point.

## How it works

- GDS can be used as a set of pure Cypher procedure calls.
- Metadata about procedure calls can be gotten from Neo4j via `CALL dbms.procedures()`
- When connecting, this API fetches the existing GDS API from the remote server, and builds a JSON representation of every possible
procedure call, inputs, and outputs
- The library defines a simple dynamic object that turns python API calls into functions which execute cypher on the server.
- In python, `gds.graph.list()` turns into `CALL gds.graph.list()` in Cypher, and so forth.

## Quickstart

```
poetry install

export NEO4J_URI=neo4j+s://whatever
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=secret

poetry run python3 main.py
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