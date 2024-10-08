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
django.setup()

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

org_to_new = {}

max_rooms = 10

sid_to_room = {}
sid_to_team = {}
room_to_sid = {}

unmatched_sids = set([])

room_to_player = ['white' for _ in range(max_rooms)]
room_to_teamIdx = [{} for _ in range(max_rooms)]
room_to_edges = [[] for _ in range(max_rooms)]
room_to_colors = [[] for _ in range(max_rooms)]
room_to_positions = [{} for _ in range(max_rooms)]

num_nodes = 6

@sio.on('connect')
async def connect(sid, environ):
    print('connected')
    # await sio.emit('connect', {'message': 'You are connected!'}, room=sid)

@sio.on('reconnect')
async def reconnect(sid, data):
    sid_org = data['socketId']  # Access the socketId from the data

    if sid_org in sid_to_room:

        print('---------')
        print('ENTERED')
        org_to_new[sid_org] = sid
        room_id = sid_to_room[sid_org]

        graph_teamIdx = room_to_teamIdx[room_id]
        white_idx = graph_teamIdx['white']
        black_idx = graph_teamIdx['black']
        graph_colors = room_to_colors[room_id]
        graph_edges = room_to_edges[room_id]
        graph_position = room_to_positions[room_id]

        team = sid_to_team[sid_org]
        player = room_to_player[room_id]

        data = {
            "team": team,
            "player": player,
            "colors": graph_colors,
            "edges": graph_edges,
            "positions": graph_position,
            "white-idx": white_idx,
            "black-idx": black_idx
        }

        print(data)

        await sio.emit('gameData', data, room=sid) 

        # sids = room_to_sid[room_id]
        # sid_iter = iter(sids)
        # sid1 = next(sid_iter)
        # sid2 = next(sid_iter)
        # if sid1 == sid_org:
        #     sid_opp = sid2
        # else:
        #     sid_opp = sid1

        # sid_opp = org_to_new[sid_opp]

        # team = sid_to_team[sid_opp]

        # data = {
        #     "team": team,
        #     "player": player,
        #     "colors": graph_colors,
        #     "edges": graph_edges,
        #     "positions": graph_position,
        #     "white-idx": white_idx,
        #     "black-idx": black_idx
        # }
        # await sio.emit('gameData', data, room=sid_opp)         
    else:
        # Check whether there's a free room
        room_id = -1
        for id in range(max_rooms):
            if id not in room_to_sid:
                room_id = id

        if room_id == -1:   # There are no rooms available
            pass
        else:   # There are rooms
            if unmatched_sids:    # If there is an unmatched player

                sid_to_room[sid_org] = room_id
                room_to_sid[room_id] = set([])
                room_to_sid[room_id].add(sid_org)

                opp_sid = unmatched_sids.pop()
                
                sid_to_room[opp_sid] = room_id
                room_to_sid[room_id].add(opp_sid)
                # graph edges generation

                org_to_new[sid_org] = sid_org
                org_to_new[opp_sid] = opp_sid
                
                graph_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (0, 4), (1, 3), (0, 3), (3, 5)]
                room_to_edges[room_id] = graph_edges

                graph_colors = ['' for _ in range(num_nodes)]
                graph_colors[0] = 'white'
                graph_colors[4] = 'white'
                graph_colors[5] = 'white'
                graph_colors[1] = 'black'
                graph_colors[2] = 'black'
                graph_colors[3] = 'black'

                ### NOTES ###
                # Make this a turn-based game
                # Make sure every node has at least two edges. One edge can lead to one player blocking the other.

                ### MAIN LOGIC ###
                # for i in random.sample(range(0, num_nodes), num_nodes // 2):
                #     graph_colors[i] = 'white'    
                # for i,x in enumerate(graph_colors):
                #     if x == '':
                #         graph_colors[i] = 'black'
                
                room_to_colors[room_id] = graph_colors

                graph = nx.Graph(graph_edges)  # Example planar graph
                position = nx.planar_layout(graph)

                graph_position = {node: position[node].tolist() for node in position.keys()}
                room_to_positions[room_id] = graph_position

                white_idx = room_to_teamIdx[room_id]['white'] = 0
                black_idx = room_to_teamIdx[room_id]['black'] = 1

                player = room_to_player[room_id]


                ### MAIN LOGIC ###
                # white_position = random.randint(0, num_nodes)
                # black_position = random.randint(0, num_nodes)
                # while white_position == black_position:
                #     white_position = random.randint(0, num_nodes)
                #     black_position = random.randint(0, num_nodes)

                sid_to_team[sid] = 'white'

                data = {
                    "team": 'white',
                    "player": player,
                    "colors": graph_colors,
                    "edges": graph_edges,
                    "positions": graph_position,
                    "white-idx": white_idx,
                    "black-idx": black_idx
                }

                await sio.emit('gameData', data, room=sid_org)

                sid_to_team[opp_sid] = 'black'

                data = {
                    "team": 'black',
                    "player": player,
                    "colors": graph_colors,
                    "edges": graph_edges,
                    "positions": graph_position,
                    "white-idx": white_idx,
                    "black-idx": black_idx
                }

                await sio.emit('gameData', data, room=opp_sid)
            else:
                unmatched_sids.add(sid_org)

@sio.on('disconnect')
async def disconnect(sid):
    pass

@sio.on('click')
async def click(sid, data):
    print('----------')
    print('click')
    sid_org = data['socketId']
    room_id = sid_to_room[sid_org]
    sids = room_to_sid[room_id]
    sid_iter = iter(sids)
    sid1 = next(sid_iter)
    sid2 = next(sid_iter)
    if sid1 == sid_org:
        sid_opp = sid2
    else:
        sid_opp = sid1

    room_to_player[room_id] = sid_to_team[sid_opp]

    team = sid_to_team[sid_org]
    idx = data['idx']
    room_to_colors[room_id][idx] = team

    graph_teamIdx = room_to_teamIdx[room_id]

    graph_teamIdx[team] = idx

    data = {
        "idx": idx
    }

    sid_opp = org_to_new[sid_opp]

    print('----------------')
    print(sid_opp)
    await sio.emit('continue', data, room=sid_opp)

'''
sid_to_room = {}
sid_to_team = {}
room_to_sid = {}

unmatched_sids = set([])

room_to_edges = [[] for _ in range(max_rooms)]
room_to_colors = [[] for _ in range(max_rooms)]
room_to_positions = [{} for _ in range(max_rooms)]
'''

@sio.on('endGame')
async def endGame(sid, data):
    sid_org = data['socketId']  # Access the socketId from the data
    room_id = sid_to_room[sid_org]
    sids = room_to_sid[room_id]
    sid1 = sids.pop()
    sid2 = sids.pop()
    if sid1 == sid_org:
        opp_sid = sid2
    else:
        opp_sid = sid1
    del sid_to_room[sid1]
    del sid_to_room[sid2]
    del sid_to_team[sid1]
    del sid_to_team[sid2]
    del room_to_sid[room_id]

    room_to_teamIdx[room_id] = {}
    room_to_edges[room_id] = []
    room_to_colors[room_id] = []
    room_to_positions[room_id] = {}

    opp_sid = org_to_new[opp_sid]

    del org_to_new[sid1]
    del org_to_new[sid2]

    await sio.emit('endGame', room=opp_sid)

@sio.on('updateToServer')
async def updateToServer(sid, data):
    await sio.emit('updateFromServer', data)

@sio.on('updateFromServer')
async def updateFromServer(sid, data):
    await sio.emit('updateGame', data)




    # nx.draw(planar_graph, pos, with_labels=True)
    # plt.show()
