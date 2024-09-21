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

max_rooms = 10

sid_to_room = {}
sid_to_team = {}

unmatched_sids = set([])

room_to_edges = [[] for _ in range(max_rooms)]
room_to_colors = [[] for _ in range(max_rooms)]
room_to_positions = [{} for _ in range(max_rooms)]

num_nodes = 4

matched = False

connected_clients = set()  # Set to track connected clients
ready_event = asyncio.Event()  # Event to signal when two clients are connected

@sio.on('connect')
async def connect(sid, environ):
    await sio.emit('connect', {'message': 'You are connected!'}, room=sid)

@sio.on('reconnect')
async def reconnect(sid, data):
    sid = data['socketId']  # Access the socketId from the data

    if sid in sid_to_room:
        room_id = sid_to_room[sid]
        graph_colors = room_to_colors[room_id]
        graph_edges = room_to_edges[room_id]
        graph_position = room_to_positions[room_id]

        data = {
            "team": sid_to_team[sid],
            "colors": graph_colors,
            "edges": graph_edges,
            "positions": graph_position
        }
        await sio.emit('gameData', data, room=sid)        
    else:
        room_id = -1
        for i in range(max_rooms):
            if not room_to_colors[i]:
                room_id = i

        if room_id == -1:   # There are no rooms available
            await sio.emit('connect', {})

        else:   # There are rooms
            if unmatched_sids:    # If there is an unmatched player
                print('--------------')
                print('SHOULD NOT ENTER')
                print('--------------')
                opp_sid = unmatched_sids.pop()
                print(sid)
                print(opp_sid)

                sid_to_room[sid] = room_id
                sid_to_room[opp_sid] = room_id

                # graph edges generation
                graph_edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
                room_to_edges[room_id] = graph_edges

                graph_colors = ['' for _ in range(num_nodes)]
                for i in random.sample(range(0, num_nodes), num_nodes // 2):
                    graph_colors[i] = 'white'    
                for i,x in enumerate(graph_colors):
                    if x == '':
                        graph_colors[i] = 'black'
                
                room_to_colors[room_id] = graph_colors

                graph = nx.Graph(graph_edges)  # Example planar graph
                position = nx.planar_layout(graph)

                graph_position = {node: position[node].tolist() for node in position.keys()}
                room_to_positions[room_id] = graph_position

                sid_to_team[sid] = 'black'
                data = {
                    "team": 'black',
                    "colors": graph_colors,
                    "edges": graph_edges,
                    "positions": graph_position
                }
                await sio.emit('gameData', data, room=sid)

                sid_to_team[opp_sid] = 'white'
                data = {
                    "team": 'white',
                    "colors": graph_colors,
                    "edges": graph_edges,
                    "positions": graph_position
                }
                await sio.emit('gameData', data, room=opp_sid)
            else:
                print('ENTEREDDDDD')
                unmatched_sids.add(sid)

@sio.on('disconnect')
async def disconnect(sid):
    global graph_colors
    connected_clients.remove(sid)  # Remove the client
    if len(connected_clients) < 2:
        graph_colors = ['' for _ in range(num_nodes)]
        matched = False
        ready_event.clear()  # Reset the event since we no longer have two clients

@sio.on('updateToServer')
async def updateToServer(sid, data):
    await sio.emit('updateFromServer', data)

@sio.on('updateFromServer')
async def updateFromServer(sid, data):
    await sio.emit('updateGame', data)




    # nx.draw(planar_graph, pos, with_labels=True)
    # plt.show()
