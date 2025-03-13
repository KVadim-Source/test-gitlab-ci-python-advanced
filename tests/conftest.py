from typing import Generator, Tuple

import pytest
from flask import Flask
from flask.testing import FlaskClient as TestClient
from flask_sqlalchemy import SQLAlchemy
from module_30_ci_linters.homework.hw1.main.app import app as main_app
from module_30_ci_linters.homework.hw1.main.extensions import db as _db
from module_30_ci_linters.homework.hw1.main.models import (
    Client,
    ClientParking,
    Parking,
)


@pytest.fixture
def app() -> Generator[Flask, None, None]:
    _app = main_app
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    with _app.app_context():
        _db.create_all()
    yield _app
    with _app.app_context():
        _db.drop_all()


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    with app.test_client() as client:
        yield client


@pytest.fixture
def db(app) -> Generator[SQLAlchemy, None, None]:
    with app.app_context():
        yield _db


@pytest.fixture
def test_client_parking(app) -> Generator[Tuple[int, int], None, None]:
    with app.app_context():
        client = Client(
            name="John",
            surname="Doe",
            credit_card="1234",
            car_number="ABC123",
        )
        parking = Parking(
            address="Main St",
            opened=True,
            count_places=10,
            count_available_places=10,
        )

        _db.session.add(client)
        _db.session.add(parking)
        _db.session.commit()

        yield client.id, parking.id

        _db.session.query(Parking).delete()
        _db.session.query(Client).delete()
        _db.session.commit()


@pytest.mark.parametrize("route", ["/clients", "/clients/1"])
def test_get_routes(
    client: TestClient, test_client_parking: tuple[int, int], route: str
) -> None:
    response = client.get(route)
    assert response.status_code == 200


def test_create_client(client: TestClient) -> None:
    client_data = {
        "name": "John",
        "surname": "Doe",
        "credit_card": "1234",
        "car_number": "ABC123",
    }
    response = client.post("/clients", json=client_data)
    assert response.status_code == 201


def test_create_client_without_required_fields(client: TestClient) -> None:
    client_data = {"name": "John"}
    response = client.post("/clients", json=client_data)
    assert response.status_code != 201


def test_create_parking(client: TestClient) -> None:
    parking_data = {
        "address": "Main St",
        "opened": True,
        "count_places": 10,
        "count_available_places": 10,
    }
    response = client.post("/parkings", json=parking_data)
    assert response.status_code == 201


@pytest.mark.parking
def test_parking_entry(
    client: TestClient, test_client_parking: tuple[int, int]
) -> None:
    client_id, parking_id = test_client_parking

    entry_data = {"client_id": client_id, "parking_id": parking_id}
    response = client.post("/client_parkings", json=entry_data)
    assert response.status_code == 200

    parking = Parking.query.get(parking_id)
    assert parking.count_available_places == 9

    filter_params = {"client_id": client_id, "parking_id": parking_id}
    client_parking_entry = ClientParking.query.filter_by(
        **filter_params
    ).first()
    assert client_parking_entry is not None
    assert client_parking_entry.time_in is not None


@pytest.mark.parking
def test_parking_exit(
    client: TestClient, test_client_parking: tuple[int, int]
) -> None:
    client_id, parking_id = test_client_parking

    entry_data = {"client_id": client_id, "parking_id": parking_id}
    client.post("/client_parkings", json=entry_data)

    exit_data = {"client_id": client_id, "parking_id": parking_id}
    response = client.delete("/client_parkings", json=exit_data)
    assert response.status_code == 200

    parking = Parking.query.get(parking_id)
    assert parking.count_available_places == 10

    filter_params = {"client_id": client_id, "parking_id": parking_id}
    client_parking_entry = ClientParking.query.filter_by(
        **filter_params
    ).first()

    assert client_parking_entry.time_out is not None
    assert client_parking_entry.time_out > client_parking_entry.time_in

    time_diff = client_parking_entry.time_out - client_parking_entry.time_in
    assert time_diff.total_seconds() > 0


@pytest.mark.parking
def test_parking_entry_closed(
    client: TestClient, test_client_parking: tuple[int, int]
) -> None:
    client_id, parking_id = test_client_parking

    parking = Parking.query.get(parking_id)
    parking.opened = False
    _db.session.commit()

    entry_data = {"client_id": client_id, "parking_id": parking_id}
    response = client.post("/client_parkings", json=entry_data)
    assert response.status_code != 200


@pytest.mark.parking
def test_parking_exit_without_entry(
    client: TestClient, test_client_parking: tuple[int, int]
) -> None:
    client_id, parking_id = test_client_parking

    exit_data = {"client_id": client_id, "parking_id": parking_id}
    response = client.delete("/client_parkings", json=exit_data)

    assert response.status_code != 200


@pytest.mark.parking
def test_parking_exit_payment(
    client: TestClient, test_client_parking: tuple[int, int]
) -> None:
    client_id, parking_id = test_client_parking

    entry_data = {"client_id": client_id, "parking_id": parking_id}
    client.post("/client_parkings", json=entry_data)

    client_obj = Client.query.get(client_id)
    assert client_obj.credit_card is not None

    exit_data = {"client_id": client_id, "parking_id": parking_id}
    response = client.delete("/client_parkings", json=exit_data)
    assert response.status_code == 200
