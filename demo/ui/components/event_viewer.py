import asyncio

import mesop as me
import pandas as pd

from state.host_agent_service import GetEvents, convert_event_to_state


def flatten_content(content: list[tuple[str, str]]) -> str:
    parts = []
    for p in content:
        if p[1] == 'text/plain' or p[1] == 'application/json':
            parts.append(p[0])
        else:
            parts.append(p[1])

    return '\n'.join(parts)


@me.component
def event_list():
    """Events list component"""
    df_data = {
        'Conversation ID': [],
        'Actor': [],
        'Role': [],
        'Id': [],
        'Content': [],
    }
    events = asyncio.run(GetEvents())
    for e in events:
        event = convert_event_to_state(e)
        df_data['Conversation ID'].append(event.conversation_id)
        df_data['Role'].append(event.role)
        df_data['Id'].append(event.id)
        df_data['Content'].append(flatten_content(event.content))
        df_data['Actor'].append(event.actor)
    if not df_data['Conversation ID']:
        me.text('No events found')
        return
    df = pd.DataFrame(
        pd.DataFrame(df_data),
        columns=['Conversation ID', 'Actor', 'Role', 'Id', 'Content'],
    )
    with me.box(
        style=me.Style(
            display='flex',
            justify_content='space-between',
            flex_direction='column',
        )
    ):
        me.table(
            df,
            header=me.TableHeader(sticky=True),
            columns={
                'Conversation ID': me.TableColumn(sticky=True),
                'Actor': me.TableColumn(sticky=True),
                'Role': me.TableColumn(sticky=True),
                'Id': me.TableColumn(sticky=True),
                'Content': me.TableColumn(sticky=True),
            },
        )
