import pytest
from app.main import create_app
from app.source import bundle
from app.workflow import steps


@pytest.fixture
def desk(tmp_path):
    return create_app(tmp_path/'library.sqlite')


@pytest.fixture
def client(desk):
    return desk.test_client()


@pytest.fixture(scope='session')
def dirty():
    return steps(bundle('dirty'))
