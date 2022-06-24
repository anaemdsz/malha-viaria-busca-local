
import os
import osmnx as ox
import networkx as nx

import matplotlib.pyplot as pyplot

useful_tags_node = ox.settings.useful_tags_node
osm_xml_node_attrs = ox.settings.osm_xml_node_attrs
osm_xml_node_tags = ox.settings.osm_xml_node_tags
useful_tags_way = ox.settings.useful_tags_way
osm_xml_way_attrs = ox.settings.osm_xml_way_attrs
osm_xml_way_tags = ox.settings.osm_xml_way_tags

config_parameters = {
    "useful_tags_node": list(set(useful_tags_node + osm_xml_node_attrs + osm_xml_node_tags)),
    "useful_tags_way": list(set(useful_tags_way + osm_xml_way_attrs + osm_xml_way_tags)),
    "all_oneway": True
}

def create_net_file_from(place_name):
    outputName=place_name #.replace(" ", "_")
    file_name = outputName+".net"

    if os.path.exists(file_name):
        return file_name
    else:
        ox.config(**config_parameters)


        # loads driveable streets as a graph from the place name
        # more in: https://geoffboeing.com/2016/11/osmnx-python-street-networks/
        graph = ox.graph_from_place(place_name, simplify=False,  network_type='drive')

        # converts "graph" to a simpler .net file
        nx.write_pajek(graph, file_name)

        # nx.write_graphml(graph, "output.graphml")
        # ox.save_graph_xml(graph, filepath='output.osm')
        # fig, ax = ox.plot_graph(graph)


        #pyplot.tight_layout()
        return file_name