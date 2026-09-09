from abc import ABC, abstractmethod

class BaseIngestionStrategy(ABC):
    
    @abstractmethod
    def process(self, raw_data: dict) -> None:
        pass