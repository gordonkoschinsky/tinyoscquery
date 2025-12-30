# python-oscquery

An OSCQuery library for python.

![Python Version >=3.10](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fgordonkoschinsky%2Fpython-oscquery%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)
![Tests](https://github.com/gordonkoschinsky/python-oscquery/actions/workflows/python-package.yml/badge.svg)

[OSCQuery](https://github.com/Vidvox/OSCQueryProposal) is a protocol that allows
an [Open Sound Control (OSC)](https://opensoundcontrol.stanford.edu) server to
announce its presence and capabilities over the network.
Clients can discover the server via [zeroconf](https://en.wikipedia.org/wiki/Zero-configuration_networking) and query
the address space via HTTP.

This library provides an integration with  [python-osc](https://pypi.org/project/python-osc/).
The namespace that is configured to be announced via the OSCQuery server is also used to automatically
type-check incoming OSC messages. For this purpose, a wrapper around a python-osc handler callback function
is provided.

## Features

- HTTP server to serve the OSC host information and the OSC address space
- Server advertised via Zeroconf/Bonjour
- Browser to discover other advertised servers on the network
- HTTP client to query other servers for their host information and address space
- Wrapper for python-osc callback that allows for validation of OSC arguments
- Shared OSC address space, used for serving OSCQuery and validation of incoming python-osc messages

## Status

### Server

The [core functionality](https://github.com/Vidvox/OSCQueryProposal?tab=readme-ov-file#core-functionality) (according to
the specification) is implemented.
Some [optional attributes](https://github.com/Vidvox/OSCQueryProposal?tab=readme-ov-file#optional-attributes) like
ACCESS, VALUE and DESCRIPTION are also implemented. However, lists (or other python
iterables) are not supported as value types.

Completely missing is
the [websocket communication](https://github.com/Vidvox/OSCQueryProposal?tab=readme-ov-file#optional-bi-directional-communication).
So no "listening" is possible.

### Client / Browser

Discovery of other OSCQuery servers on the network and querying of the OSC address space is implemented.

## Installation

```bash
    $ python -m pip install python-oscquery
```

## Usage

Please also have a look at the 'examples' directory in this repository.

### Configuring the OSC address space

The OSC address space must be configured before it can be advertised and used for validation of incoming messages.
The address space consists of individual nodes. Those nodes form a tree. The branches of the tree are called
"OSC containers", the leaves are "OSC methods".

When adding a node to the address space, its full OSC path (e.g. "/foo/bar/baz") is used to determine its relation to
other nodes in the tree. Missing nodes between the existing structure and the node that is to be added are created
automatically by python-oscquery.

```python

from pythonoscquery.shared.osc_address_space import OSCAddressSpace
from pythonoscquery.shared.osc_path_node import OSCPathNode
from pythonoscquery.shared.osc_access import OSCAccess

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
```

### Advertising and running an OSCQuery service

Once the address space is configured, it can be served to interested clients.

```python
from pythonoscquery.osc_query_service import OSCQueryService

osc_ip = "127.0.0.1"
oscquery_port = 9020
osc_port = 9021

# Create the server. Serving via HTTP and zeroconf advertisement starts automatically.
oscqs = OSCQueryService(
    osc_address_space, "Test-Service", oscquery_port, osc_port, osc_ip
)

# The server runs in a daemon thread, so program flow can continue
print("Server is up and serving address space %s", osc_address_space)

input("Press Enter to terminate server...")
```

The server can now be queried. For example, with [Chataigne](https://benjamin.kuperberg.fr/chataigne/en):

![Screenshot of Chataigne inspector for the OSQQuery module, showing that the values from the address space have been fetched](/docs/images/chataigne1.png)

### Discovering other OSCQuery services

python-oscquery also provides a browser to detect advertised OSCQuery servers on the network.

```python
import time
from pythonoscquery.osc_query_browser import OSCQueryBrowser

browser = OSCQueryBrowser()
time.sleep(1)  # Wait for discovery

for service_info in browser.get_discovered_oscquery():
    print(service_info)
```

### Querying other OSCQuery services

The discovered service information can be used to create a client instance:

```python
from pythonoscquery.osc_query_client import OSCQueryClient

for service_info in browser.get_discovered_oscquery():
    client = OSCQueryClient(service_info)

```

The client can get the host information from the server:

```python  
    # Find host info
host_info = client.get_host_info()
print(
    f"Found OSC Host: {host_info.name} with ip {host_info.osc_ip}:{host_info.osc_port}"
)


```

It also can query the server for nodes in its address space:

```python  
# Query a node and print its value
node = client.query_node("/testing/is/cool")
if node:
    print(
        f"Node {node.full_path} with description {node.description} (value(s) {node.value} of type(s) {repr(node.type)})"
    )
else:
    print("Node not found")
```

If a node is found, python-oscquery tries to instantiate an OSCPathNode from the returned JSON data. This might fail
if the OSC server is not completely following the spec.

### Using the address space to validate incoming messages with python-osc

The address space can be used to validate the arguments of incoming OSC messages. python-oscquery provides a wrapper
around callbacks that can be mapped on a python-osc dispatcher.
When this wrapped callback is called, it validates the received number of values and their types against the configured
node. If the types do not match, the actual callback function is not called and the message is dropped.

For convenience, a mapping function is provided that not only creates the wrapped callback, but also registers the node
in the address space and maps it on the python-osc dispatcher.

```python
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

from pythonoscquery.pythonosc_callback_wrapper import map_node
from pythonoscquery.osc_query_service import OSCQueryService
from pythonoscquery.shared.osc_access import OSCAccess
from pythonoscquery.shared.osc_address_space import OSCAddressSpace
from pythonoscquery.shared.osc_path_node import OSCPathNode


def generic_handler(address, *args, **kwargs):
    """Callback function that acts as a handler for python-osc"""
    print(f"Generic handler callback function called with address {address} and args {args}, kwargs {kwargs}")


# Instantiate the python-osc dispatcher
dispatcher = Dispatcher()

# Configure the osc address space and map each method node on the python-osc dispatcher
osc_address_space = OSCAddressSpace()

# Configure a method node
node = OSCPathNode(
    "/test/writable/float",
    value=99.0,
    access=OSCAccess.READWRITE_VALUE,
    description="Read/write float value",
)
# Create a wrapper around the callback, add the node to the address space and map it on the python-osc dispatcher
map_node(node, dispatcher, generic_handler, address_space=osc_address_space)

osc_ip = "127.0.0.1"
oscquery_port = 9020
osc_port = 9021

# Start python-oscquery server
oscqs = OSCQueryService(osc_address_space, "Test-Service", oscquery_port, osc_port, osc_ip)

print(
    "OSCQuery Server is up and serving address space %s", osc_address_space
)

# Start python-osc server
server = BlockingOSCUDPServer((osc_ip, osc_port), dispatcher)
print("OSC Server is up.")

server.serve_forever()
```

## Project to-do

- [ ] Make OSCQueryClient not depended on service_info, but manually configurable
- [ ] Think about thread-safety of the HTTP-server
- [ ] Add a mechanism to update OSC nodes with new values
- [ ] Add the RANGE attribute and validate messages against it
- [ ] Add websocket communication as per spec
- [ ] Add ability to remove nodes from the address space
- [ ] Add more documentation