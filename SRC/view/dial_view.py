## To DO make abstract class 

from abc import ABC, abstractmethod

class DialView(ABC):
    def __init__(self, dial: dial):
        super().__init__()
        self.dial = dial
    
    @abstractmethod

    def display(self):
        pass
