import builtins

import pytest

from pythonoscquery.shared.osc_access import OSCAccess
from pythonoscquery.shared.osc_address_space import OSCAddressSpace
from pythonoscquery.shared.osc_path_node import OSCPathNode
from pythonoscquery.shared.oscquery_spec import OSCQueryAttribute


@pytest.fixture
def path():
    return "/test"


@pytest.fixture
def access():
    return OSCAccess.NO_VALUE


@pytest.fixture
def description():
    return "A test description"


@pytest.fixture
def attribute():
    return OSCQueryAttribute.FULL_PATH


@pytest.fixture
def address_space():
    return OSCAddressSpace()


class TestOSCPathNode:
    @pytest.mark.parametrize(
        "path",
        [
            "",
            "////testing",
            "/test#",
            "/test*",
            "/test?",
            "/test,",
            "/test[",
            "/test]",
            "/test{",
            "/test}",
            "/test/",
            "/ ",
        ],
        indirect=False,
    )
    def test_node_creation_rejects_invalid_path(self, path):
        # Arrange
        # Act
        with pytest.raises(ValueError):
            node = OSCPathNode(path)

    @pytest.mark.parametrize(
        "path",
        [
            "/",
            "/test",
            "/test/foo/bar/baz",
        ],
        indirect=False,
    )
    def test_node_creation_accepts_valid_path(self, path):
        # Arrange
        # Act
        node = OSCPathNode(path)
        # Assert
        assert node is not None

    @pytest.mark.parametrize(
        "path",
        [
            "/testing",
            "/testing/foo",
            "/testing/foo/bar",
        ],
        indirect=False,
    )
    @pytest.mark.parametrize(
        "access",
        [
            OSCAccess.READWRITE_VALUE,
            OSCAccess.READONLY_VALUE,
            OSCAccess.WRITEONLY_VALUE,
        ],
        indirect=False,
    )
    def test_node_creation_with_wrong_access_for_container_nodes_raises(
        self, path, access
    ):
        # Arrange
        # Act
        with pytest.raises(ValueError):
            node = OSCPathNode(
                path,
                access,
            )

    @pytest.mark.parametrize(
        "path",
        [
            "/testing",
            "/testing/foo",
            "/testing/foo/bar",
        ],
        indirect=False,
    )
    @pytest.mark.parametrize(
        "access",
        [
            OSCAccess.NO_VALUE,
        ],
        indirect=False,
    )
    def test_node_creation_with_novalue_access_types_for_method_nodes_raises(
        self, path, access
    ):
        # Arrange
        # Act
        with pytest.raises(ValueError):
            node = OSCPathNode(path, access, 99)

    @pytest.mark.parametrize(
        "path",
        [
            "/",
            "/test",
            "/test/foo/bar/baz",
        ],
        indirect=False,
    )
    @pytest.mark.parametrize(
        "access",
        [
            OSCAccess.READWRITE_VALUE,
            OSCAccess.READONLY_VALUE,
            OSCAccess.WRITEONLY_VALUE,
        ],
        indirect=False,
    )
    def test_node_creation_sets_correct_description(self, path, access):
        # Arrange
        # Act
        node = OSCPathNode(path, access, value=99)
        # Assert
        assert node.access is access

    @pytest.mark.parametrize(
        "path",
        [
            "/",
            "/test",
            "/test/foo/bar/baz",
        ],
        indirect=False,
    )
    @pytest.mark.parametrize(
        "description",
        [
            "Some description",
            "Another description",
        ],
        indirect=False,
    )
    def test_node_creation_sets_correct_access(self, path, description):
        # Arrange
        # Act
        node = OSCPathNode(path, description=description)
        # Assert
        assert node.description is description

    def test_node_equality_operator_only_with_same_type(self):
        assert (OSCPathNode("/test") == 99) is False

    def test_node_equality_operator(self):
        assert (OSCPathNode("/test") == OSCPathNode("/test")) is True

    def test_node_repr(self):
        # Arrange
        node = OSCPathNode("/test")
        # Act
        # Assert
        assert node.__class__.__name__ in repr(node)
        assert str(node.full_path) in repr(node)

    def test_node_value_checker_accepts_values_with_correct_types(self):
        # Arrange
        node = OSCPathNode(
            "/test",
            access=OSCAccess.READONLY_VALUE,
            value=[99, "hello", True, False, 123.5],
        )
        # Act
        # Assert
        assert node.are_values_valid([12, "hi", False, True, 987.2]) is True
        assert node.are_values_valid([12.55, False, 897, "gsdfg", 12]) is False

    def test_node_value_checker_rejects_values_when_node_has_no_configured_types(self):
        # Arrange
        node = OSCPathNode(
            "/test",
        )
        # Act
        # Assert
        assert node.are_values_valid([12.55, False, 897, "gsdfg", 12]) is False

    def test_node_attributes_are_set(self):
        # Arrange
        child = OSCPathNode(
            "/test/bar",
            access=OSCAccess.READONLY_VALUE,
            description="child of test",
            value=[99, "hello", True, False, 123.5],
        )
        node = OSCPathNode(
            "/test",
            contents=[child],
            description="test",
        )
        # Act
        # Assert
        assert node.attributes == {
            OSCQueryAttribute.FULL_PATH: "/test",
            OSCQueryAttribute.CONTENTS: [child],
            OSCQueryAttribute.ACCESS: OSCAccess.NO_VALUE,
            OSCQueryAttribute.DESCRIPTION: "test",
            OSCQueryAttribute.VALUE: None,
            OSCQueryAttribute.TYPE: None,
        }
        assert child.attributes == {
            OSCQueryAttribute.FULL_PATH: "/test/bar",
            OSCQueryAttribute.CONTENTS: None,
            OSCQueryAttribute.ACCESS: OSCAccess.READONLY_VALUE,
            OSCQueryAttribute.DESCRIPTION: "child of test",
            OSCQueryAttribute.VALUE: [99, "hello", True, False, 123.5],
            OSCQueryAttribute.TYPE: [
                builtins.int,
                builtins.str,
                builtins.bool,
                builtins.bool,
                builtins.float,
            ],
        }

    def test_node_is_container(self):
        # Arrange
        node = OSCPathNode(
            "/test",
            access=OSCAccess.READONLY_VALUE,
            value=[99, "hello", True, False, 123.5],
        )
        # Act
        # Assert
        assert node.is_container is False

    def test_node_is_not_container(self, address_space):
        # Arrange
        node = OSCPathNode(
            "/test/bar",
            access=OSCAccess.READONLY_VALUE,
            value=[99, "hello", True, False, 123.5],
        )
        address_space.add_node(node)
        sut = address_space.find_node("/test")
        # Act
        # Assert
        assert sut.is_container is True

    def test_node_json_complete_serialization(self):
        # Arrange
        child = OSCPathNode(
            "/test/foo",
            access=OSCAccess.READONLY_VALUE,
            value=[99, "hello", True, False, 123.5],
            description="test",
        )
        node = OSCPathNode(
            "/test",
            contents=[child],
        )

        # Act
        json = node.to_json()
        # Assert
        assert (
            json
            == '{"FULL_PATH": "/test", "CONTENTS": {"foo": {"FULL_PATH": "/test/foo", "VALUE": [99, "hello", true, false, 123.5], "TYPE": "isTTf", "ACCESS": 1, "DESCRIPTION": "test"}}, "ACCESS": 0}'
        )

    def test_node_json_complete_serialization_empty_description_empty_contents(self):
        # Arrange
        node = OSCPathNode(
            "/test",
            access=OSCAccess.READONLY_VALUE,
            value=[99, "hello", True, False, 123.5],
        )

        # Act
        json = node.to_json()
        # Assert
        assert (
            json
            == '{"FULL_PATH": "/test", "VALUE": [99, "hello", true, false, 123.5], "TYPE": "isTTf", "ACCESS": 1}'
        )

    @pytest.mark.parametrize(
        "attribute",
        [
            OSCQueryAttribute.FULL_PATH,
            OSCQueryAttribute.VALUE,
            OSCQueryAttribute.ACCESS,
            OSCQueryAttribute.CONTENTS,
            OSCQueryAttribute.DESCRIPTION,
            OSCQueryAttribute.TYPE,
        ],
        indirect=False,
    )
    def test_node_json_complete_serialization_filter_attribute(self, attribute):
        # Arrange
        child = OSCPathNode(
            "/test/foo",
            access=OSCAccess.READONLY_VALUE,
            value=[99, "hello", True, False, 123.5],
            description="foo",
        )
        node = OSCPathNode(
            "/test",
            contents=[child],
            description="test",
        )

        # Act 1
        json = node.to_json(attribute)
        # Assert 1
        match attribute:
            case OSCQueryAttribute.FULL_PATH:
                assert json == '{"FULL_PATH": "/test"}'
            case OSCQueryAttribute.VALUE:
                assert json == "{}"
            case OSCQueryAttribute.ACCESS:
                assert json == '{"ACCESS": 0}'
            case OSCQueryAttribute.CONTENTS:
                assert json == '{"CONTENTS": {"foo": {}}}'
            case OSCQueryAttribute.DESCRIPTION:
                assert json == '{"DESCRIPTION": "test"}'
            case OSCQueryAttribute.TYPE:
                assert json == "{}"
            case _:
                assert False

        # Act 2
        json = child.to_json(attribute)
        # Assert 2
        match attribute:
            case OSCQueryAttribute.FULL_PATH:
                assert json == '{"FULL_PATH": "/test/foo"}'
            case OSCQueryAttribute.VALUE:
                assert json == '{"VALUE": [99, "hello", true, false, 123.5]}'
            case OSCQueryAttribute.ACCESS:
                assert json == '{"ACCESS": 1}'
            case OSCQueryAttribute.CONTENTS:
                assert json == "{}"
            case OSCQueryAttribute.DESCRIPTION:
                assert json == '{"DESCRIPTION": "foo"}'
            case OSCQueryAttribute.TYPE:
                assert json == '{"TYPE": "isTTf"}'
            case _:
                assert False

    def test_node_from_json(self):
        # Arrange
        # Act
        node = OSCPathNode.from_json(
            {
                "FULL_PATH": "/test",
                "VALUE": [99, "hello", True, False, 123.5],
                "TYPE": "isTTf",
                "ACCESS": 1,
            }
        )

        # Assert
        assert node.full_path == "/test"
        assert node.type == [
            builtins.int,
            builtins.str,
            builtins.bool,
            builtins.bool,
            builtins.float,
        ]
        assert node.value == [99, "hello", True, False, 123.5]
        assert node.access == OSCAccess.READONLY_VALUE
        assert node.contents is None
        assert node.description is None

    def test_node_from_json_with_children(self):
        # Arrange
        # Act
        node = OSCPathNode.from_json(
            {
                "FULL_PATH": "/test",
                "CONTENTS": {
                    "foo": {
                        "FULL_PATH": "/test/foo",
                        "VALUE": [99, "hello", True, False, 123.5],
                        "TYPE": "isTTf",
                        "ACCESS": 1,
                        "DESCRIPTION": "test",
                    }
                },
                "ACCESS": 0,
            }
        )
        child = node.contents[0]

        # Assert
        assert node.full_path == "/test"
        assert node.contents == [child]
        assert node.description is None

        assert child.type == [
            builtins.int,
            builtins.str,
            builtins.bool,
            builtins.bool,
            builtins.float,
        ]
        assert child.value == [99, "hello", True, False, 123.5]
        assert child.access == OSCAccess.READONLY_VALUE
        assert child.description == "test"

    def test_node_from_json_value_invalid(self):
        # Arrange
        # Act
        # Assert
        with pytest.raises(TypeError):
            node = OSCPathNode.from_json(
                {
                    "FULL_PATH": "/test",
                    "VALUE": 99,  # not an json array (python list)
                    "TYPE": "i",
                    "ACCESS": 1,
                }
            )

    def test_node_instantiated_with_content_and_value_raises(self):
        # Arrange
        # Act
        # Assert
        with pytest.raises(ValueError):
            node = OSCPathNode(
                full_path="/test",
                contents=[OSCPathNode("/test/child")],
                value=[99, "hello", True, False, 123.5],
                access=OSCAccess.READONLY_VALUE,
                description="Code can be either container or method, but not both.",
            )

    def test_child_node_added_to_method_node_raises(self):
        # Arrange
        method_node = OSCPathNode(
            full_path="/test",
            value=[99, "hello", True, False, 123.5],
            access=OSCAccess.READONLY_VALUE,
            description="Code can be either container or method, but not both.",
        )
        child_node = OSCPathNode(
            full_path="/test/child",
            value=[99],
            access=OSCAccess.READONLY_VALUE,
            description="This child node can't be added",
        )
        # Act
        # Assert
        with pytest.raises(ValueError):
            method_node.add_child(child_node)
