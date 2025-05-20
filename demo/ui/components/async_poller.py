from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

import mesop.labs as mel

from state.state import AppState


@dataclass
class AsyncAction:
    value: AppState
    duration_seconds: int


@mel.web_component(path='./async_poller.js')
def async_poller(
    *,
    trigger_event: Callable[[mel.WebEvent], Any],
    action: AsyncAction | None = None,
    key: str | None = None,
):
    """Creates an invisible component that will delay state changes asynchronously.

    Right now this implementation is limited since we basically just pass the key
    around. But ideally we also pass in some kind of value to update when the time
    out expires.

    The main benefit of this component is for cases, such as status messages that
    may appear and disappear after some duration. The primary example here is the
    example snackbar widget, which right now blocks the UI when using the sleep
    yield approach.

    The other benefit of this component is that it works generically (rather than
    say implementing a custom snackbar widget as a web component).

    Returns:
      The web component that was created.
    """
    return mel.insert_web_component(
        name='async-action-component',
        key=key,
        events={
            'triggerEvent': trigger_event,
        },
        properties={
            'polling_interval': action.duration_seconds if action else 1,
            'action': asdict(action) if action else {},
        },
    )
