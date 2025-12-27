import logging

from tinyoscquery.osc_query_service import OSCQueryService
from tinyoscquery.shared.osc_access import OSCAccess
from tinyoscquery.shared.osc_namespace import OSCNamespace
from tinyoscquery.shared.osc_path_node import OSCPathNode

if __name__ == "__main__":
    osc_namespace = OSCNamespace()
    osc_namespace.add_node(
        OSCPathNode(
            "/testing/is/cool",
            value=99,
            access=OSCAccess.READONLY_VALUE,
            description="Read only int value",
        )
    )
    osc_namespace.add_node(
        OSCPathNode("/testing/is/good", value=False, access=OSCAccess.READWRITE_VALUE)
    )
    osc_namespace.add_node(
        OSCPathNode(
            "/testing/is/marvelous",
            value=[False, 123, 567.8, "bar"],
            access=OSCAccess.READWRITE_VALUE,
        )
    )
    osc_namespace.add_node(
        OSCPathNode(
            "/testing/is/required",
            value=[False, True],
            access=OSCAccess.READWRITE_VALUE,
        )
    )
    osc_namespace.add_node(
        OSCPathNode(
            "/testing/is/ok",
            value=[1, 5],
            access=OSCAccess.READWRITE_VALUE,
        )
    )

    oscqs = OSCQueryService(osc_namespace, "Test-Service", 9020, 9020)

    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Server is up and serving namespace %s", osc_namespace)

    input("Press Enter to terminate server...")
