import logging

from pythonoscquery.osc_query_service import OSCQueryService
from pythonoscquery.shared.osc_access import OSCAccess
from pythonoscquery.shared.osc_address_space import OSCAddressSpace
from pythonoscquery.shared.osc_path_node import OSCPathNode

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # Configure the osc address space and map each method node on the python-osc dispatcher
    osc_address_space = OSCAddressSpace()

    osc_address_space.add_node(
        OSCPathNode(
            "/test/writable/float",
            value=99.0,
            access=OSCAccess.READWRITE_VALUE,
            description="Read/write float value",
        )
    )

    osc_address_space.add_node(
        OSCPathNode(
            "/test/writable/bool",
            value=False,
            access=OSCAccess.READWRITE_VALUE,
            description="Read/write boolean value",
        )
    )

    osc_address_space.add_node(
        OSCPathNode(
            "/test/writable/integer",
            value=12,
            access=OSCAccess.READWRITE_VALUE,
            description="Read/write int value",
        )
    )

    osc_address_space.add_node(
        OSCPathNode(
            "/test/writable/string",
            value="Hello",
            access=OSCAccess.READWRITE_VALUE,
            description="Read/write string value",
        )
    )

    osc_address_space.add_node(
        OSCPathNode(
            "/test/readable/string",
            value="Hello",
            access=OSCAccess.READONLY_VALUE,
            description="Read-only string value",
        )
    )

    osc_ip = "127.0.0.1"
    oscquery_port = 9020
    osc_port = 9021

    oscqs = OSCQueryService(
        osc_address_space, "Test-Service", oscquery_port, osc_port, osc_ip
    )

    logger.debug("Server is up and serving address space %s", osc_address_space)

    input("Press Enter to terminate server...")
