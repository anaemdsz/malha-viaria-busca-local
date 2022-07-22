from load_place import create_net_file_from
import osmnx as ox
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from NetworkOptimization import NetworkOptimization
import datetime, pprint


# color_list = ox.plot.get_colors(n=len(edge_types), cmap='plasma_r')
# color_mapper = pd.Series(color_list, index=edge_types.index).to_dict()


if __name__ == "__main__":
    if(True):
        for place in ['ufsc', 'chapecó', 'nashville']:
            for _range in [50]:
                # Config section
                #ox.settings.use_cache=True
                place_name = place                  # Place to be optimized
                radius = _range                     # Radius of the area to be optimized
                minimum_path_length = 60            # Number of seconds to be considered for averages
                primaries_only = False              # False = checks all roads, True = Only checks primary highways
                
                # Initialized optimizer class
                optimize = NetworkOptimization(threshold=minimum_path_length)

                # Create and adapt graph graph
                G = ox.graph_from_address(f"{place_name}", network_type='drive', dist=radius)
                Gp = ox.project_graph(G)
                graph = ox.utils_graph.get_largest_component(Gp, strongly=True) # Guarantee graph is strongly connected, so we don't have isolated nodes due to radius cutoff
                
                nodes, edges = ox.graph_to_gdfs(graph)
                colors =  ox.plot.get_colors(len(graph.edges()))
                #optimize.get_density_colors(optimize.get_vehichle_density(optimize.add_lanes(graph)))

                ox.plot_graph(graph, edge_color=colors, show=False, node_size=0, edge_linewidth=0.3, save=True, filepath=f'length_based/traveltime/{place_name}/default_{radius}.png')

                primaries = 0
                for u,v, data in graph.edges(data=True):
                    if data['highway'] == 'primary':
                        primaries+=1
                
                for budget in [15, 20, 25]:
                    print(f'Analyzing {place}::{_range}::{budget} : {datetime.datetime.now()}')
                    print(f'Buget: {budget}k: {place_name} - {radius}m')
                    print(f'Nodes: {len(nodes)}')
                    print(f'Edges: {len(edges)}')
                    print(f'Primaries: {primaries}')
                    optimize.traveltime(graph, budget*(10**2), f"length_based/traveltime/{place_name}/{radius}", only_primary=primaries_only)
                    print(f'Finished {place}::{_range}::{budget} : {datetime.datetime.now()}\n\n\n\n\n\n\n')