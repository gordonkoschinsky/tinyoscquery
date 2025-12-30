from pythonoscquery.shared.osc_access import OSCAccess
from pythonoscquery.shared.osc_address_space import OSCAddressSpace
from pythonoscquery.shared.osc_path_node import OSCPathNode

# Create the address space. This will already have the root node "/" configured.
osc_address_space = OSCAddressSpace()

# Create a method node. A method node has one or more values, but can't have any children (content).
node = OSCPathNode(
    "/foo/bar/baz",
    value=99.0,
    access=OSCAccess.READWRITE_VALUE,
    description="Read/write float value",
)

# Add the node to the address space
# This automatically creates and links the nodes "/foo", "/foo/bar" and adds "/foo/bar/baz"
osc_address_space.add_node(node)

# Nodes in the space can be access by searching for them

container_node_foo = osc_address_space.find_node("/foo")
container_node_foobarbaz = osc_address_space.find_node("/foo/bar/baz")

# The properties of the nodes can be accessed, for example:
print(container_node_foo.is_container)  # True
print(container_node_foo.value)  # None

print(container_node_foobarbaz.is_container)  # False
print(container_node_foobarbaz.value)  # [99.0]
