import logging
import time

from pythonoscquery.osc_query_browser import OSCQueryBrowser
from pythonoscquery.osc_query_client import OSCQueryClient
from pythonoscquery.osc_query_service import OSCQueryService
from pythonoscquery.shared.osc_access import OSCAccess
from pythonoscquery.shared.osc_address_space import OSCAddressSpace
from pythonoscquery.shared.osc_path_node import OSCPathNode

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    osc_address_space = OSCAddressSpace()
    osc_address_space.add_node(
        OSCPathNode(
            "/testing/is/cool",
            value=[99, False, "Hello", 123.0],
            access=OSCAccess.READONLY_VALUE,
        )
    )
    # Start server
    oscqs = OSCQueryService(
        osc_address_space, "Test-Service", 9020, 9020, osc_ip="127.1.1.1"
    )

    time.sleep(1)  # Wait for server being up

    # Start browser
    browser = OSCQueryBrowser()
    time.sleep(1)  # Wait for discovery
    logger.info("Browser is up.")

    for service_info in browser.get_discovered_oscquery():
        client = OSCQueryClient(service_info)

        # Find host info
        host_info = client.get_host_info()
        logger.info(
            f"Found OSC Host: {host_info.name} with ip {host_info.osc_ip}:{host_info.osc_port}"
        )

        # Query a node and print its value
        node = client.query_node("/testing/is/cool")
        if node:
            logger.info(
                f"Node {node.full_path} with description {node.description} (value(s) {node.value} of type(s) {repr(node.type)})"
            )
        else:
            logger.info("Node not found")
