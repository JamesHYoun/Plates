import networkx as nx
import numpy as np
import json
from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
def home_view(request):    
    return None

def play_view(request):
    if request.method == "GET":
        graph_edges = [(0, 1), (1, 2), (2, 0)]
        graph = nx.Graph(graph_edges)  # Example planar graph
        pos = nx.planar_layout(graph)

        pos_list = {node: pos[node].tolist() for node in pos.keys()}

        graph_info = {
            "edges": list(graph.edges),
            "positions": pos_list
        }
    
        return JsonResponse(graph_info)
    return None