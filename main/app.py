from datetime import datetime

import sqlalchemy
from flask import Flask, Response, jsonify, request

from .extensions import db
from .models import Client, ClientParking, Parking

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///prod.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/clients", methods=["GET"])
def get_clients() -> Response:
    clients = Client.query.all()
    return jsonify([client.to_dict() for client in clients])


@app.route("/clients/<int:client_id>", methods=["GET"])
def get_client(client_id: int) -> tuple[Response, int] | Response:
    client = Client.query.get(client_id)
    return (
        jsonify(client.to_dict())
        if client
        else (jsonify({"error": "Client not found"}), 404)
    )


@app.route("/clients", methods=["POST"])
def create_client() -> tuple[Response, int]:
    data = request.json
    required_fields = ["name", "surname", "credit_card", "car_number"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    if not all(isinstance(data[field], str) for field in ["name", "surname"]):
        return jsonify({"error": "Name/surname must be strings"}), 400

    if not all(
        isinstance(data[field], str) for field in ["credit_card", "car_number"]
    ):
        return jsonify({"error": "Card/car number must be strings"}), 400

    if not data["credit_card"]:
        return jsonify({"error": "Credit card required"}), 400

    client = Client(
        name=data["name"],
        surname=data["surname"],
        credit_card=data["credit_card"],
        car_number=data["car_number"],
    )

    try:
        db.session.add(client)
        db.session.commit()
        return jsonify({"message": "Client created"}), 201
    except sqlalchemy.exc.SQLAlchemyError as e:
        db.session.rollback()
        error_message = f"Client creation failed: {e}"
        return jsonify({"error": error_message}), 500


@app.route("/parkings", methods=["POST"])
def create_parking() -> tuple[Response, int]:
    data = request.json
    required_fields = [
        "address",
        "opened",
        "count_places",
        "count_available_places",
    ]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    if not isinstance(data["address"], str):
        return jsonify({"error": "Address must be string"}), 400

    if not isinstance(data["opened"], bool):
        return jsonify({"error": "Opened must be boolean"}), 400

    if not all(
        isinstance(data[f], int)
        for f in ["count_places", "count_available_places"]
    ):
        return jsonify({"error": "Places counts must be integers"}), 400

    if (
        data["count_places"] <= 0
        or data["count_available_places"] < 0
        or data["count_available_places"] > data["count_places"]
    ):
        return jsonify({"error": "Invalid places count"}), 400

    parking = Parking(
        address=data["address"],
        opened=data["opened"],
        count_places=data["count_places"],
        count_available_places=data["count_available_places"],
    )

    try:
        db.session.add(parking)
        db.session.commit()
        return jsonify({"message": "Parking created"}), 201
    except sqlalchemy.exc.SQLAlchemyError as e:
        db.session.rollback()
        error_message = f"Parking creation failed: {e}"
        return jsonify({"error": error_message}), 500


@app.route("/client_parkings", methods=["POST"])
def client_park_entry() -> tuple[Response, int]:
    data = request.json
    client_id = data["client_id"]
    parking_id = data["parking_id"]

    client = Client.query.get(client_id)
    parking = Parking.query.get(parking_id)

    if not client or not parking:
        return jsonify({"error": "Client/parking not found"}), 404

    if not parking.opened or parking.count_available_places == 0:
        return jsonify({"error": "Parking closed/full"}), 400

    try:
        client_parking = ClientParking(
            client_id=client_id, parking_id=parking_id, time_in=datetime.now()
        )
        db.session.add(client_parking)
        parking.count_available_places -= 1
        db.session.commit()
        return jsonify(client_parking.to_dict())
    except sqlalchemy.exc.SQLAlchemyError as e:
        db.session.rollback()
        error_message = f"Parking entry failed: {e}"
        return jsonify({"error": error_message}), 500


@app.route("/client_parkings", methods=["DELETE"])
def client_park_exit() -> tuple[Response, int]:
    data = request.json
    client_id = data["client_id"]
    parking_id = data["parking_id"]

    client = Client.query.get(client_id)
    parking = Parking.query.get(parking_id)
    client_parking = ClientParking.query.filter_by(
        client_id=client_id, parking_id=parking_id
    ).first()

    if not client or not parking or not client_parking:
        return jsonify({"error": "Client/parking/entry not found"}), 404

    if not client.credit_card:
        return jsonify({"error": "No credit card"}), 400

    try:
        client_parking.time_out = datetime.now()
        parking.count_available_places += 1
        db.session.commit()
        return jsonify(client_parking.to_dict())
    except sqlalchemy.exc.SQLAlchemyError as e:
        db.session.rollback()
        error_message = f"Exit update failed: {e}"
        return jsonify({"error": error_message}), 500
