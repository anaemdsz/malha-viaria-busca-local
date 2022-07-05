from load_place import create_net_file_from
import osmnx as ox
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from pprint import pprint
import copy
import multiprocessing
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

    def remove_lane(self, graph, edge, nodes_tuple, prefer_smaller_side=True):
        lanes = edge['lanes']
        if lanes == '1':
            return graph
        try:
            if prefer_smaller_side:
                edge['lanes'] = str(int(min(lanes)) - 1)
            else:
                edge['lanes'] = str(int(max(lanes)) - 1)
        except e:
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
        except e:
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

    def reduce_edge_traveltime(self, graph, edge, reduction):
        try:
            edge['travel_time'] = edge['travel_time']* ((100-reduction)/100)
        except:
            pass

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
        # impute missing edge speeds and add travel times
        # Gs = ox.add_edge_speeds(Gs, fallback=50.0)
        # Gs = ox.add_edge_travel_times(Gs)
        node_pairs = []
        for origin in Gs.nodes.keys():
            for dest in Gs.nodes.keys():
                node_pairs.append((origin, dest))
        #times_traversed, total_time, total_routes
        lock = multiprocessing.Manager().Lock()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            res = {executor.submit( self.average_time_step, Gs, pair[0], pair[1]) for pair in node_pairs}

            i = 1
            for future in concurrent.futures.as_completed(res):
                print(f'{i}/{len(node_pairs)}', end='\r')
                i +=1
                #pprint(future.result())
                edge_time = future.result()
                if edge_time == 0 or edge_time == None:
                    pass
                else:
                   #with lock:
                    total_time += edge_time
                    total_routes += 1  
            executor.shutdown()     
        
        if(total_routes >= 1):
            return (total_time/total_routes)
        else:
            return 0
    
    
    def add_edge_max_cars(self, graph, average_car=4):
        # We consider an average car length of 4 meters.
        edges = graph.edges(keys=True, data=True)
        for u, v, k, data in edges:
            lanes = min(data['lanes'])
            data["max_cars"] = int(lanes)*(data["length"]/average_car)
        
        return graph

    def add_lanes(self, graph):
        edges = graph.edges(keys=True, data=True)
        for u, v, k, data in edges:
            if "lanes" not in data:
                data["lanes"] = '1'
        
        return graph

    def apply_changes(self, graph, change):
        pprint(change)
        change_type = change['type']
        edge = change['edge']       
        if (edge == (0, 0, 0)):
            pprint(f"No better solution was found.")
            return graph

        self.budget -= self.get_cost(graph, change_type, edge)
        
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



    def neighborhood_search(self, graph, budget, file_name, only_primary=False):
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
            
            i = 1
            pprint(f'Budget remaining: {self.budget}')
            for u, v, k, data in edges:
                data["passed"] = False
            for u, v, k, data in edges:
                pprint(f'{datetime.now()} -- {i}/{len(edges)}: {(u, v, k)}')
                # pprint(data)
                i += 1
                if data["highway"] != "primary":
                    continue

                improvements_edge   = {} # Reset average times for the new edge 
                
                # Uncomment for visuals on the progress, slows down program.
                # ec = []
                # for x, y, z, d in edges: # update colormap to visualize progress
                #     #print(data)
                #     if u == x and v ==  y:
                #         ec.append('r')
                #     elif d["passed"] == True:
                #         ec.append('g')
                #     else:
                #         ec.append('y')
                # ox.plot_graph(graph, edge_color=ec, show=False, node_size=0, edge_linewidth=0.3, save=True, filepath=f'ufsc.png')
                
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
                improvements_edge["reverse_lane"]= self.get_average_time(self.reverse_lane(aux_graph, edge, (u, v, k)), self.threshold)
        
                
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
        # Uncomment for visuals on the progress, slows down program.
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

