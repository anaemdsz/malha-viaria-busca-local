from load_place import create_net_file_from
import osmnx as ox
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from pprint import pprint

class NetworkOptimization:
    
    def __init__(self):
        pass

    def reduce_edge_traveltime(self, graph, edge, reduction):
        try:
            print(edge)
            edge['travel_time'] = edge['travel_time']* ((100-reduction)/100)
            print(edge)
        except:
            pass


    def get_average_time(self, Gs, threshold):
        total_time = 0
        total_routes = 0
        times_traversed = {}
        # impute missing edge speeds and add travel times
        Gs = ox.add_edge_speeds(Gs, fallback=50.0)
        Gs = ox.add_edge_travel_times(Gs)
        for origin in Gs.nodes.keys():
            for dest in Gs.nodes.keys():
                if origin == dest:
                    pass
                else:
                    shortest_path = nx.shortest_path(Gs, origin, dest, weight='travel_time')
                    shortest_path_length = nx.shortest_path_length(Gs, origin, dest, weight='travel_time')
                    if shortest_path_length > threshold:
                        total_time += shortest_path_length
                        total_routes += 1
                        for i in range(len(shortest_path)-1):
                            edge = (shortest_path[i], shortest_path[i+1])
                            if edge not in times_traversed.keys():
                                times_traversed[edge] = 1
                            else:
                                times_traversed[edge] += 1
        
        if(total_routes >= 1):
            return round(total_time/total_routes), times_traversed
        else:
            return 0, times_traversed
    
    
    def add_edge_max_cars(self, graph, average_car=4):
        # We consider an average car length of 4 meters.
        edges = graph.edges(keys=True, data=True)
        for u, v, k, data in edges:
            lanes = min(data["lanes"]) if "lanes" in data else 1 # min in place for roads with varying lane sizes.
            data["max_cars"] = int(lanes)*(data["length"]/average_car)
        
        return graph


    def neighborhood_search(self, graph, moves_allowed):
        graph = ox.add_edge_speeds(graph, fallback=50.0) # Add max speed to lanes
        graph = ox.add_edge_travel_times(graph) # Add travel time to lanes
        graph = self.add_edge_max_cars(graph) # Add max amount of cars for all edges
   
        edges = graph.edges(keys=True, data=True)
        best_improvement = 0 # Best average travel time reduction.
        starting_average_travel, ignore = 99, 0 #self.get_average_time(graph, 60)
        print(starting_average_travel)

        improvements = {}

        #   for ALLOWED_MOVES
        #       For every edge  
        #           improvement_list = get all improvements for the edge (speed_limit_increase, add_lane)
        #           improvemnt_times = average_travel_time(improvement_list)       
        #           edge_improve = MAX(improvement_times)
        #           improvements[edge] = edge_improve
        #       
        #       best_neighbor = MAX(improvements)
        #       graph = do_move(graph, best_neighbor)
        #   return graph


        for i in range(moves_allowed):
            for u, v, k, data in edges:
                edge = graph.edges[(u, v, k)]
                print(edge == data)
                self.reduce_edge_traveltime(graph, edge, 10)
                #improvements_average[str(edge)] =  
