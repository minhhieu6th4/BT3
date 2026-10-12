# Harmless upload fixture; not executed by the submission API.
class Bot:
    def get_move(self, state):
        return {"from": [0, 1], "to": [1, 1]}
