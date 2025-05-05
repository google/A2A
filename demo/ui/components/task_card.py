import json

import mesop as me
import pandas as pd

from state.state import ContentPart, SessionTask, StateTask


def message_string(content: ContentPart) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content)


@me.component
def task_card(tasks: list[SessionTask]):
    """Task card component"""
    columns = ['Conversation ID', 'Task ID', 'Description', 'Status', 'Output']
    df_data = {c: [] for c in columns}
    for task in tasks:
        df_data['Conversation ID'].append(task.session_id)
        df_data['Task ID'].append(task.task.task_id)
        df_data['Description'].append(
            '\n'.join(message_string(x[0]) for x in task.task.message.content)
        )
        df_data['Status'].append(task.task.state)
        df_data['Output'].append(flatten_artifacts(task.task))
    df = pd.DataFrame(pd.DataFrame(df_data), columns=columns)
    with me.box(
        style=me.Style(
            display='flex',
            justify_content='space-between',
        )
    ):
        me.table(
            df,
            header=me.TableHeader(sticky=True),
            columns={c: me.TableColumn(sticky=True) for c in columns},
        )


def flatten_artifacts(task: StateTask) -> str:
    parts = []
    for a in task.artifacts:
        for p in a:
            if p[1] == 'text/plain' or p[1] == 'application/json':
                parts.append(message_string(p[0]))
            else:
                parts.append(p[1])

    return '\n'.join(parts)
