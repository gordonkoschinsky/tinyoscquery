import time

from tinyoscquery.osc_query_service import OSCQueryService
from tinyoscquery.shared.osc_access import OSCAccess
from tinyoscquery.shared.osc_path_node import OSCPathNode

if __name__ == "__main__":
    oscqs = OSCQueryService("Test-Service", 9020, 9020)
    print(oscqs.root_node)

    oscqs.add_node(
        OSCPathNode("/testing/is/cool", value=False, access=OSCAccess.READWRITE_VALUE)
    )

    print(oscqs.root_node)

    while True:
        time.sleep(1)
