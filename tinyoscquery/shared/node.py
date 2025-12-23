import builtins
import json
from json import JSONEncoder
from typing import List, TypeVar, Union

from tinyoscquery.shared.osc_access import OSCAccess


class OSCNodeEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, OSCQueryNode):
            obj_dict = {}
            for k, v in vars(o).items():
                if v is None:
                    continue

                k = k.lower()

                match k:
                    case "contents":
                        if len(v) < 1:
                            continue
                        obj_dict["CONTENTS"] = {}
                        for sub_node in v:
                            if sub_node.full_path is not None:
                                obj_dict["CONTENTS"][
                                    sub_node.full_path.split("/")[-1]
                                ] = sub_node
                            else:
                                continue
                    case "value":
                        if len(v) > 0:
                            obj_dict["VALUE"] = v
                            obj_dict["TYPE"] = python_type_list_to_osc_type(o.type_)
                    case _:
                        obj_dict[k.upper()] = v

            # FIXME: I missed something, so here's a hack!

            if "TYPE_" in obj_dict:
                del obj_dict["TYPE_"]
            return obj_dict

        return json.JSONEncoder.default(self, o)


T = TypeVar("T", bound=int | float | bool | str)


class OSCQueryNode:
    def __init__(
        self,
        full_path: str,
        contents: list["OSCQueryNode"] = None,
        access: OSCAccess = OSCAccess.NO_VALUE,
        description: str = None,
        value: Union[T, List[T]] = None,
    ):
        self.full_path = full_path

        self.contents: list["OSCQueryNode"] = contents or []

        # Ensure that value is an iterable
        try:
            iter(value)
        except TypeError:
            value = [value] if value else []
        self.value = value

        if not value and access is not OSCAccess.NO_VALUE:
            raise Exception(
                f"No value(s) given, access must be {OSCAccess.NO_VALUE.name} for container nodes."
            )

        self.access = access

        self.description = description

    @classmethod
    def from_json(cls, json) -> "OSCQueryNode":
        contents = None
        if "CONTENTS" in json:
            sub_nodes = []
            for subNode in json["CONTENTS"]:
                sub_nodes.append(OSCQueryNode.from_json(json["CONTENTS"][subNode]))
            contents = sub_nodes

        # This *should* be required but some implementations don't have it...
        full_path = None
        if "FULL_PATH" in json:
            full_path = json["FULL_PATH"]

        description = None
        if "DESCRIPTION" in json:
            description = json["DESCRIPTION"]

        access = None
        if "ACCESS" in json:
            access = OSCAccess(json["ACCESS"])

        value = None
        if "VALUE" in json:
            value = []
            if not isinstance(json["VALUE"], list):
                raise Exception("OSCQuery JSON Value is not List / Array? Out-of-spec?")

            for idx, v in enumerate(json["VALUE"]):
                # According to the spec, if there is not yet a value, the return will be an empty JSON object
                if isinstance(v, dict) and not v:
                    # FIXME does this apply to all values in the value array always...? I assume it does here
                    value = []
                    break
                else:
                    value.append(v)

        return cls(full_path, contents, access, description, value)

    @property
    def type_(self) -> list[T]:
        types = []
        for v in self.value:
            types.append(type(v))
        return types

    def find_subnode(self, full_path: str) -> Union["OSCQueryNode", None]:
        if self.full_path == full_path:
            return self

        if not self.contents:
            return None

        for sub_node in self.contents:
            found_node = sub_node.find_subnode(full_path)
            if found_node:
                return found_node

        return None

    def add_child_node(self, child: "OSCQueryNode"):
        if child == self:
            return

        path_split = child.full_path.rsplit("/", 1)
        if len(path_split) < 2:
            raise Exception("Tried to add child node with invalid full path!")

        parent_path = path_split[0]

        if parent_path == "":
            parent_path = "/"

        parent = self.find_subnode(parent_path)

        if parent is None:
            parent = OSCQueryNode(parent_path)
            self.add_child_node(parent)

        parent.contents.append(child)

    def to_json(self) -> str:
        return json.dumps(self, cls=OSCNodeEncoder)

    def __iter__(self):
        yield self
        if self.contents is not None:
            for subNode in self.contents:
                yield from subNode

    def __str__(self) -> str:
        return f'<OSCQueryNode @ {self.full_path} (D: "{self.description}" T:{self.type_} V:{self.value})>'


def osc_type_string_to_python_type(type_str: str) -> list[type]:
    types: list[type] = []
    for type_value in type_str:
        match type_value:
            case "":
                pass
            case "i":
                types.append(int)
            case "f" | "h" | "d" | "t":
                types.append(float)
            case "T" | "F":
                types.append(bool)
            case "s":
                types.append(str)
            case _:
                raise Exception(
                    f"Unknown OSC type when converting! {type_value} -> ???"
                )

    return types


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
            case _:
                raise Exception(f"Cannot convert {type_} to OSC type!")

    return " ".join(output)


if __name__ == "__main__":
    root = OSCQueryNode("/", description="root node")
    root.add_child_node(OSCQueryNode("/test/node/one"))
    root.add_child_node(OSCQueryNode("/test/node/two"))
    root.add_child_node(OSCQueryNode("/test/othernode/one"))
    root.add_child_node(OSCQueryNode("/test/othernode/three"))

    # print(root)

    for _child in root:
        print(_child)
