from networkx import nx

def generic_worker(query, **params):
    return lambda e: [ dict(i) for i in e.run(query, **params)]

def write_batch(session, query, batch):
    # print("Q=%s batch=%s" % (query, batch))
    return session.write_transaction(generic_worker(query, batch=batch))

def destroy_graph(session, label):
    destroy_cypher = """
        CALL apoc.periodic.iterate(
            "MATCH (n:`%s`) RETURN n",
            "DETACH DELETE n",
            { batchSize: 5000, parallel: false })
    """ % label

    return session.write_transaction(generic_worker(destroy_cypher))

def write_networkx_graph(driver, G, label, batch_size=10000, destroy=True):
    merge_nodes = """
        UNWIND $batch AS event
        MERGE (i:`%s` { id: event.id })
            SET i += event.props
        RETURN count(i) as nodes
    """ % label

    batch = []
    with driver.session() as session:
        destroy_graph(session, label)

        for id, props in G.nodes(data=True):
            # print('ID=%s PROPS=%s' % (id, props))
            batch.append({ 'id': id, 'props': props })

            if len(batch) >= batch_size:
                write_batch(session, merge_nodes, batch)
                batch = []

        if len(batch) > 0:
            write_batch(session, merge_nodes, batch)
            batch = []

        merge_rels = """
            UNWIND $batch AS event
            MATCH (a:`%s` { id: event.a })
            MATCH (b:`%s` { id: event.b })
            MERGE (a)-[r:`%s`]->(b)
            SET r += event.props
            RETURN count(r) as rels
        """ % (label, label, label)

        for a, b, props in G.edges(data=True):
            # print("A=%s B=%s PROPS=%s" % (a, b, props))
            if a is None or b is None:
                raise Exception("Cannot use null ID in rel")

            batch.append({ 'a': a, 'b': b, 'props': props })

            if len(batch) >= batch_size:
                write_batch(session, merge_rels, batch)
                batch = []
        
        if len(batch) > 0:
            write_batch(session, merge_rels, batch)

        return label, G

def read_networkx_graph(driver, label, directed=True):
    if label is None or label == '':
        raise Exception("You must provide a valid graph label")

    print("Reading networkx graph labeled %s" % label)
    nodes = """
        MATCH (n:`%s`) 
        RETURN 
            n.id as id, 
            apoc.map.removeKey(n{.*}, 'id') as props
    """ % label 

    rels = """
        MATCH (a:`%s`)-[r:`%s`]->(b:`%s`) 
        RETURN 
            a.id as a, 
            b.id as b, 
            apoc.map.removeKey(r{.*}, 'id') as props
    """ % (label, label, label)

    G = None
    if directed: 
        G = nx.DiGraph()
    else: 
        G = nx.Graph()

    with driver.session() as session:
        # print(nodes)
        node_results = session.read_transaction(generic_worker(nodes))
        
        for n in node_results:
            G.add_node(n['id'], **n['props'])

        # print(rels)
        edge_results = session.read_transaction(generic_worker(rels))

        for e in edge_results:
            G.add_edge(e['a'], e['b'], **e['props'])

    print("Read graph %s" % G)
    return label, G
