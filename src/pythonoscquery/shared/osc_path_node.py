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
    def __init__(
        self,
        full_path: str,
        contents: list["OSCPathNode"] = None,
        access: OSCAccess = OSCAccess.NO_VALUE,
        description: str = None,
        value: Union[T, list[T]] = None,
    ):
        if not is_valid_path(full_path):
            raise ValueError(
                "Invalid path: Path must start with a single trailing forward slash (/)."
                "Path must not contain any of the following characters: {}."
                "Path must not have empty nodes (like /test//path). Path must not have trailing forward slashes. ".format(
                    disallowed_path_chars
                )
            )

        self._attributes: dict[OSCQueryAttribute, Any] = {}

        self._attributes[OSCQueryAttribute.FULL_PATH] = full_path

        self._attributes[OSCQueryAttribute.CONTENTS]: list["OSCPathNode"] = (
            contents or []
        )

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

        self._attributes[OSCQueryAttribute.TYPE] = types if value is not None else None

        self._attributes[OSCQueryAttribute.ACCESS] = access

        self._attributes[OSCQueryAttribute.DESCRIPTION] = description

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

        return cls(full_path, contents, access, description, value)

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
    def is_method(self) -> bool:
        """Returns True if this node is an OSC method, False otherwise.
        An OSC method"""
        if self.contents:
            return False
        return True

    def find_subnode(self, full_path: str) -> "OSCPathNode | None":
        """Recursively find a node with the given full path"""
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
        return json.dumps(self, cls=OSCNodeEncoder, attribute_filter=attribute)

    def validate_values(self, values: list[T]) -> list[T]:
        """Validate the given value types against the specified types of this node.
        Raises TypeError if any of the values are invalid, of if the number of values does
        not match the number of types of this node.
        Returns sanitized values,
        """
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
