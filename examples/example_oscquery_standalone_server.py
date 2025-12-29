import logging

from pythonoscquery.osc_query_service import OSCQueryService
from pythonoscquery.shared.osc_access import OSCAccess
from pythonoscquery.shared.osc_address_space import OSCAddressSpace
from pythonoscquery.shared.osc_path_node import OSCPathNode

logging.basicConfig()
logger = logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    osc_address_space = OSCAddressSpace()
    osc_address_space.add_node(
        OSCPathNode(
            "/testing/is/cool",
            value=99,
            access=OSCAccess.READONLY_VALUE,
            description="Read only int value",
        )
    )
    osc_address_space.add_node(
        OSCPathNode("/testing/is/good", value=False, access=OSCAccess.READWRITE_VALUE)
    )
    osc_address_space.add_node(
        OSCPathNode(
            "/testing/is/marvelous",
            value=[False, 123, 567.8, "bar"],
            access=OSCAccess.READWRITE_VALUE,
        )
    )
    osc_address_space.add_node(
        OSCPathNode(
            "/testing/is/required",
            value=[False, True],
            access=OSCAccess.READWRITE_VALUE,
        )
    )
    osc_address_space.add_node(
        OSCPathNode(
            "/testing/is/ok",
            value=[1, 5],
            access=OSCAccess.READWRITE_VALUE,
        )
    )
    osc_address_space.add_node(
        OSCPathNode(
            "/write_only",
            value=1,
            access=OSCAccess.WRITEONLY_VALUE,
        )
    )

    oscqs = OSCQueryService(osc_address_space, "Test-Service", 9020, 9020)

    logger.debug("Server is up and serving address space %s", osc_address_space)

    input("Press Enter to terminate server...")
