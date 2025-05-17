from pocketflow import Flow

from .nodes import AnswerQuestion, DecideAction, SearchWeb


def create_agent_flow():
    """Create and connect the nodes to form a complete agent flow.

    The flow works like this:
    1. DecideAction node decides whether to search or answer
    2. If search, go to SearchWeb node
    3. If answer, go to AnswerQuestion node
    4. After SearchWeb completes, go back to DecideAction

    Returns:
        Flow: A complete research agent flow
    """
    # Create instances of each node
    decide = DecideAction()
    search = SearchWeb()
    answer = AnswerQuestion()

    # Connect the nodes
    # If DecideAction returns "search", go to SearchWeb
    decide - 'search' >> search

    # If DecideAction returns "answer", go to AnswerQuestion
    decide - 'answer' >> answer

    # After SearchWeb completes and returns "decide", go back to DecideAction
    search - 'decide' >> decide

    # Create and return the flow, starting with the DecideAction node
    return Flow(start=decide)
