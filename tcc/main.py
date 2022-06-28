from load_place import create_net_file_from
import osmnx as ox
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from NetworkOptimization import NetworkOptimization

optimize = NetworkOptimization()

if __name__ == "__main__":
    #ox.config(use_cache=True, log_console=True)
    
    radius = 750
    place_name = "Ufsc, Florianopolis"
    minimum_path_length = 200 # Number of seconds to be considered for averages
    G = ox.graph_from_address(f"{place_name}, Brazil", network_type='drive', dist=radius)
    #G = ox.graph_from_place(f"{place_name}, Brazil", network_type='drive')
    #G = ox.graph_from_bbox(-27.568694628375766, -27.620267778597213, -48.49074027067684, -48.565328692532546, network_type='drive')
    Gp = ox.project_graph(G)
    Gs = ox.utils_graph.get_largest_component(Gp, strongly=True)
    #print(G.edges.data('speed_kph', default=40.0))

    nodes, edges = ox.graph_to_gdfs(Gp)
    colors = ox.plot.get_colors(len(Gs.edges))
    ox.plot_graph(Gs, edge_color=colors, show=False, node_size=0, edge_linewidth=0.3, save=True, filepath=f'{place_name}.png')

    # route = nx.shortest_path(Gs, 8559093475, 3739434958, weight='travel_time')

    # i = 0
    # for n in route:
    #     route = nx.shortest_path(Gs, 8559093475, n, weight='travel_time')
    #     ox.plot_graph_route(Gs, route, edge_color=colors, show=False, node_size=0, edge_linewidth=0.3, save=True, filepath=f'{place_name}-{i}.png', dpi=800)#, annotate=True)
    #     i+=1

    # print(route)
    # ox.plot_graph_route(Gs, route, edge_color=colors, show=False, node_size=0, edge_linewidth=0.3, save=True, filepath=f'{place_name}.png', dpi=800)#, annotate=True)

    # average_time, amount_edge = get_average_time(Gs, minimum_path_length)

    # for u, v, data in Gs.edges(keys=False, data=True):
    #     try:
    #         print(data)
    #         data['passes'] = amount_edge[(u,v)]
    #     except:
    #         data['passes'] = 0

    optimize.neighborhood_search(Gs, 3)

    # colors = ox.plot.get_edge_colors_by_attr(Gs, 'passes', num_bins=4, cmap ='jet')
    # ox.plot_graph(Gs, edge_color=colors, show=False, node_size=0, edge_linewidth=0.3, save=True, filepath=f'{place_name}.png')
    # print(f"The average length of paths longer than {minimum_path_length}s is {average_time}s")


