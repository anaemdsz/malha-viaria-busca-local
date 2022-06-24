from load_place import create_net_file_from
import osmnx as ox
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from pprint import pprint

class NetworkOptimization:
    
    def __init__(self):
        pass

    def neighborhood_search(self, graph):
            nodes, edges = ox.graph_to_gdfs(graph)
            for edge in edges:
                nx.set_edge_attributes
