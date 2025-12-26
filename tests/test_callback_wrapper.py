import logging

import pytest
from pythonosc import osc_message_builder
from pythonosc.dispatcher import Dispatcher

from tinyoscquery.osc_handler_wrapper import OSCCallbackWrapper
from tinyoscquery.shared.osc_path_node import OSCPathNode

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
def callback_wrapper(dispatcher, callback, address, osc_path_node):
    return OSCCallbackWrapper(osc_path_node, dispatcher=dispatcher, callback=callback)


class TestCallbackWrapper:
    @pytest.mark.parametrize(
        "address", ["/lalalala", "/test", "/eins/zwo/drei"], indirect=False
    )
    def test_callback_wrapper_calls_callback_when_called(
        self, dispatcher, callback, callback_wrapper, address
    ):
        for h in dispatcher.handlers_for_address(address):
            h.invoke(
                ("dummy", 99), osc_message_builder.OscMessageBuilder(address).build()
            )

        callback.assert_called_once_with(address)

    @pytest.mark.parametrize(
        "address", ["/lalalala", "/test", "/eins/zwo/drei"], indirect=False
    )
    def test_callback_wrapper_does_not_call_callback_when_called_with_different_address(
        self, dispatcher, callback, callback_wrapper, address
    ):
        message_address = "/message/address"

        # There should be already no handler for the message address
        for h in dispatcher.handlers_for_address(message_address):
            h.invoke(
                ("dummy", 99),
                osc_message_builder.OscMessageBuilder(message_address).build(),
            )

        callback.assert_not_called()

    @pytest.mark.parametrize("address", ["/test"], indirect=False)
    @pytest.mark.parametrize(
        "osc_path_node", [OSCPathNode("/test", value=67)], indirect=False
    )
    def test_raises_when_value_in_message_missing(
        self, dispatcher, callback, callback_wrapper, address, osc_path_node
    ):
        for h in dispatcher.handlers_for_address(address):
            with pytest.raises(TypeError):
                h.invoke(
                    ("dummy", 99),
                    osc_message_builder.OscMessageBuilder(address).build(),
                )

    @pytest.mark.parametrize("address", ["/test"], indirect=False)
    @pytest.mark.parametrize(
        "osc_path_node", [OSCPathNode("/test", value=67)], indirect=False
    )
    def test_callback_called_with_one_value(
        self, dispatcher, callback, callback_wrapper, address, osc_path_node
    ):
        message_builder = osc_message_builder.OscMessageBuilder(address)
        value_1 = 1
        message_builder.add_arg(value_1)
        message = message_builder.build()

        for h in dispatcher.handlers_for_address(address):
            h.invoke(("dummy", 99), message)

        callback.assert_called_once_with(address, value_1)

    @pytest.mark.parametrize("address", ["/test"], indirect=False)
    @pytest.mark.parametrize(
        "osc_path_node", [OSCPathNode("/test", value=node_values)], indirect=False
    )
    def test_callback_called_with_many_values(
        self, dispatcher, callback, callback_wrapper, address, osc_path_node
    ):
        message_builder = osc_message_builder.OscMessageBuilder(address)

        for v in node_values:
            message_builder.add_arg(v)
        message = message_builder.build()

        for h in dispatcher.handlers_for_address(address):
            h.invoke(("dummy", 99), message)

        args = callback.call_args.args

        # Check arguments, take floating point errors into account
        for called, expected in zip(args, [address, *node_values]):
            assert called == pytest.approx(expected)

        callback.assert_called_once()
