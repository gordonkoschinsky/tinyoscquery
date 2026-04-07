import pytest

from pythonoscquery.shared.osc_address_space import OSCAddressSpace
from pythonoscquery.shared.osc_path_node import OSCPathNode


def path():
    return "/test"


@pytest.fixture
def address_space():
    return OSCAddressSpace()


class TestOSCAddressSpace:
    def test_empty_address_space_contains_root_node(self):
        # Arrange
        ns = OSCAddressSpace()
        # Act
        # Assert
        assert ns.root_node is not None
        assert ns.root_node.full_path == "/"
        assert ns.number_of_nodes == 1

    def test_address_space_with_one_toplevel_node_contains_two_nodes(self):
        # Arrange
        ns = OSCAddressSpace()
        # Act
        ns.add_node(OSCPathNode("/test"))
        # Assert
        assert ns.number_of_nodes == 2

    def test_address_space_repr(self):
        # Arrange
        ns = OSCAddressSpace()
        # Act
        # Assert
        assert ns.__class__.__name__ in repr(ns)
        assert str(ns.number_of_nodes) in repr(ns)

    def test_address_space_finds_added_node(self):
        # Arrange
        ns = OSCAddressSpace()
        node = OSCPathNode("/test/for/bar/baz")

        # Act
        ns.add_node(node)

        # Assert
        assert ns.find_node(node.full_path) is node

    def test_address_space_does_not_find_none_existing_node(self):
        # Arrange
        ns = OSCAddressSpace()
        node = OSCPathNode("/test/for/bar/baz")

        # Act
        ns.add_node(node)

        # Assert
        assert ns.find_node("/some/other/address") is None

    def test_address_space_adding_creates_missing_path_nodes(self):
        # Arrange
        ns = OSCAddressSpace()
        # Act
        ns.add_node(OSCPathNode("/test/foo/bar/baz"))
        # Assert
        assert ns.number_of_nodes == 5
        assert ns.find_node("/test") is not None
        assert ns.find_node("/test/foo") is not None
        assert ns.find_node("/test/foo/bar") is not None
        assert ns.find_node("/test/foo/bar/baz") is not None

    @pytest.mark.parametrize(
        "path",
        [
            "/",
            "/testing",
            "/testing/foo",
            "/testing/foo/bar",
        ],
        indirect=False,
    )
    def test_address_space_adding_child_with_same_path_does_nothing(
        self, path, address_space
    ):
        # Arrange
        node = OSCPathNode(path)
        address_space.add_node(node)
        number_of_children_before_adding = address_space.number_of_nodes
        # Act
        address_space.add_node(OSCPathNode(path))
        # Assert
        assert address_space.number_of_nodes == number_of_children_before_adding

    def test_address_space_nodes_on_path_are_not_created_multiple_times(
        self, address_space
    ):
        # Arrange / Act
        node = OSCPathNode("/foo/bar")
        address_space.add_node(node)
        node = OSCPathNode("/foo/baz")
        address_space.add_node(node)
        # Assert
        assert address_space.number_of_nodes == 4
