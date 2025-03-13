from typing import Any

import factory
from factory import Faker as FactoryFaker
from faker import Faker
from module_30_ci_linters.homework.hw1.main.extensions import db
from module_30_ci_linters.homework.hw1.main.models import Client, Parking

fake = Faker()


def generate_credit_card() -> str | None:
    return fake.credit_card_number() if fake.random_int(min=0, max=1) else None


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = db.session

    name = FactoryFaker("first_name")
    surname = FactoryFaker("last_name")
    credit_card: Any = factory.LazyAttribute(lambda x: generate_credit_card())
    car_number = FactoryFaker("license_plate")


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Parking
        sqlalchemy_session = db.session

    address = FactoryFaker("address")
    opened = FactoryFaker("boolean")
    count_places = FactoryFaker("random_int", min=1, max=100)
    count_available_places: Any = factory.LazyAttribute(
        lambda o: o.count_places
    )
