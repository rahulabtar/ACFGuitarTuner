from model.tuner import Tuner
from dial_view import DialView

class DialViewTuner(DialView):
    def __init__(self, dial):
        super().__init__(dial)

    def display(self):
        current_value = self.dial.get_value()
        print(f"Dial Value: {current_value}")