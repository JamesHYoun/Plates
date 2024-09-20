import asyncio
import os
import django
from django.core.asgi import get_asgi_application
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

import networkx as nx
from django.shortcuts import render
from django.http import JsonResponse

import random



import socketio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plates_project.settings')
# django.setup()

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins = [
        'http://localhost:8001',
    ])

sio_app = socketio.ASGIApp(sio, socketio_path='/socket.io/')
# sio_app = asgi_cors(sio_app, allow_all=True)
# sio_app = socketio.ASGIApp(sio)

django_asgi_app = get_asgi_application()


application = sio_app

# application = ProtocolTypeRouter({
#     "http": django_asgi_app,        
#     "websocket": sio_app  # Handle WebSocket requests with Socket.IO
# })

# Define Socket.IO events

num_nodes = 4
graph_edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
graph_colors = ['' for _ in range(num_nodes)]

connected_clients = set()  # Set to track connected clients
ready_event = asyncio.Event()  # Event to signal when two clients are connected

@sio.on('connect')
async def connect(sid, environ):
    print('Client connected:', sid)
    connected_clients.add(sid)  # Add the new client
    if len(connected_clients) == 2:
        ready_event.set()  # Signal that we have two clients
    await sio.emit('connect')

@sio.on('disconnect')
async def disconnect(sid):
    global graph_colors
    connected_clients.remove(sid)  # Remove the client
    if len(connected_clients) < 2:
        graph_colors = ['' for _ in range(num_nodes)]
        ready_event.clear()  # Reset the event since we no longer have two clients
    print('Client disconnected:', sid)

@sio.on('updateToServer')
async def updateToServer(sid, data):
    print('Received gameState:', data)
    await sio.emit('updateFromServer', data)

@sio.on('updateFromServer')
async def updateFromServer(sid, data):
    print('Received updateGame:', data)
    await sio.emit('updateGame', data)

@sio.on('getRequest')
async def getRequest(sid):
    # planar_graph = nx.random_planar_graph(n)
    print('ENTEREDDDDD')
    if len(connected_clients) == 1:
        team = 'white'
        for i in random.sample(range(0, num_nodes), num_nodes // 2):
            graph_colors[i] = team    
    else:
        team = 'black'
        for i,x in enumerate(graph_colors):
            if x == '':
                graph_colors[i] = team

    print(graph_colors)

    await ready_event.wait()

    graph = nx.Graph(graph_edges)  # Example planar graph
    pos = nx.planar_layout(graph)

    pos_list = {node: pos[node].tolist() for node in pos.keys()}

    data = {
        "team": team,
        "graph-colors": graph_colors,
        "edges": list(graph_edges),
        "positions": pos_list
    }
    await sio.emit('gameData', data, room=sid)

    # nx.draw(planar_graph, pos, with_labels=True)
    # plt.show()
