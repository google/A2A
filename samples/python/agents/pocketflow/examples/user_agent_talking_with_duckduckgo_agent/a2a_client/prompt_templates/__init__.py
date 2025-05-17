import os

from jinja2 import Environment, FileSystemLoader


dir_path = os.path.dirname(os.path.realpath(__file__))

env = Environment(loader=FileSystemLoader(dir_path))

available_agents_template = env.get_template('available_agents_prompt.jinja')
agent_selector_template = env.get_template('agent_selector.jinja')
action_template = env.get_template('action.jinja')
answer_question_with_no_context_template = env.get_template(
    'answer_question_with_no_context.jinja'
)
agent_context_template = env.get_template('agent_context.jinja')

if __name__ == '__main__':
    available_agents_prompt = available_agents_template.render(
        agents=[
            {
                'name': 'Agent 1',
                'description': 'Agent 1 description',
                'skills': [
                    {
                        'name': 'Skill 1',
                        'description': 'Skill 1 description',
                        'examples': ['Example 1', 'Example 2'],
                    }
                ],
            },
            {
                'name': 'Agent 2',
                'description': 'Agent 2 description',
                'skills': [
                    {
                        'name': 'Skill 2',
                        'description': 'Skill 2 description',
                        'examples': ['Example 3', 'Example 4'],
                    }
                ],
            },
        ]
    )

    prompt = agent_selector_template.render(
        question='How is Thai stock market this week?',
        available_agents_prompt=available_agents_prompt,
    )

    print(prompt)

    agent_context_prompt = agent_context_template.render(
        agent_contexts=[
            {
                'agent_name': 'Agent 1',
                'agent_skills': [
                    {
                        'name': 'Skill 1',
                        'description': 'Skill 1 description',
                        'examples': ['Example 1', 'Example 2'],
                    }
                ],
                'question': 'How is Thai stock market this week?',
                'answer': 'Thai stock market is doing well this week',
            }
        ]
    )

    print(agent_context_prompt)

    action_prompt = action_template.render(
        question='How is Thai stock market this week?',
        context=agent_context_prompt,
    )

    print(action_prompt)
