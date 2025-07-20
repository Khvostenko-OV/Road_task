import json

from flask import jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash

from app import app
from db_sync import db_session
from models import Map, Network, User


@app.route("/")
def hello():
    return jsonify({"message": "Hello!"})


@app.route("/add_user", methods=["post"])
def add_user():
    username = request.form.get("login")
    password = request.form.get("password")
    if not username or not password:
        return jsonify({"error": "Login and password are required"}), 400

    if User.user_exists(username):
        return jsonify({"error": f"User '{username}' already exists"}), 400

    try:
        user = User(username=username, password_hash=generate_password_hash(password))

        db_session.add(user)
        db_session.commit()

    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500

    login_user(user)
    return jsonify(user.to_dict)


@app.route("/login", methods=["post"])
def login():
    username = request.form.get("login")
    password = request.form.get("password")
    if not username or not password:
        return jsonify({"error": "Login and password are required"}), 400

    user = db_session.query(User).filter(User.username == username).first()
    if not user:
        return jsonify({"error": f"User '{username}' not found"}), 404

    if not user.check_password(password):
        return jsonify({"error": "Bad pair login/password"}), 400

    login_user(user)
    return jsonify(user.to_dict)


@app.route("/logout", methods=["post"])
def logout():
    logout_user()
    return jsonify({"message": "OK"})


@app.route("/add_network", methods=["post"])
@login_required
def add_network():
    '''
        Add new road network
        :param
            name (str) - network name
            file (file) - geojson file (type - FeatureCollection)

        Creates new map (version 1)
    '''

    name = request.form.get("name")
    if not name:
        return jsonify({"error": "Network name required"}), 400
    if Network.name_exists(name):
        return jsonify({"error": f"Network '{name}' already exists!"}), 400

    if not ("file" in request.files):
        return jsonify({"error": "GeoJSON file required"}), 400
    file = request.files.get("file")
    public = request.form.get("public", "") == "true"

    try:
        geojson = json.load(file)
        new_network = Network(name=name, owner_id=current_user.id, public=public)
        new_map = Map(network=new_network)
        new_map.add_geodata(geojson)

        db_session.add(new_network)
        db_session.commit()

    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(new_network.to_dict), 201


def search_network(network_id: int = 0, network_name: str = "") -> (Network, str, int):
    '''
        Search network by id or by name. If both parameters are set, the search is by id
    '''
    if not (network_id or network_name):
        return None, "Network id or network name is required", 400

    if network_id:
        network = db_session.get(Network, network_id)
    else:
        network = db_session.query(Network).filter(Network.name == network_name).first()

    if not network:
        return None, f"Network {f'id={network_id}' if network_id else network_name} not found", 404

    return network, "", 0


@app.route("/update_network", methods=["post"])
@login_required
def update_network():
    '''
        Add new map to existing network
        :param
            id (int) - network id (preferred)
            name (str) - network name
            file (file) - geojson file (type - FeatureCollection)

        The network is searched by id or by name. If both parameters are set, the search is by id
    '''

    if not ("file" in request.files):
        return jsonify({"error": "GeoJSON file required"}), 400
    file = request.files.get("file")

    network, err, err_code = search_network(int(request.form.get("id", 0)), request.form.get("name"))
    if not network:
        return jsonify({"error": err}), err_code

    if network.owner_id != current_user.id:
        return jsonify({"error": "Access denied! Authentication required!"}), 401

    try:
        geojson = json.load(file)

        network.latest_version += 1
        new_map = Map(network=network, version=network.latest_version)
        new_map.add_geodata(geojson)

        db_session.add(new_map)
        db_session.commit()

    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(network.to_dict), 201


@app.route("/network/")
def get_network():
    '''
        Get network info
        :param
            id (int) - network id (preferred)
            name (str) - network name

        The network is searched by id or by name. If both parameters are set, the search is by id
    '''

    network, err, err_code = search_network(int(request.args.get("id", 0)), request.args.get("name"))
    if not network:
        return jsonify({"error": err}), err_code

    if not network.public and (not current_user.is_authenticated or network.owner_id != current_user.id):
        return jsonify({"error": "Access denied! Authentication required!"}), 401

    return jsonify(network.to_dict)


@app.route("/network/edges/")
def get_map():
    '''
        Get defined version of network edges
        :param
            id (int) - network id (preferred)
            name (str) - network name
            version (int, optional) - version number. If not set returns latest version

        The network is searched by id or by name. If both parameters are set, the search is by id
    '''

    network, err, err_code = search_network(int(request.args.get("id", 0)), request.args.get("name"))
    if not network:
        return jsonify({"error": err}), err_code

    if not network.public and (not current_user.is_authenticated or network.owner_id != current_user.id):
        return jsonify({"error": "Access denied! Authentication required!"}), 401

    version = int(request.args.get("version", 0))
    if not version:
        version = network.latest_version
    map_id = network.versions.get(version)
    if not map_id:
        return jsonify({"error": f"Network '{network.name}' version {version} not found"}), 404

    map_obj = db_session.get(Map, map_id)
    if not map_obj:
        return jsonify({"error": f"Map id={map_id} not found"}), 404

    return jsonify(map_obj.to_dict | {"edges": map_obj.edges})
