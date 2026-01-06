import builtins
import json
import logging
from collections.abc import Iterable
from json import JSONEncoder
from typing import Any, TypeVar, Union

from .osc_access import OSCAccess
from .osc_spec import disallowed_path_chars, is_valid_path
from .oscquery_spec import OSCQueryAttribute

logger = logging.getLogger(__name__)


class OSCNodeEncoder(JSONEncoder):
    def __init__(self, attribute_filter: OSCQueryAttribute | None = None, **kwargs):
        super(OSCNodeEncoder, self).__init__()
        self.attribute_filter = attribute_filter

    def default(self, o):
        if isinstance(o, OSCPathNode):
            obj_dict = {}
            o: OSCPathNode
            for k, v in o.attributes.items():
                if v is None:
                    continue

                if self.attribute_filter is not None and self.attribute_filter != k:
                    continue

                match k:
                    case OSCQueryAttribute.CONTENTS:
                        if len(v) < 1:
                            continue
                        obj_dict["CONTENTS"] = {}
                        sub_node: OSCPathNode
                        for sub_node in v:
                            obj_dict["CONTENTS"][
                                sub_node.attributes[OSCQueryAttribute.FULL_PATH].split(
                                    "/"
                                )[-1]
                            ] = sub_node
                    case OSCQueryAttribute.TYPE:
                        obj_dict["TYPE"] = python_type_list_to_osc_type(v)
                    case _:
                        obj_dict[k.name.upper()] = v

            return obj_dict

        return json.JSONEncoder.default(self, o)  # pragma: no cover


T = TypeVar("T", bound=int | float | bool | str)


class OSCPathNode:
    """A node in the OSC address space tree."""

    @classmethod
    def from_json(cls, json_data: dict[str, Any]) -> "OSCPathNode":
        """Factory method to create an instance of OSCPathNode from JSON data."""
        contents = None
        if "CONTENTS" in json_data:
            sub_nodes = []
            for subNode in json_data["CONTENTS"]:
                sub_nodes.append(OSCPathNode.from_json(json_data["CONTENTS"][subNode]))
            contents = sub_nodes

        # This *should* be required but some implementations don't have it...
        full_path = None
        if "FULL_PATH" in json_data:
            full_path = json_data["FULL_PATH"]

        description = None
        if "DESCRIPTION" in json_data:
            description = json_data["DESCRIPTION"]

        access = None
        if "ACCESS" in json_data:
            access = OSCAccess(json_data["ACCESS"])

        value = None
        if "VALUE" in json_data:
            value = []
            if not isinstance(json_data["VALUE"], list):
                raise TypeError("OSCQuery JSON Value is not List / Array? Out-of-spec?")

            for v in json_data["VALUE"]:
                value.append(v)

        return cls(
            full_path=full_path,
            access=access,
            description=description,
            value=value,
            contents=contents,
        )

    def __init__(
        self,
        full_path: str,
        access: OSCAccess = OSCAccess.NO_VALUE,
        value: Union[T, list[T]] = None,
        description: str = None,
        contents: list["OSCPathNode"] = None,
    ):
        """
        Args:
            full_path: The OSC address path, e.g. "/test/foo/bar"
            access: The access mode of the node
            value: A list of initial values for the node. The argument types are derived from those values
                If the actual value does not matter, a placeholder with the correct type can be used instead
            description: A textual description of the node's purpose
            contents: The child nodes of this node. Don't use this directly, but  add new node via the AddressSpace.
                This parameter exists for instantiation via json data.
        """
        if not is_valid_path(full_path):
            raise ValueError(
                "Invalid path: Path must start with a single trailing forward slash (/)."
                "Path must not contain any of the following characters: {}."
                "Path must not have empty nodes (like /test//path). Path must not have trailing forward slashes. ".format(
                    disallowed_path_chars
                )
            )

        if contents and value:
            raise ValueError(
                "A node can either have child nodes (for OSC containers) or values (for OSC methods), but not both."
            )

        self._attributes: dict[OSCQueryAttribute, Any] = {}

        self._attributes[OSCQueryAttribute.FULL_PATH] = full_path

        self._attributes[OSCQueryAttribute.CONTENTS]: list["OSCPathNode"] = contents

        # Ensure that value is an iterable
        if not isinstance(value, Iterable) or isinstance(value, str):
            value = [value] if value is not None else []

        if not value and access is not OSCAccess.NO_VALUE:
            raise ValueError(
                f"No value(s) given, access must be {OSCAccess.NO_VALUE.name} for container nodes."
            )

        if value and access is OSCAccess.NO_VALUE:
            raise ValueError(
                f"Value(s) given, access must not be {OSCAccess.NO_VALUE.name} for method nodes."
            )

        self._attributes[OSCQueryAttribute.VALUE] = value if value else None

        types = []
        if value:
            for v in self._attributes[OSCQueryAttribute.VALUE]:
                types.append(type(v))

        self._attributes[OSCQueryAttribute.TYPE] = types if value else None

        self._attributes[OSCQueryAttribute.ACCESS] = access

        self._attributes[OSCQueryAttribute.DESCRIPTION] = description

    @property
    def attributes(self) -> dict[OSCQueryAttribute, Any]:
        return self._attributes

    @property
    def full_path(self) -> str:
        return self._attributes[OSCQueryAttribute.FULL_PATH]

    @property
    def contents(self) -> list["OSCPathNode"]:
        return self._attributes[OSCQueryAttribute.CONTENTS]

    @property
    def description(self) -> str:
        return self._attributes[OSCQueryAttribute.DESCRIPTION]

    @property
    def access(self) -> OSCAccess:
        return self._attributes[OSCQueryAttribute.ACCESS]

    @property
    def value(self) -> Any:
        return self._attributes[OSCQueryAttribute.VALUE]

    @property
    def type(self) -> Any:
        return self._attributes[OSCQueryAttribute.TYPE]

    @property
    def is_container(self) -> bool:
        """Returns True if this node is an OSC container, False otherwise.
        An OSC container is a node that has child nodes, aka a branch in the address space tree.
        To enable gradual build-up of the address tree, nodes are also considered to be containers if they have no
        values configured.
        """
        if self.contents or not self.value:
            return True
        return False

    def add_child(self, child: "OSCPathNode"):
        """Add a child node to this node.
        *This should not be called directly, but implicitly from OSCAddressSpace.add_node()*"""
        if not self.is_container:
            raise ValueError(
                f"Can only add child nodes to an OSC container. Node '{self.full_path}' is not a container"
            )
        if self.contents is None:
            self._attributes[OSCQueryAttribute.CONTENTS] = []
        self.contents.append(child)

    def find_subnode(self, full_path: str) -> "OSCPathNode | None":
        """Recursively find a node with the given full path.
        Args:
            full_path: Address of the node to find, e.g. "/test/bar"
        Returns:
            The found node or None if not found
        """
        if self.full_path == full_path:
            return self

        if not self.contents:
            return None

        for sub_node in self.contents:
            found_node = sub_node.find_subnode(full_path)
            if found_node:
                return found_node

        return None

    def to_json(self, attribute: OSCQueryAttribute | None = None) -> str:
        """Convert the attributes of this node to json.

        Args:
            attribute: OSC query attribute, e.g. "OSCQueryAttribute.VALUE". If given, only this attribute will be rendered.
        Returns:
            The json string
        """
        return json.dumps(self, cls=OSCNodeEncoder, attribute_filter=attribute)

    def validate_values(self, values: list[T]) -> list[T]:
        """Validate the given value types against the specified types of this node.

        Sanitizes some values:

        - If the client sent 0 or 1 as a substitute for a boolean value, the value will be converted to its boolean
        equivalent.

        Args:
            values: List of values to validate. Must be in the same order as configured for this node.
        Returns:
             Sanitized values
        Raises:
            TypeError if any of the values are invalid, of if the number of values does
            not match the number of types of this node.
        """
        if not self.type and values:
            raise TypeError(f"Expected no value(s), got {len(values)}")

        if not self.type:
            return values

        if len(values) != len(self.type):
            raise TypeError(f"Expected {len(self.type)} value(s), got {len(values)}")

        for i, expected_type in enumerate(self.type):
            received_type = type(values[i])
            if received_type is not expected_type:
                if (
                    expected_type is builtins.bool
                    and received_type is builtins.int
                    and values[i] in (0, 1)
                ):
                    # Some clients might send int 0 or 1 as substitute for bool
                    values[i] = bool(values[i])
                    continue

                raise TypeError(
                    f"Expected {expected_type} for value {i}, got {type(values[i])}"
                )
        return values

    def are_values_valid(self, values: list[T]) -> bool:
        """Convenience method for validate_values()."""
        try:
            self.validate_values(values)
        except TypeError:
            return False
        return True

    def __iter__(self):
        yield self
        if self.contents is not None:
            for subNode in self.contents:
                yield from subNode

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} @ {self.full_path} (D: "{self.description}" T:{self.type} V:{self.value})>'

    def __eq__(self, other) -> bool:
        if not isinstance(other, OSCPathNode):
            return NotImplemented
        return self.full_path == other.full_path


def python_type_list_to_osc_type(types_: list[type]) -> str:
    output = []
    for type_ in types_:
        match type_:
            case builtins.bool:
                output.append("T")
            case builtins.int:
                output.append("i")
            case builtins.float:
                output.append("f")
            case builtins.str:
                output.append("s")
            case _:  # pragma: no cover
                raise Exception(
                    f"Cannot convert {type_} to OSC type!"
                )  # pragma: no cover

    return "".join(output)
