import builtins
import logging

import pytest
from pythonosc import osc_message_builder
from pythonosc.dispatcher import Dispatcher

from pythonoscquery.pythonosc_callback_wrapper import OSCCallbackWrapper, map_node
from pythonoscquery.shared.osc_access import OSCAccess
from pythonoscquery.shared.osc_address_space import OSCAddressSpace
from pythonoscquery.shared.osc_path_node import OSCPathNode

logging.basicConfig(level=logging.DEBUG)

node_values = [1, "hello", 5.92, True]


@pytest.fixture
def address():
    return "/test"


@pytest.fixture
def osc_path_node(address):
    return OSCPathNode(address)


@pytest.fixture
def dispatcher():
    return Dispatcher()


@pytest.fixture
def callback(mocker):
    return mocker.stub(name="callback_stub")


@pytest.fixture
def callback_wrapper(callback, osc_path_node):
    return OSCCallbackWrapper(osc_path_node, callback=callback)


@pytest.fixture
def needs_reply_address():
    return False


@pytest.fixture
def fixed_args():
    return ["first fixed", 123]


@pytest.fixture
def address_space():
    return OSCAddressSpace()


def get_message_value(osc_path_node):
    """Build message value with the correct type.
    Don't use the same value as in the node spec, but create new one with the same type
    """
    node_value = osc_path_node.value[0]
    match type(node_value):
        case builtins.bool if node_value is True:
            value_1 = True
        case builtins.bool if node_value is False:
            value_1 = False
        case builtins.int:
            value_1 = 99541
        case builtins.float:
            value_1 = 874.15314
        case builtins.str:
            value_1 = "foobar"
    return value_1


class TestCallbackWrapper:
    def test_wrapper_called_without_registered_handler_raises(self, callback_wrapper):
        with pytest.raises(TypeError):
            callback_wrapper()

    @pytest.mark.parametrize(
        "address", ["/lalalala", "/test", "/eins/zwo/drei"], indirect=False
    )
    def test_callback_wrapper_calls_callback_when_called(
        self, osc_path_node, dispatcher, callback, address
    ):
        map_node(osc_path_node, dispatcher, callback)

        for h in dispatcher.handlers_for_address(address):
            h.invoke(
                ("dummy", 99), osc_message_builder.OscMessageBuilder(address).build()
            )

        callback.assert_called_once_with(address)

    @pytest.mark.parametrize(
        "address", ["/lalalala", "/test", "/eins/zwo/drei"], indirect=False
    )
    def test_callback_wrapper_when_called_with_different_address_not_called(
        self, dispatcher, callback, callback_wrapper, osc_path_node
    ):
        map_node(osc_path_node, dispatcher, callback)
        message_address = "/message/address"

        # There should be already no handler for the message address
        for h in dispatcher.handlers_for_address(message_address):
            h.invoke(
                ("dummy", 99),
                osc_message_builder.OscMessageBuilder(message_address).build(),
            )

        callback.assert_not_called()

    @pytest.mark.parametrize(
        "address", ["/lalalala", "/test", "/eins/zwo/drei"], indirect=False
    )
    @pytest.mark.parametrize("needs_reply_address", [False, True], indirect=False)
    @pytest.mark.parametrize("fixed_args", [["first fixed", 123], ()], indirect=False)
    def test_callback_wrapper_calls_callback_with_optional_args_when_called(
        self,
        osc_path_node,
        dispatcher,
        callback,
        address,
        needs_reply_address,
        fixed_args,
    ):
        map_node(
            osc_path_node,
            dispatcher,
            callback,
            None,
            *fixed_args,
            needs_reply_address=needs_reply_address,
        )

        for h in dispatcher.handlers_for_address(address):
            h.invoke(
                ("dummy", 99), osc_message_builder.OscMessageBuilder(address).build()
            )

        if needs_reply_address:
            if fixed_args:
                callback.assert_called_once_with(("dummy", 99), address, fixed_args)
            else:
                callback.assert_called_once_with(("dummy", 99), address)
        else:
            if fixed_args:
                callback.assert_called_once_with(address, fixed_args)
            else:
                callback.assert_called_once_with(address)

    @pytest.mark.parametrize("address", ["/test"], indirect=False)
    @pytest.mark.parametrize(
        "osc_path_node",
        [OSCPathNode("/test", value=67, access=OSCAccess.READWRITE_VALUE)],
        indirect=False,
    )
    def test_callback_when_value_in_message_missing_not_called(
        self, dispatcher, callback, address, osc_path_node
    ):
        map_node(osc_path_node, dispatcher, callback)

        for h in dispatcher.handlers_for_address(address):
            h.invoke(
                ("dummy", 99),
                osc_message_builder.OscMessageBuilder(address).build(),
            )

        callback.assert_not_called()

    @pytest.mark.parametrize("address", ["/test"], indirect=False)
    @pytest.mark.parametrize(
        "osc_path_node",
        [OSCPathNode("/test", value=67, access=OSCAccess.READWRITE_VALUE)],
        indirect=False,
    )
    def test_callback_when_too_many_value_in_message_not_called(
        self, dispatcher, callback, callback_wrapper, address, osc_path_node
    ):
        map_node(osc_path_node, dispatcher, callback)

        message_builder = osc_message_builder.OscMessageBuilder(address)
        for v in node_values:
            message_builder.add_arg(v)
        message = message_builder.build()

        for h in dispatcher.handlers_for_address(address):
            h.invoke(
                ("dummy", 99),
                message,
            )

        callback.assert_not_called()

    @pytest.mark.parametrize("address", ["/test"], indirect=False)
    @pytest.mark.parametrize(
        "osc_path_node",
        [
            OSCPathNode("/test", value=67, access=OSCAccess.READWRITE_VALUE),
            OSCPathNode("/test", value=123.456, access=OSCAccess.READWRITE_VALUE),
            OSCPathNode("/test", value="hello", access=OSCAccess.READWRITE_VALUE),
            OSCPathNode("/test", value=True, access=OSCAccess.READWRITE_VALUE),
            OSCPathNode("/test", value=False, access=OSCAccess.READWRITE_VALUE),
        ],
        indirect=False,
    )
    def test_callback_called_with_one_correct_value(
        self, dispatcher, callback, callback_wrapper, address, osc_path_node
    ):
        map_node(osc_path_node, dispatcher, callback)

        message_builder = osc_message_builder.OscMessageBuilder(address)
        value_1 = get_message_value(osc_path_node)

        message_builder.add_arg(value_1)
        message = message_builder.build()

        for h in dispatcher.handlers_for_address(address):
            h.invoke(("dummy", 99), message)

        # Check arguments, take floating point errors into account
        args = callback.call_args.args
        for called, expected in zip(args, [address, value_1]):
            assert called == pytest.approx(expected)

        callback.assert_called_once()

    @pytest.mark.parametrize("address", ["/test"], indirect=False)
    @pytest.mark.parametrize(
        "osc_path_node",
        [OSCPathNode("/test", value=node_values, access=OSCAccess.READWRITE_VALUE)],
        indirect=False,
    )
    def test_callback_called_with_many_values(
        self, dispatcher, callback, callback_wrapper, address, osc_path_node
    ):
        map_node(osc_path_node, dispatcher, callback)

        message_builder = osc_message_builder.OscMessageBuilder(address)

        for v in node_values:
            message_builder.add_arg(v)
        message = message_builder.build()

        for h in dispatcher.handlers_for_address(address):
            h.invoke(("dummy", 99), message)

        # Check arguments, take floating point errors into account
        args = callback.call_args.args
        for called, expected in zip(args, [address, *node_values]):
            assert called == pytest.approx(expected)

        callback.assert_called_once()

    @pytest.mark.parametrize("address", ["/test"], indirect=False)
    @pytest.mark.parametrize(
        "osc_path_node",
        [OSCPathNode("/test", value=67, access=OSCAccess.READWRITE_VALUE)],
        indirect=False,
    )
    def test_callback_with_wrong_value_type_not_called(
        self, dispatcher, callback, callback_wrapper, address, osc_path_node
    ):
        map_node(osc_path_node, dispatcher, callback)

        message_builder = osc_message_builder.OscMessageBuilder(address)
        value_1 = "baz"
        message_builder.add_arg(value_1)
        message = message_builder.build()

        for h in dispatcher.handlers_for_address(address):
            h.invoke(("dummy", 99), message)

        callback.assert_not_called()

    def test_node_mapping_adds_to_address_space(
        self, osc_path_node, dispatcher, callback, address_space
    ):
        assert address_space.number_of_nodes == 1
        map_node(osc_path_node, dispatcher, callback, address_space)
        assert address_space.number_of_nodes == 2
        assert address_space.find_node(osc_path_node.full_path) == osc_path_node

    @pytest.mark.parametrize("address", ["/test"], indirect=False)
    @pytest.mark.parametrize(
        "osc_path_node",
        [
            OSCPathNode(
                "/test", value=[True, False, 99], access=OSCAccess.READWRITE_VALUE
            )
        ],
        indirect=False,
    )
    def test_boolean_values_substituted_with_ints_considered_valid(
        self,
        osc_path_node,
        dispatcher,
        callback,
        callback_wrapper,
        address_space,
        address,
    ):
        map_node(osc_path_node, dispatcher, callback)

        message_builder = osc_message_builder.OscMessageBuilder(address)

        # Build a message that uses int 0 and 1 as substitutes for True and False
        for v in [0, 1, 100]:
            message_builder.add_arg(v)
        message = message_builder.build()

        for h in dispatcher.handlers_for_address(address):
            h.invoke(("dummy", 99), message)

        # Check arguments, take floating point errors into account
        args = callback.call_args.args
        for called, expected in zip(
            args, [address, *[False, True, 100]]
        ):  # the int substitutes should be converted back to boolean values
            assert called == pytest.approx(expected)

        callback.assert_called_once()
