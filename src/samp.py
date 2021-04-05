from networkx import nx
from gds_python import GDS

gds = GDS('neo4j+s://1fa52338.databases.neo4j.io', 'neo4j', 'WFCenAFwNQg4v__8JPgmH7KfcNAfZKRaGt8C9ksxwMU').connect()
print(gds)

scenarios = [
    nx.generators.barabasi_albert_graph(100, 2),
    nx.cubical_graph(),
    nx.random_geometric_graph(100, 0.125),
]

for i in range(0, len(scenarios)):
    G = scenarios[i]
    label, retG = gds.write_networkx_graph(G, i)
    label, reanimated = gds.read_networkx_graph(label, directed=G.is_directed())
    print("Isomorphic? %s" % nx.is_isomorphic(G, reanimated))
