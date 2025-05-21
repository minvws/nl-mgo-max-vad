# pylint:disable=too-few-public-methods
from faker import Faker
import pytest


def pytest_addoption(parser, pluginmanager):
    parser.addoption(
        "--docker",
        action="store_true",
        default=False,
        help="Flags whether pytest is ran inside a docker container",
    )


@pytest.fixture(scope="session")
def inside_docker(pytestconfig):
    return pytestconfig.getoption("docker")


@pytest.fixture()
def faker() -> Faker:
    return Faker()
