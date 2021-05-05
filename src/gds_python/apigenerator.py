from typing import Any, Callable
import json
from neo4j import GraphDatabase
import re
import logging

class APIGenerator:
    def __init__(self, driver):
        self.driver = driver

    def generate(self, prefix='gds'):
        fetch_api = """
            call dbms.procedures() 
            yield name, signature, description, mode, defaultBuiltInRoles 
            where name =~ '%s.*' 
            RETURN *;
        """ % prefix

        api_description = []

        with self.driver.session() as session:
            results = session.run(fetch_api)

            for row in results:
                description = row['description']
                mode = row['mode']
                
                name = row['name']

                signature = row['signature']
                try:
                    sig = self.parse_signature(name, signature)

                    api_call = {
                        # Trim the leading 'gds.' which is the same for all of them.
                        "name": name[len(prefix)+1:],
                        "mode": mode,
                        "description": description,
                        "inputs": sig['inputs'],
                        "outputs": sig['outputs']
                    }
                    api_description.append(api_call)
                except Exception as e:
                    print("Failed to parse %s with signature %s" % (
                        name, signature
                    ))

        return api_description

    def parse_parameters(self, paramlist):
        """Take a cypher parameter definition as a single string and parse it into name, default, type, and required.
        
        Example:  configuration = {} :: MAP? will return
        { name: configuration, default: {}, type: "MAP", required: FALSE }
        """
        if paramlist.strip() == '':
            return {}
        if paramlist.strip() == 'VOID':
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
        # gds.features.importer.skipOrphanNodes(skipOrphanNodes :: BOOLEAN?) :: VOID
        # apoc.nodes.group(labels :: LIST? OF STRING?, groupByProperties :: LIST? OF STRING?, aggregations = [{*=count}, {*=count}] :: LIST? OF MAP?, config = {} :: MAP?) :: (nodes :: LIST? OF NODE?, relationships :: LIST? OF RELATIONSHIP?, node :: NODE?, relationship :: RELATIONSHIP?)

        # This initial split separates into a front-half (name & inputs) and a back-half (outputs)
        parts = re.split('\\) :: \\(?', signature)
        inputs = parts[0].replace(name + "(", "")
        outputs = parts[1].replace(")", "")

        # print("INPUTS\n%s\nOUTPUTS\n%s\n" % (inputs, outputs))

        return {
            "inputs": self.parse_parameters(inputs),
            "outputs": self.parse_parameters(outputs)
        }
