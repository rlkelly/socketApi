  #!/usr/bin/env python

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on available packages.
async_mode = None

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey
            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

    print('async_mode is ' + async_mode)

# monkey patching is necessary because this application uses a background
# thread
if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()
elif async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()

import time
from threading import Thread
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

from flask_restful import Resource, Api

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
api = Api(app)
socketio = SocketIO(app, async_mode=async_mode)
thread = None


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        time.sleep(10)
        count += 1
        socketio.emit('my response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')


@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.daemon = True
        thread.start()
    return render_template('index.html')


class Assets(Resource):
    def get(self):
        assets = {"assets":[{"deviceID":1, "id":1, "isActive":True, "name":"Jim", "type":"Personnel", "metadata":{"assetClass": "Welder", "classification": "Welder", "age": 35, "inDate":"2015-04-23T18:25:43.511Z", "experience":10, "taskOrder":12345, "phone": "234-234-4595" }},
                            {"deviceID":2, "id":2, "isActive":True, "name":"Jeb", "type":"Personnel", "metadata":{"assetClass": "Foreman", "classification": "Foreman", "age": 45, "inDate":"2015-04-23T18:25:43.511Z", "experience":15, "taskOrder":12345, "phone": "234-234-4595" }},
                            {"deviceID":3, "id":3, "isActive":True, "name":"Bob", "type":"Personnel", "metadata":{"assetClass": "Foreman", "classification": "Geologist", "age": 45, "inDate":"2015-04-23T18:25:43.511Z", "experience":10, "taskOrder":12345, "phone": "234-234-4595" }},
                            {"deviceID":4, "id":4, "isActive":True, "name":"#345345", "type":"Material", "metadata":{"assetClass": "Piping", "classification": "Piping", "details":"Black steel ASTM A53, Grade B, seamless, Schedule 40 with threaded ends", "inDate":"2015-04-23T18:25:43.511Z", "taskOrder":12345}},
                            {"deviceID":5, "id":5, "isActive":True, "name":"ID# 544", "type":"Vehicle", "metadata":{"assetClass": "Vehicle", "classification": "Forklift", "model":"H800-1050HDS", "inDate":"2015-04-23T18:25:43.511Z", "taskOrder":12345}}]}
        return assets

class Buildings(Resource):
    def get(self):
        buildings = {"buildings":[{"id":1, "name":"Tengiz Field"}]}
        return buildings

class Floors(Resource):
    def get(self):
        floors = {"floors":[{"id": 1, "buildingId":1, "floorIndex":1, "floorName":"Lay Down Yard", "Oil&Gas_Zonesmap_050416_yard%20large.svg":"field", "origin":{"x":0, "y":0}, "scaleFactor":1},
                            {"id": 2, "buildingId":1, "floorIndex":2, "floorName":"Main Ops", "Oil&Gas_Zonesmap_050416_yard%20large.svg":"field", "origin":{"x":0, "y":0}, "scaleFactor":1},
                            {"id": 3, "buildingId":1, "floorIndex":3, "floorName":"Drop Off Zones", "Oil&Gas_Zonesmap_050416_yard%20large.svg":"field", "origin":{"x":0, "y":0}, "scaleFactor":1},
                            {"id": 4, "buildingId":1, "floorIndex":4, "floorName":"Gravel Base", "Oil&Gas_Zonesmap_050416_yard%20large.svg":"field", "origin":{"x":0, "y":0}, "scaleFactor":1},
                            {"id": 5, "buildingId":1, "floorIndex":5, "floorName":"Office Building", "Oil&Gas_Zonesmap_050416_yard%20large.svg":"field", "origin":{"x":0, "y":0}, "scaleFactor":1},
                            {"id": 5, "buildingId":1, "floorIndex":5, "floorName":"Rail Depo", "Oil&Gas_Zonesmap_050416_yard%20large.svg":"field", "origin":{"x":0, "y":0}, "scaleFactor":1},
                        ]}
        return floors

api.add_resource(Assets, '/assets')
api.add_resource(Buildings, '/buildings')
api.add_resource(Floors, '/floors')


@socketio.on('my event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my broadcast event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    print(message)
    print('xyz')
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my room event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True)
