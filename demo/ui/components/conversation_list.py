import mesop as me
from mesop import SelectOption
import pandas as pd
from typing import List
import uuid

from state.state import AppState
from state.state import StateConversation
from state.host_agent_service import CreateConversation
from state.host_agent_service import ListRemoteAgents

@me.page(
    path="/select_agent",
    title="Select Remote Agent",
)
async def select_agent_page():
    """Page to pick a remote agent."""
    app_state = me.state(AppState)

    remote_agents = await ListRemoteAgents()

    if not remote_agents:
        me.text("No remote agents registered yet.")
        return

    me.text("Pick a Remote Agent to start a conversation:")

    for agent in remote_agents:
        me.content_button(
            label=agent.name,
            type="raised",
            on_click=lambda e, url=agent.url: start_conversation(url),
            style=me.Style(margin=me.Margin(bottom=10)),
        )

async def start_conversation(agent_url: str):
    """Start a conversation with the selected agent."""
    app_state = me.state(AppState)

    new_id = str(uuid.uuid4())
    conversation = StateConversation(
        conversation_id=new_id,
        conversation_name="Remote Conversation",
        is_active=True,
        message_ids=[],
        remote_agent_url=agent_url,
    )

    app_state.conversations.append(conversation)
    app_state.messages = []
    me.navigate("/conversation", query_params={"conversation_id": conversation.conversation_id})
    yield

@me.component
def conversation_list(conversations: List[StateConversation]):
    """Conversation list component"""
    df_data = {"ID": [], "Name": [], "Status": [], "Messages": []}
    for conversation in conversations:
        df_data["ID"].append(conversation.conversation_id)
        df_data["Name"].append(conversation.conversation_name)
        df_data["Status"].append("Open" if conversation.is_active else "Closed")
        df_data["Messages"].append(len(conversation.message_ids))
    df = pd.DataFrame(
        pd.DataFrame(df_data),
        columns=["ID", "Name", "Status", "Messages"])
    with me.box(
        style=me.Style(
            display="flex",
            justify_content="space-between",
            flex_direction="column",
        )
    ):
        me.table(
          df,
          on_click=on_click,
          header=me.TableHeader(sticky=True),
          columns={
            "ID": me.TableColumn(sticky=True),
            "Name": me.TableColumn(sticky=True),
            "Status": me.TableColumn(sticky=True),
            "Messages": me.TableColumn(sticky=True),
          },
        )
        with me.content_button(
            type="raised",
            on_click=add_conversation,
            key="new_conversation",
            style=me.Style(
                display="flex",
                flex_direction="row",
                gap=5,
                align_items="center",
                margin=me.Margin(top=10),
            ),
        ):
            me.icon(icon="add")

async def CreateRemoteConversation(agent_url: str) -> StateConversation:
    """Manually create a remote conversation locally."""
    new_id = str(uuid.uuid4())
    conversation = StateConversation(
        conversation_id=new_id,
        conversation_name="Remote Agent Conversation",
        is_active=True,
        message_ids=[],
        remote_agent_url=agent_url  # <-- important!
    )
    app_state = me.state(AppState)
    app_state.conversations.append(conversation)
    return conversation


async def add_conversation(e: me.ClickEvent):
    """Immediately create a new conversation when + is clicked."""
    app_state = me.state(AppState)

    # 🛠️ FIRST: create a server-side conversation
    server_conversation = await CreateConversation()

    if not server_conversation:
        print("[ERROR] Failed to create server-side conversation")
        return

    # 🛠️ NEXT: pick a remote agent immediately
    from state.host_agent_service import pick_agent_using_chatgpt
    remote_agent_url = await pick_agent_using_chatgpt("default")  # You can pass any default string here

    if not remote_agent_url:
        print("[ERROR] No remote agent available! Falling back to None.")
        remote_agent_url = None

    # 🛠️ THEN: create the local Mesop state
    new_conversation = StateConversation(
        conversation_id=server_conversation.conversation_id,
        conversation_name=server_conversation.name or "Remote Conversation",
        is_active=True,
        message_ids=[],
        remote_agent_url=remote_agent_url,  # ✅ NOW SET REMOTE AGENT URL!
    )

    app_state.conversations.append(new_conversation)
    app_state.messages = []

    me.navigate("/conversation", query_params={"conversation_id": new_conversation.conversation_id})
    yield

def on_click(e: me.TableClickEvent):
  state = me.state(AppState)
  conversation = state.conversations[e.row_index]
  state.current_conversation_id = conversation.conversation_id
  me.query_params.update({"conversation_id": conversation.conversation_id})
  me.navigate("/conversation", query_params=me.query_params)
  yield
