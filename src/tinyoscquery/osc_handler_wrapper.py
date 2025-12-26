import logging

from pythonosc.dispatcher import Dispatcher

from tinyoscquery.shared.osc_path_node import OSCPathNode

logger = logging.getLogger(__name__)


class OSCCallbackWrapper:
    def __init__(self, node: OSCPathNode, dispatcher: Dispatcher, callback: callable):
        self.node = node
        self.callback = callback
        self.handler = dispatcher.map(node.full_path, self)

    def __call__(self, *args, **kwargs):
        logger.debug(
            f"OSCHandlerWrapper {self.node.full_path} called with args={args} kwargs={kwargs}"
        )
        values = args
        if self.handler.needs_reply_address:
            # the osc client address, when required by the callback, is always the first argument. We don't need to check it.
            values = values[1:]
        # the osc message address is always the next argument. We don't need to check it.
        values = values[1:]
        if self.handler.args:
            # fixed parameters, when required by the callback, are always the next argument. We don't need to check them.
            values = values[1:]

        if len(values) != len(self.node.type):
            raise TypeError(
                f"Expected {len(self.node.type)} value(s), got {len(values)} when calling callback {repr(self.callback)} for {self.node.full_path}"
            )

        for i, type_ in enumerate(self.node.type):
            if type(values[i]) is not type_:
                raise TypeError(f"Expected {type_} for value {i}, got {values[i]}")

        return self.callback(*args, **kwargs)
