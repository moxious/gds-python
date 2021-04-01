from typing import Any, Callable
import json
from neo4j import GraphDatabase
import logging

class APIGenerator:
    def __init__(self, driver):
        self.driver = driver

    def generate(self):
        fetch_api = """
            call dbms.procedures() 
            yield name, signature, description, mode, defaultBuiltInRoles 
            where name =~ 'gds.*' 
            RETURN *;
        """

        api_description = []

        with self.driver.session() as session:
            results = session.run(fetch_api)

            for row in results:
                description = row['description']
                mode = row['mode']
                
                name = row['name']

                signature = row['signature']
                sig = self.parse_signature(name, signature)

                api_call = {
                    # Trim the leading 'gds.' which is the same for all of them.
                    "name": name[4:],
                    "mode": mode,
                    "description": description,
                    "inputs": sig['inputs'],
                    "outputs": sig['outputs']
                }
                api_description.append(api_call)

        return api_description

    def parse_parameters(self, paramlist):
        """Take a cypher parameter definition as a single string and parse it into name, default, type, and required.
        
        Example:  configuration = {} :: MAP? will return
        { name: configuration, default: {}, type: "MAP", required: FALSE }
        """
        if paramlist.strip() == '':
            return {}

        params = paramlist.strip().split(", ")

        result = []

        for param in params:
            parts = param.split(" :: ")
            if len(parts)<2:
                raise Exception("Missing parse on paramlist '%s' part '%s' from parts '%s'" % (paramlist, param, params))

            required = True
            default_value = None

            name_parts = parts[0].split(' = ')
            name = name_parts[0]

            if len(name_parts) > 1:
                default_value = name_parts[1]

            type_defn = parts[1]

            if type_defn.endswith('?'):
                required = False
                type_defn = type_defn.replace('?', '')
            
            result.append({
                "name": name,
                "default": default_value,
                "type": type_defn,
                "required": required
            })

        return result

    def parse_signature(self, name, signature):
        """Given a name and a cypher signature for a proc, this parses into a detailed list of inputs and outputs"""
        inputs = []
        outputs = []

        # EXAMPLE:
        # gds.wcc.write.estimate(graphName :: ANY?, configuration = {} :: MAP?) :: (requiredMemory :: STRING?, treeView :: STRING?, mapView :: MAP?, bytesMin :: INTEGER?, bytesMax :: INTEGER?, nodeCount :: INTEGER?, relationshipCount :: INTEGER?, heapPercentageMin :: FLOAT?, heapPercentageMax :: FLOAT?)

        # This initial split separates into a front-half (name & inputs) and a back-half (outputs)
        parts = signature.split(") :: (")
        inputs = parts[0].replace(name + "(", "")
        outputs = parts[1].replace(")", "")

        return {
            "inputs": self.parse_parameters(inputs),
            "outputs": self.parse_parameters(outputs)
        }

class GDSAPI:
    reserved_fields = ['api', 'driver', 'context', 'generate_callable_neo4j_function', 'generate_cypher', 'run']

    def __init__(self, api, driver, context='gds'):
        # This API is a list of objects with method names like this:
        # [
        #     { name: "graph.list" }, { name: "foo.bar" }
        # ]
        # Each time you look for an attribute, we see what api matches the prefix
        # (let's say "graph") and return a "sub-api" object
        self.context = context
        self.api = api
        self.driver = driver

    def run(self, query, **params):
        with self.driver.session() as session:
            result = session.run(query, **params)
            return [dict(i) for i in result]

    def generate_cypher(self, api, args):
        cypher = "WITH 'This query generated by gds-python v0.01' AS disclaimer\nCALL %s(" % (api['name'])

        l = len(args)
        params = {}
        for i in range(0, l):
            name = "p%d" % i
            params[name] = args[i]
            cypher = cypher + name + ", "
        cypher = cypher + ")\n"

        output_names = map(lambda e: e['name'], api['outputs'])
        all_outputs = ", ".join(list(output_names))

        cypher = cypher + "YIELD %s" % all_outputs + "\nRETURN %s" % all_outputs
        return cypher, params

    def generate_callable_neo4j_function(self, context, api):
        """Given a JSON description of an API function, this function returns another callable function that actually executes the
        relevant cypher on the server and unpacks/delivers results"""       
        def input_signature():
            return { key: api[key] for key in ['name', 'description', 'inputs' ]}

        def closure(*args):
            required_arguments = list(filter(lambda e: e['required'], api['inputs']))
            if len(args) < len(required_arguments) or len(args) > len(required_arguments):
                raise Exception(
                    "Invalid input!  You provided %d arguments, when %d are required of %d total. The signature is %s" % (
                        len(args), len(required_arguments), len(api['inputs']),
                        json.dumps(input_signature(), indent=2)))

            if args:
                logging.debug("ARGS %s" % args)

            with self.driver.session() as session:
                cypher, params = self.generate_cypher(api, args)
                print("RUNNING CYPHER %s WITH PARAMS %s" % (cypher, params))
                # splat
                results = session.run(cypher, **params)

                # TODO -- for very large result sets this is probably a bad idea, this is just a quick POC
                # This is just to unpack the "neo4j native format" to something friendlier.
                return [dict(i) for i in results]
        
        closure.__name__ = api['name']
        closure.__doc__ = api['description']
        return closure

    def __getattribute__(self, name: str) -> Callable:
        """Dynamic function fetcher.
        The purpose of this is to allow the user to call any function they like, and dynamically "look up the function" within
        the API specification.  Functions which don't exist return lambdas that always raise Exceptions.  Functions that do
        exist return "callable neo4j functions" that execute the equivalent on the remote server.
        """
        if name in GDSAPI.reserved_fields:
            return object.__getattribute__(self, name)

        def subdir_api(api_fn):
            new_fn = api_fn.copy()
            # Chop off the leading portion of name, which 
            # navigates one directory down
            new_fn['name'] = api_fn['name'][len(name) + 1:]
            return new_fn

        sub_api = list(map(
            subdir_api,            
            filter(lambda i: i['name'].startswith(name + ".") or i['name'] == name, self.api)))

        logging.debug("MATCHES", list(map(lambda e: e['name'], sub_api)))

        def failure():
            raise Exception("Method %s does not exist in the GDS API" % name)

        if len(sub_api) == 0:
            return failure

        if len(sub_api) == 1:
            # We have found the single API call the user was after.
            api_call = sub_api[0]
            api_call['name'] = self.context + ".%s" % name
            return self.generate_callable_neo4j_function(self.context + ".%s" % name, api_call)

        logging.debug("METACALL %s" % name)
        return GDSAPI(sub_api, self.driver, self.context + '.%s' % name)


class GDS:
    def __init__(self, url, username, password):
        self.driver = GraphDatabase.driver(url, auth=(username, password))

    def connect(self):
        """Call this method to verify connectivity to the Neo4j system, and to bootstrap the API"""
        self.generator = APIGenerator(self.driver)
        self.api = self.generator.generate()
        return GDSAPI(self.api, self.driver)
