import dataclasses
import json
import uuid

from typing import Any, Literal

import mesop as me

from common.types import DataPart, Message, TextPart
from state.host_agent_service import SendMessage
from state.state import AppState, StateMessage


ROW_GAP = 15
BOX_PADDING = 20


@dataclasses.dataclass
class FormElement:
    """FormElement is a declarative structure for the form rendering"""

    name: str = ''
    label: str = ''
    value: str = ''
    formType: Literal[
        'color',
        'date',
        'datetime-local',
        'email',
        'month',
        'number',
        'password',
        'search',
        'tel',
        'text',
        'time',
        'url',
        'week',
        # These are custom types that dictate non input elements.
        'radio',
        'checkbox',
        'date-picker',
    ] = 'text'
    required: bool = False
    formDetails: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class FormState:
    message_id: str
    data: dict[str, str]
    errors: dict[str, str]
    elements: list[FormElement]

    def __post_init__(self):
        # Parse each element as FormElement. Clean up for non-recursive dict parse
        for i, element_dict in enumerate(self.elements):
            if isinstance(element_dict, dict):
                self.elements[i] = FormElement(**element_dict)


@me.stateclass
class State:
    """This contains the data in the form"""

    # forms: dict[str, FormState]
    forms: dict[str, str]


def is_form(message: StateMessage) -> bool:
    """Returns whether the message indicates a form should be rendered"""
    if any([x[1] == 'form' for x in message.content]):
        return True
    return False


def form_sent(message: StateMessage, app_state: AppState) -> bool:
    return message.message_id in app_state.form_responses


def render_form(message: StateMessage, app_state: AppState):
    """Renders the form or the data entered in a submitted form"""
    # Check if the form was completed, if so, render the content as a card
    if message.message_id in app_state.completed_forms:
        render_form_card(message, app_state.completed_forms[message.message_id])
        return
    # Otherwise, get the form structure.
    instructions, form_structure = generate_form_elements(message)

    data = {}
    # Initialize the state data
    for element in form_structure:
        data[element.name] = element.value

    state = me.state(State)
    if message.message_id not in state.forms:
        form = FormState(
            message_id=message.message_id,
            data=data,
            errors={},
            elements=form_structure,
        )
        try:
            state.forms[message.message_id] = form_state_to_string(form)
        except Exception as e:
            print('Failed to serialize form', e, form)
    render_structure(message.message_id, form_structure, instructions)


def render_form_card(message: StateMessage, data: dict[str, Any] | None):
    """Renders the result of a previous form as a card"""
    with me.box(
        style=me.Style(
            padding=me.Padding.all(BOX_PADDING),
            max_width='75vw',
            background=me.theme_var('surface'),
            border_radius=15,
            margin=me.Margin(top=5, bottom=20, left=5, right=5),
            justify_content=(
                'end' if message.role == 'agent' else 'space-between'
            ),
            box_shadow=(
                '0 1px 2px 0 rgba(60, 64, 67, 0.3), '
                '0 1px 3px 1px rgba(60, 64, 67, 0.15)'
            ),
        )
    ):
        if data:
            # Build markdown result
            lines = []
            for k, v in data.items():
                lines.append(
                    f'**{k}**: {v}  '
                )  # end with 2 spaces to force newline

            me.markdown('\n'.join(lines).rstrip())
        else:
            me.text('Form canceled')


def generate_form_elements(
    message: StateMessage,
) -> tuple[str, list[FormElement]]:
    """Returns a declarative structure for a form to generate"""
    # Get the message part with the form information.
    form_content = next(filter(lambda x: x[1] == 'form', message.content), None)
    if not form_content:
        return []
    form_info = form_content[0]
    if not isinstance(form_info, dict):
        return []
    return instructions_for_form(form_info), make_form_elements(form_info)


def make_form_elements(form_info: dict[str, Any]) -> list[FormElement]:
    if 'form' not in form_info or 'properties' not in form_info['form']:
        return []
    # This is the key, value pairs of field names -> field info. Now we need to
    # supplement it.
    fields = form_info['form']['properties']
    if 'required' in form_info['form'] and isinstance(
        form_info['form']['required'], list
    ):
        for field in form_info['form']['required']:
            if field in fields:
                fields[field]['required'] = True
    if 'form_data' in form_info and isinstance(form_info['form_data'], dict):
        for field, value in form_info['form_data'].items():
            fields[field]['value'] = value
    # Now convert the dictionary to FormElements
    elements = []
    for key, info in fields.items():
        elements.append(
            FormElement(
                name=key,
                label=info['title'] if 'title' in info else key,
                value=info['value'] if 'value' in info else '',
                required=info['required'] if 'required' in info else False,
                formType=info['format'] if 'format' in info else 'text',
                # TODO more details for input like validation rules
                formDetails={},
            )
        )
    return elements


def instructions_for_form(form_info: dict[str, Any]) -> str:
    if 'instructions' in form_info:
        return form_info['instructions']
    return ''


def render_structure(id: str, elements: list[FormElement], instructions: str):
    with me.box(
        style=me.Style(
            padding=me.Padding.all(BOX_PADDING),
            max_width='75vw',
            background=me.theme_var('surface'),
            border_radius=15,
            margin=me.Margin(top=5, bottom=20, left=5, right=5),
            box_shadow=(
                '0 1px 2px 0 rgba(60, 64, 67, 0.3), '
                '0 1px 3px 1px rgba(60, 64, 67, 0.15)'
            ),
        )
    ):
        if instructions:
            me.text(
                instructions,
                type='headline-4',
                style=me.Style(margin=me.Margin(bottom=10)),
            )
        for element in elements:
            with form_group():
                input_field(id=id, element=element)
        with me.box():
            me.button('Cancel', type='flat', on_click=cancel_form, key=id)
            me.button('Submit', type='flat', on_click=submit_form, key=id)


def input_field(
    *,
    id: str,
    element: FormElement,
    width: str | int = '100%',
):
    """Renders an individual form input field"""
    state = me.state(State)
    form = FormState(**json.loads(state.forms[id]))
    key = (
        element.name
        if element.name
        else element.label.lower().replace(' ', '_')
    )
    value = element.value
    if form.data.get(key):
        value = form.data[key]
    with me.box(style=me.Style(flex_grow=1, width=width)):
        me.input(
            key=f'{id}_{key}',
            label=element.label,
            value=value,
            appearance='outline',
            color='warn' if key in form.errors else 'primary',
            style=me.Style(width=width),
            type=element.formType,
            on_blur=on_blur,
        )
        if key in form.errors:
            me.text(
                form.errors[key],
                style=me.Style(
                    margin=me.Margin(top=-13, left=15, bottom=15),
                    color=me.theme_var('error'),
                    font_size=13,
                ),
            )


@me.content_component
def form_group(flex_direction: Literal['row', 'column'] = 'row'):
    """Groups input fields together visually"""
    with me.box(
        style=me.Style(
            display='flex',
            flex_direction=flex_direction,
            gap=ROW_GAP,
            width='100%',
        )
    ):
        me.slot()


def on_change(e: me.RadioChangeEvent):
    state = me.state(State)
    key_parts = e.key.split('_')
    id = key_parts[0]
    field = '_'.join(key_parts[1:])
    form = FormState(**json.loads(state.forms[id]))
    form.data[field] = e.value
    state.forms[id] = form_state_to_string(form)


def on_blur(e: me.InputBlurEvent):
    state = me.state(State)
    key_parts = e.key.split('_')
    id = key_parts[0]
    field = '_'.join(key_parts[1:])
    form = FormState(**json.loads(state.forms[id]))
    form.data[field] = e.value
    state.forms[id] = form_state_to_string(form)


async def cancel_form(e: me.ClickEvent):
    message_id = str(uuid.uuid4())
    app_state = me.state(AppState)
    app_state.form_responses[message_id] = e.key
    app_state.background_tasks[message_id] = ''
    app_state.completed_forms[e.key] = None
    request = Message(
        id=message_id,
        role='user',
        parts=[TextPart(text='rejected form entry')],
        metadata={
            'conversation_id': app_state.current_conversation_id,
            'message_id': message_id,
        },
    )
    response = await SendMessage(request)


async def send_response(id: str, state: State, app_state: AppState):
    message_id = str(uuid.uuid4())
    app_state.background_tasks[message_id] = ''
    app_state.form_responses[message_id] = id
    form = FormState(**json.loads(state.forms[id]))
    request = Message(
        id=message_id,
        role='user',
        parts=[DataPart(data=form.data)],
        metadata={
            'conversation_id': app_state.current_conversation_id,
            'message_id': message_id,
        },
    )
    response = await SendMessage(request)


async def submit_form(e: me.ClickEvent):
    try:
        state = me.state(State)
        id = e.key
        form = FormState(**json.loads(state.forms[id]))
        # Replace with real validation logic.
        errors = {}
        for element in form.elements:
            if element.name == 'error':
                continue
            if not form.data[element.name] and element.required:
                errors[element.name] = (
                    f'{element.name.replace("_", " ").capitalize()} is required'
                )
        form.errors = errors
        state.forms[id] = form_state_to_string(form)
        # Replace with form processing logic.
        if errors:
            return
        app_state = me.state(AppState)
        app_state.completed_forms[id] = form.data
        await send_response(id, state, app_state)
    except Exception as e:
        print('Failed to submit form', e)


# There is some issue with mesop serialization. Instead we use raw string
# in the server state and interpret it as needed.
def form_state_to_string(form: FormState) -> str:
    form_dict = dataclasses.asdict(form)
    return json.dumps(form_dict)
