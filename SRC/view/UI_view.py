#TO DO , make UI GUI parts 

from abc import ABC, abstractmethod

class UIView(ABC):
    def __init__(self, UI: ui):
        super().__init__()
        self.ui = ui
    
    @abstractmethod
    
    def display(self):
        pass


if __name__ == "__main__":
    pass