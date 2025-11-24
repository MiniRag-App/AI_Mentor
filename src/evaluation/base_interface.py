from abc import ABC,abstractmethod


class BaseEvaluator(ABC):

    @abstractmethod
    def evaluate(self, queries,groud_truth):
        pass

    @abstractmethod
    def generate_report(self):
        pass