import time

from tinyoscquery.osc_query_browser import OSCQueryBrowser
from tinyoscquery.osc_query_client import OSCQueryClient
from tinyoscquery.osc_query_service import OSCQueryService
from tinyoscquery.shared.osc_access import OSCAccess
from tinyoscquery.shared.osc_path_node import OSCPathNode

if __name__ == "__main__":
    # Start server
    oscqs = OSCQueryService("Test-Service", 9020, 9020, osc_ip="127.1.1.1")
    print(oscqs.root_node)

    oscqs.add_node(
        OSCPathNode("/testing/is/cool", value=99, access=OSCAccess.READONLY_VALUE)
    )
    time.sleep(1)  # Wait for server being up

    # Start browser
    browser = OSCQueryBrowser()
    time.sleep(2)  # Wait for discovery
    print("Browser is up.")

    for service_info in browser.get_discovered_oscquery():
        client = OSCQueryClient(service_info)

        # Find host info
        host_info = client.get_host_info()
        print(
            f"Found OSC Host: {host_info.name} with ip {host_info.osc_ip}:{host_info.osc_port}"
        )

        # Query a node and print its value
        node = client.query_node("/testing/is/cool")
        if node:
            print(
                f"Node {node.full_path} with description {node.description} (value {node.value} of type {node.type_})"
            )
        else:
            print("Node not found")
