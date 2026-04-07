from ipaddress import IPv4Address

import pytest
import urllib3

from pythonoscquery.osc_query_service import OSCQueryService
from pythonoscquery.shared.osc_access import OSCAccess
from pythonoscquery.shared.osc_address_space import OSCAddressSpace
from pythonoscquery.shared.osc_path_node import OSCPathNode


@pytest.fixture
def address_space():
    return OSCAddressSpace()


@pytest.fixture
def server(address_space):
    return OSCQueryService(
        address_space, "Unit test server", 8080, 8080, IPv4Address("127.0.0.1")
    )


@pytest.fixture
def simple_node():
    return OSCPathNode(
        "/test", value=99, access=OSCAccess.READONLY_VALUE, description="Test node"
    )


@pytest.fixture
def write_only_node():
    return OSCPathNode(
        "/write_only",
        value=123,
        access=OSCAccess.WRITEONLY_VALUE,
        description="Write only node",
    )


class TestOSCQueryService:
    def test_query(self, server, address_space, simple_node, write_only_node):
        """I'm quite sure that this is not a good way to test the server, since it starts the actual server.
        I don't have the time at the moment to read up / think about a better way."""
        # Arrange
        server.start()
        address_space.add_node(simple_node)
        # Act 1
        response = urllib3.request("GET", "http://127.0.0.1:8080/?HOST_INFO")
        json = response.json()
        status = response.status
        # Assert 1
        assert status == 200
        assert json["OSC_IP"] == "127.0.0.1"

        # Act 2
        response = urllib3.request("GET", "http://127.0.0.1:8080/")
        json = response.json()
        status = response.status
        # Assert 2
        assert status == 200
        assert json == {
            "ACCESS": 0,
            "CONTENTS": {
                "test": {
                    "ACCESS": 1,
                    "DESCRIPTION": "Test node",
                    "FULL_PATH": "/test",
                    "TYPE": "i",
                    "VALUE": [99],
                }
            },
            "DESCRIPTION": "root node",
            "FULL_PATH": "/",
        }

        # Act 3
        response = urllib3.request("GET", "http://127.0.0.1:8080/some_bogus_adress")
        status = response.status
        # Assert 3
        assert status == 404

        # Act 4
        response = urllib3.request("GET", "http://127.0.0.1:8080/test")
        json = response.json()
        status = response.status
        # Assert 4
        assert status == 200
        assert json == {
            "ACCESS": 1,
            "DESCRIPTION": "Test node",
            "FULL_PATH": "/test",
            "TYPE": "i",
            "VALUE": [99],
        }

        # Act 4
        response = urllib3.request("GET", "http://127.0.0.1:8080/test?VALUE")
        json = response.json()
        status = response.status
        # Assert 4
        assert status == 200
        assert json == {"VALUE": [99]}

        # Act 5
        response = urllib3.request("GET", "http://127.0.0.1:8080/test?BOGUSATTRIBUTE")
        status = response.status
        # Assert 5
        assert status == 400

        # Arrange 6 - Adding a node to  the address space is instantly reflected
        address_space.add_node(write_only_node)
        # Act 6
        response = urllib3.request("GET", "http://127.0.0.1:8080/")
        status = response.status
        json = response.json()
        # Assert 6
        assert status == 200
        assert json == {
            "ACCESS": 0,
            "CONTENTS": {
                "test": {
                    "ACCESS": 1,
                    "DESCRIPTION": "Test node",
                    "FULL_PATH": "/test",
                    "TYPE": "i",
                    "VALUE": [99],
                },
                "write_only": {
                    "ACCESS": 2,
                    "DESCRIPTION": "Write only node",
                    "FULL_PATH": "/write_only",
                    "TYPE": "i",
                    "VALUE": [123],
                },
            },
            "DESCRIPTION": "root node",
            "FULL_PATH": "/",
        }

        # Act 7
        response = urllib3.request(
            "GET", "http://127.0.0.1:8080/write_only?VALUE", timeout=30.0
        )
        status = response.status
        # Assert 7
        assert status == 204
