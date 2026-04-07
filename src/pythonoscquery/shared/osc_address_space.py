import logging
import threading
from functools import lru_cache

from .osc_path_node import OSCPathNode

logger = logging.getLogger(__name__)


class OSCAddressSpace:
    """Represents an OSC address space.

    This resembles a tree structure.  The leaves of this tree are the *OSC methods* and the branch nodes are called *OSC containers*.

    Always contains a root node with address "/".
    """

    def __init__(self):
        self._root = OSCPathNode("/", description="root node")
        self._lock = threading.Lock()

    @property
    def lock(self) -> threading.Lock:
        return self._lock

    @property
    def root_node(self) -> OSCPathNode:
        """The root node of the address space."""
        return self._root

    @property
    @lru_cache()
    def number_of_nodes(self) -> int:
        """The number of nodes in the address space. Includes the root node."""
        number_of_nodes = 0
        for _ in self._root:
            number_of_nodes += 1
        return number_of_nodes

    def add_node(self, node: OSCPathNode):
        """Add a node to the address space.
        If the node already exists, it will *not* be replaced.
        If the node address consists of several segments, the segments that might be missing in the space will be added
        automatically.

        Example:
            If the space contains nodes for the address path "/foo/bar" and the node that should be added has a full
            path of "/foo/bar/baz/new_node", the container node "baz" will be added as a child of "/foo/bar/", and then
             the method node "new_node" will be added as a child of "/foo/bar/baz".

        Args:
            node: OSC path node that will be added to the address space
        """
        if self.find_node(node.full_path) is not None:
            logger.warning(
                "Node (%s) already exists, not added again to address space",
                node.full_path,
            )
            return

        path = node.full_path.split("/")

        child_path = ""
        current_node = self._root

        for path_segment in path:
            if path_segment == "":
                continue
            child_path += "/" + path_segment

            if child_path == node.full_path:
                # All nodes up to the destination have been created, the last node is the actual node that is to be added
                with self.lock:
                    current_node.add_child(node)
                break
            else:
                child = self.find_node(child_path)
                if not child:
                    child = OSCPathNode(child_path)

                    with self.lock:
                        current_node.add_child(child)

            current_node = child

        self.__class__.number_of_nodes.fget.cache_clear()

    def find_node(self, address: str) -> OSCPathNode | None:
        """Find a node in the address space.
        Args:
            address: The address of the node to find. Example: "/foo/bar/baz/my_node"
        Returns:
            The node if it exists, otherwise None
        """
        return self.root_node.find_subnode(address)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.number_of_nodes} nodes)"
