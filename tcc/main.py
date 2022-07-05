from load_place import create_net_file_from
import osmnx as ox
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from NetworkOptimization import NetworkOptimization



if __name__ == "__main__":
    # Config section
    #ox.settings.use_cache=True
    place_name = "ufsc"                 # Place to be optimized
    radius = 600                        # Radius of the area to be optimized
    minimum_path_length = 60            # Number of seconds to be considered for averages
    primaries_only = True               # False = checks all roads, True = Only checks primary highways
    
    # Initialized optimizer class
    optimize = NetworkOptimization(threshold=minimum_path_length)

    # Create and adapt graph graph
    G = ox.graph_from_address(f"{place_name}", network_type='drive', dist=radius)
    Gp = ox.project_graph(G)
    graph = ox.utils_graph.get_largest_component(Gp, strongly=True) # Guarantee graph is strongly connected, so we don't have isolated nodes due to radius cutoff
    
    nodes, edges = ox.graph_to_gdfs(graph)
    colors = ox.plot.get_colors(len(graph.edges))

    ox.plot_graph(graph, edge_color=colors, show=False, node_size=0, edge_linewidth=0.3, save=True, filepath=f'{place_name}.png')

    primaries = 0
    for u,v, data in graph.edges(data=True):
        if data['highway'] == 'primary':
            primaries+=1

    for budget in [10, 50, 150]:
        print(f'Buget: {budget}k: {place_name} - {radius}m')
        print(f'Nodes: {len(nodes)}')
        print(f'Edges: {len(edges)}')
        print(f'Primaries: {primaries}')
        optimize.neighborhood_search(graph, budget*(10**3), place_name, only_primary=primaries_only)