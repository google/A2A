class NotesManager:
    def __init__(self):
        self.notes = []

    def add_note(self, text: str):
        self.notes.append(text)

    def get_notes(self) -> str:
        return "\n".join(self.notes)