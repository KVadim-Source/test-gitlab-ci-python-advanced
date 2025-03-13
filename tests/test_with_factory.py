from module_30_ci_linters.homework.hw1.main.models import Client, Parking

from .factories import ClientFactory, ParkingFactory


def test_create_client_with_factory(client, db):
    initial_clients_count = Client.query.count()
    client_data = ClientFactory.build()

    response = client.post(
        "/clients",
        json={
            "name": client_data.name,
            "surname": client_data.surname,
            "credit_card": client_data.credit_card,
            "car_number": client_data.car_number,
        },
    )

    if client_data.credit_card:
        assert response.status_code == 201
        assert Client.query.count() == initial_clients_count + 1

        new_client = Client.query.order_by(Client.id.desc()).first()
        assert new_client.name == client_data.name
        assert new_client.surname == client_data.surname
        assert new_client.credit_card == client_data.credit_card
        assert new_client.car_number == client_data.car_number
    else:
        assert response.status_code == 400


def test_create_parking_with_factory(client, db):
    initial_parkings_count = Parking.query.count()
    parking_data = ParkingFactory.build()

    response = client.post(
        "/parkings",
        json={
            "address": parking_data.address,
            "opened": parking_data.opened,
            "count_places": parking_data.count_places,
            "count_available_places": parking_data.count_available_places,
        },
    )

    assert response.status_code == 201
    assert Parking.query.count() == initial_parkings_count + 1

    new_parking = Parking.query.order_by(Parking.id.desc()).first()
    assert new_parking.address == parking_data.address
    assert new_parking.opened == parking_data.opened
    assert new_parking.count_places == parking_data.count_places
    assert new_parking.count_available_places == (
        parking_data.count_available_places
    )
