class KnowledgeManager:
    def __init__(self):
        self.knowledge = ""

    def add_knowledge(self, text: str):
        self.knowledge += text + "\n"

    def get_knowledge(self) -> str:
        return self.knowledge