import logging

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

from pythonoscquery.osc_query_service import OSCQueryService
from pythonoscquery.pythonosc_callback_wrapper import map_node
from pythonoscquery.shared.osc_access import OSCAccess
from pythonoscquery.shared.osc_address_space import OSCAddressSpace
from pythonoscquery.shared.osc_path_node import OSCPathNode

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


def generic_handler(address, *args, **kwargs):
    logger.debug(
        f"Generic handler callback function called with address {address} and args {args}, kwargs {kwargs}"
    )


if __name__ == "__main__":
    # Instantiate the python-osc dispatcher
    dispatcher = Dispatcher()

    # Configure the osc address space and map each method node on the python-osc dispatcher
    osc_address_space = OSCAddressSpace()

    node = OSCPathNode(
        "/test/writable/float",
        value=99.0,
        access=OSCAccess.READWRITE_VALUE,
        description="Read/write float value",
    )
    map_node(node, dispatcher, generic_handler, address_space=osc_address_space)

    node = OSCPathNode(
        "/test/writable/bool",
        value=False,
        access=OSCAccess.READWRITE_VALUE,
        description="Read/write boolean value",
    )
    map_node(node, dispatcher, generic_handler, address_space=osc_address_space)

    node = OSCPathNode(
        "/test/writable/integer",
        value=12,
        access=OSCAccess.READWRITE_VALUE,
        description="Read/write int value",
    )
    map_node(node, dispatcher, generic_handler, address_space=osc_address_space)

    node = OSCPathNode(
        "/test/writable/string",
        value="Hello",
        access=OSCAccess.READWRITE_VALUE,
        description="Read/write string value",
    )
    map_node(node, dispatcher, generic_handler, address_space=osc_address_space)

    node = OSCPathNode(
        "/test/readable/string",
        value="Hello",
        access=OSCAccess.READONLY_VALUE,
        description="Read-only string value",
    )
    map_node(node, dispatcher, generic_handler, address_space=osc_address_space)

    osc_ip = "127.0.0.1"
    oscquery_port = 9020
    osc_port = 9021

    oscqs = OSCQueryService(
        osc_address_space, "Test-Service", oscquery_port, osc_port, osc_ip
    )
    oscqs.start()

    logger.debug(
        "OSCQuery Server is up and serving address space %s", osc_address_space
    )

    server = BlockingOSCUDPServer((osc_ip, osc_port), dispatcher)
    logger.debug("OSC Server is up.")

    server.serve_forever()
