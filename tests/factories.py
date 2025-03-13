import factory
from faker import Faker
from module_30_ci_linters.homework.hw1.main.extensions import db
from module_30_ci_linters.homework.hw1.main.models import Client, Parking

fake = Faker()


def generate_credit_card():
    return fake.credit_card_number() if fake.random_int(min=0, max=1) else None


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = db.session

    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    credit_card = factory.LazyAttribute(lambda x: generate_credit_card())
    car_number = factory.Faker("license_plate")


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Parking
        sqlalchemy_session = db.session

    address = factory.Faker("address")
    opened = factory.Faker("boolean")
    count_places = factory.Faker("random_int", min=1, max=100)
    count_available_places = factory.LazyAttribute(lambda o: o.count_places)
