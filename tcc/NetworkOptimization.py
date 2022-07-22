import osmnx as ox
import networkx as nx
from pprint import pprint
import copy, numpy
import concurrent.futures
from datetime import datetime
class NetworkOptimization:
    
    def __getstate__(self):
        self_dict = self.__dict__.copy()
        return self_dict

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __init__(self, threshold=60):
        self.changes = []
        self.prices = {   #placeholder values
            "add_lane": 800,
            "remove_lane": 300,
            "reverse_lane": 150
        }
        self.budget = 0
        self.threshold = threshold
        pass

    def get_probability_table(self, graph):
        p_table = []
        for u, v, k, d in graph.edges(keys=True, data=True):
            p_edge = []
            total_kms = 0
            for _u, _v, _k , _d in graph.edges(keys=True, data=True):
                if _u == v:
                    road_kms = int(_d['lanes'][0])*_d['length']
                elif (u == _u) and (v == _v) and (k == _k):
                    road_kms = int(_d['lanes'][0])*_d['length']
                else:
                    road_kms = 0
                total_kms += road_kms
                p_edge.append(road_kms)
            for i, p in enumerate(p_edge):
                p_edge[i] = p/total_kms
            p_table.append(p_edge)
        print('Generating probability table for Markov Chain')
        pprint(p_table)
        return p_table
                


    def remove_lane(self, graph, edge, nodes_tuple, prefer_smaller_side=True):
        lanes = edge['lanes']
        if lanes == '1':
            return graph
        try:
            if prefer_smaller_side:
                edge['lanes'] = str(int(min(lanes)) - 1)
            else:
                edge['lanes'] = str(int(max(lanes)) - 1)
        except Exception as e:
            pprint(e)

        graph[nodes_tuple[0]][nodes_tuple[1]][nodes_tuple[2]]['lanes'] = edge['lanes']
        return graph

    def add_lane(self, _graph, edge, nodes_tuple, prefer_smaller_side=True):        
        lanes = edge["lanes"] if "lanes" in edge else '1' # min in place for roads with varying lane sizes.

        try:
            if prefer_smaller_side:
                edge['lanes'] = str(int(min(lanes)) + 1)
            else:
                edge['lanes'] = str(int(max(lanes)) + 1)
        except Exception as e:
            pprint(e)
        
        _graph[nodes_tuple[0]][nodes_tuple[1]][nodes_tuple[2]]['lanes'] = edge['lanes']
        return _graph

    def reverse_lane(self, graph, edge, nodes_tuple, prefer_smaller_side=True):
        #pprint(edge)
        if len(edge["lanes"]) == 1:
            try:
                attrs = graph[nodes_tuple[0]][nodes_tuple[1]][nodes_tuple[2]] # Get attributes from current road
                graph.remove_edge(nodes_tuple[0], nodes_tuple[1], nodes_tuple[2]) # Remove current road
                graph.add_edge(nodes_tuple[1], nodes_tuple[0], nodes_tuple[2]) # add reverse road
                
                for key in attrs.keys():
                    graph[nodes_tuple[1]][nodes_tuple[0]][nodes_tuple[2]][key] = attrs[key]
            except Exception as e:
                pprint(e)
                print('Unable to reverse this lane.')

        elif len(edge["lanes"]) == 2:
            edge["lanes"][0] = int(edge["lanes"][0]) - 1
            edge["lanes"][1] = int(edge["lanes"][1]) + 1
            graph[nodes_tuple[0]][nodes_tuple[1]][nodes_tuple[2]]['lanes'] = edge['lanes']

        return graph

    def average_time_step(self, Gs, origin, dest):
        if origin == dest:
            return 0
        else:
            try:
                shortest_path = nx.shortest_path(Gs, origin, dest, weight='travel_time')                # Sub travel time for cars/lane/km
                shortest_path_length = nx.shortest_path_length(Gs, origin, dest, weight='travel_time')  # Sub travel time for cars/lane/km
                if shortest_path_length > self.threshold:        
                    return shortest_path_length
            except:
                return 3000


    # def averate_time_step(*args, **kwargs):
    #     return self.average_time_step(*args, *kwargs)

    def get_average_time(self, Gs, threshold):
        total_time = 0
        total_routes = 0
        node_pairs = []
        for origin in Gs.nodes.keys():
            for dest in Gs.nodes.keys():
                node_pairs.append((origin, dest))
        with concurrent.futures.ThreadPoolExecutor() as executor:
            res = {executor.submit( self.average_time_step, Gs, pair[0], pair[1]) for pair in node_pairs}

            for future in concurrent.futures.as_completed(res):
                edge_time = future.result()
                if edge_time == 0 or edge_time == None:
                    pass
                else:
                    total_time += edge_time
                    total_routes += 1  
            executor.shutdown()     
        
        if(total_routes >= 1):
            return (total_time/total_routes)
        else:
            return 0
    
    def add_lanes(self, graph):
        edges = graph.edges(keys=True, data=True)
        for u, v, k, data in edges:
            if "lanes" not in data:
                data["lanes"] = '1'
        return graph

    def get_vehichle_density(self, graph, vehichles_per_km=25, timesteps=1):
        p_table = self.get_probability_table(graph)
        vehichles = []
        for u, v, k, data in graph.edges(keys=True, data=True):
            edge_kms = int(min(data['lanes'])) * data['length']
            vehichles.append(vehichles_per_km * edge_kms)
        
        for i in range(timesteps):
            vehichles = numpy.matmul(vehichles, p_table)/1000
        
        return vehichles


    def apply_changes(self, graph, change):
        pprint(change)
        change_type = change['type']
        edge = change['edge']       
        if (edge == (0, 0, 0)):
            pprint(f"No better solution was found.")
            return graph
        u, v, k = edge

        # Changed to length based instead of cost
        self.budget -= graph[u][v][k]['length'] #self.get_cost(graph, change_type, edge)
        
        data = graph[edge[0]][edge[1]][edge[2]]
        if change_type == "add_lane": 
            self.changes.append(edge)
            pprint(f'Adding lane to {edge}')
            graph = self.add_lane(graph, data, edge)
            return graph
        elif change_type == "remove_lane": 
            self.changes.append(edge)
            pprint(f'Removing lane from {edge}')
            graph = self.remove_lane(graph, data, edge)
            return graph
        elif change_type == "reverse_lane": 
            self.changes.append((edge[1], edge[0], edge[2]))
            pprint(f'Reversing 1 lane on {edge}')
            graph = self.reverse_lane(graph, data, edge)
            return graph
        return graph
    
    
    def get_cost (self, graph, type, edge):
        length = graph[edge[0]][edge[1]][edge[2]]['length']

        return(length*self.prices[type])

    def get_density_colors (self, densities):
        colors = []
        for dens in densities:
            if dens < 7:
                colors.append('w')
            elif dens < 11:
                colors.append('b')
            elif dens < 16:
                colors.append('g')
            elif dens < 22:
                colors.append('y')
            elif dens < 28:
                colors.append('orange')
            else:
                colors.append('r')
        return colors


    def density(self, graph, budget, file_name, only_primary=False, n_densities=10):
        self.budget = budget
        graph = ox.add_edge_speeds(graph, fallback=50.0) # Add max speed to lanes
        graph = ox.add_edge_travel_times(graph) # Add travel time to lanes
        graph = self.add_lanes(graph) # Some edges don't have lanes on OSM, so we set them to 1
        graph = self.add_edge_max_cars(graph) # Add max amount of cars for all edges
        starting_densities = self.get_vehichle_density(graph)      
        pprint(f"Starting total density={sum(starting_densities)}")  
        worst_n_densities = sum(sorted(starting_densities, reverse=True)[:n_densities])

        curr_best = {"density":worst_n_densities,
                    "type": None,
                    "edge": None}    

        while self.budget > 0:
            graph = ox.add_edge_travel_times(graph) # Add travel time to lanes
            edges = graph.edges(keys=True, data=True) # Initialize edges
            
            if curr_best['edge'] == (0, 0, 0):
                break

            curr_best = {"density":worst_n_densities,
                        "type": None,
                        "edge": (0, 0, 0)}            
            
            pprint(f'Budget remaining: {self.budget}')
            for u, v, k, data in edges:
                data["passed"] = False

            for u, v, k, data in edges:
                if (data["highway"] != "primary") and only_primary:
                    continue

                improvements_edge = {} # Reset average times for the new edge
                
                aux_graph = copy.deepcopy(graph)
                edge = aux_graph.edges[(u, v, k)]
                aux_graph = self.add_lane(aux_graph, edge, (u, v, k))
                new_densities = self.get_vehichle_density(aux_graph)
                improvements_edge["add_lane"] = sum(sorted(new_densities, reverse=True)[:n_densities])
                
                aux_graph = copy.deepcopy(graph)
                edge = aux_graph.edges[(u, v, k)]
                aux_graph = self.remove_lane(aux_graph, edge, (u, v, k))
                new_densities = self.get_vehichle_density(aux_graph)
                improvements_edge["remove_lane"] = sum(sorted(new_densities, reverse=True)[:n_densities])
                
                aux_graph = copy.deepcopy(graph)
                edge = aux_graph.edges[(u, v, k)]
                aux_graph = self.reverse_lane(aux_graph, edge, (u, v, k))
                new_densities = self.get_vehichle_density(aux_graph)
                improvements_edge["reverse_lane"]= sum(sorted(new_densities, reverse=True)[:n_densities])
                if curr_best['density'] > min(improvements_edge.values()):
                    new_best = min(improvements_edge.values())
                    new_type = min(improvements_edge, key=improvements_edge.get)
                    new_edge =  (u, v, k)

                    cost = graph[u][v][k]['length'] #self.get_cost(graph, new_type, new_edge)
                    if self.budget >= cost:
                        curr_best = {
                            "density": new_best,
                            "type": new_type,
                            "edge": new_edge
                            }

            graph = self.apply_changes(graph, curr_best)        
            worst_n_densities = curr_best["density"]
            pprint(f'Budget remaining: {self.budget}')

        n_densities = self.get_vehichle_density(graph)
        print(n_densities)
        ec = self.get_density_colors(n_densities)

        n_densities = (n_densities/max(n_densities))+0.25
        ox.plot_graph(graph, edge_color=ec, show=False, node_size=0, edge_linewidth=n_densities, save=True, filepath=f'{file_name}_{budget}.png')

        ec = []
        el = []
        for u, v, k, d in graph.edges(keys=True, data=True): 
            if (u, v, k) in self.changes:
                ec.append('r')
                el.append(0.7)
            else:
                ec.append('b')
                el.append(0.3)
        ox.plot_graph(graph, edge_color=ec, show=False, node_size=0, edge_linewidth=el, save=True, filepath=f'{file_name}_{budget}_changes.png')



        pprint(f"Best possible solution for this budget: {sum(self.get_vehichle_density(graph))}")


    def traveltime(self, graph, budget, file_name, only_primary=False):
        self.budget = budget
        graph = ox.add_edge_speeds(graph, fallback=50.0) # Add max speed to lanes
        graph = ox.add_edge_travel_times(graph) # Add travel time to lanes
        graph = self.add_lanes(graph) # Some edges don't have lanes on OSM, so we set them to 1
        graph = self.add_edge_max_cars(graph) # Add max amount of cars for all edges
        starting_average_travel = self.get_average_time(graph, self.threshold) # ignore passes for this analysis
        pprint(starting_average_travel)

        curr_best = {"traveltime":starting_average_travel,
                    "type": None,
                    "edge": None}    

        while self.budget > 0:
            graph = ox.add_edge_travel_times(graph) # Add travel time to lanes
            edges = graph.edges(keys=True, data=True) # Initialize edges
            
            if curr_best['edge'] == (0, 0, 0):
                break

            curr_best = {"traveltime":starting_average_travel,
                        "type": None,
                        "edge": (0, 0, 0)}            

            pprint(f'Budget remaining: {self.budget}')
            for u, v, k, data in edges:
                data["passed"] = False
            for u, v, k, data in edges:
                if data["highway"] != "primary":
                    continue

                improvements_edge   = {} # Reset average times for the new edge 
                
                aux_graph = copy.deepcopy(graph)
                edge = aux_graph.edges[(u, v, k)]
                aux_graph = self.add_lane(aux_graph, edge, (u, v, k))
                aux_graph = ox.add_edge_travel_times(aux_graph) # Update travel time to lanes
                improvements_edge["add_lane"] = self.get_average_time(aux_graph, self.threshold)
                
                aux_graph = copy.deepcopy(graph)
                edge = aux_graph.edges[(u, v, k)]
                aux_graph = self.remove_lane(aux_graph, edge, (u, v, k))
                aux_graph = ox.add_edge_travel_times(aux_graph) # Update travel time to lanes
                improvements_edge["remove_lane"] = self.get_average_time(aux_graph, self.threshold)
                
                aux_graph = copy.deepcopy(graph)
                edge = aux_graph.edges[(u, v, k)]
                aux_graph = self.reverse_lane(aux_graph, edge, (u, v, k))
                improvements_edge["reverse_lane"]= self.get_average_time(aux_graph, self.threshold)
        
                
                if curr_best['traveltime'] > min(improvements_edge.values()):
                    new_best = min(improvements_edge.values())
                    new_type = min(improvements_edge, key=improvements_edge.get)
                    new_edge =  (u, v, k)

                    cost = self.get_cost(graph, new_type, new_edge)
                    if self.budget >= cost:
                        pprint(cost)
                        curr_best = {
                            "traveltime": new_best,
                            "type": new_type,
                            "edge": new_edge
                            }
                        pprint(curr_best)

                
                data["passed"] = True
                graph.add_edge(u, v, key=k, 
                osmid=data['osmid'],
                oneway=data['oneway'],
                lanes=data['lanes'],
                highway=data['highway'],
                reversed=data['reversed'],
                length=data['length'],
                geometry=data['geometry'],
                speed_kph=data['speed_kph'],             
                travel_time=data['travel_time'],
                max_cars=data['max_cars'],
                passed=data['passed'],)

            graph = self.apply_changes(graph, curr_best)        
            starting_average_travel = curr_best["traveltime"]
            pprint(f'Budget remaining: {self.budget}')
        pprint(f"Best possible solution for this budget: {self.get_average_time(graph, self.threshold)}")
        
        pprint(self.changes)
        ec = []
        el = []
        for u, v, k, d in graph.edges(keys=True, data=True): # update colormap to visualize progress       
            if (u, v, k) in self.changes:
                ec.append('r')
                el.append(0.7)
            else:
                ec.append('b')
                el.append(0.3)
        ox.plot_graph(graph, edge_color=ec, show=False, node_size=0, edge_linewidth=el, save=True, filepath=f'{file_name}_{budget}.png')

