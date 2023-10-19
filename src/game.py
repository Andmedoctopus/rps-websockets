from collections import defaultdict

class BaseGameElement:
    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return True
        return False


class Scissors(BaseGameElement):
    def __gt__(self, other):
        if isinstance(other, Paper):
            return True
        if isinstance(other, Rock) or isinstance(other, Scissors):
            return False
        raise NotImplemented(f"Can't compare Scissors with {other}")


class Rock(BaseGameElement):
    def __gt__(self, other):
        if isinstance(other, Scissors):
            return True
        if isinstance(other, Paper) or isinstance(other, Rock):
            return False
        raise NotImplemented(f"Can't compare Rock with {other}")


class Paper(BaseGameElement):
    def __gt__(self, other) -> bool:
        if isinstance(other, Rock):
            return True
        if isinstance(other, Scissors) or isinstance(other, Paper):
            return False
        raise NotImplemented(f"Can't compare Paper with {other}")


class Game:
    def beat(self, c1: str, c2: str) -> bool:
        selector = {"scissors": Scissors, "rock": Rock, "paper": Paper}
        choice1 = selector[c1.lower()]()
        choice2 = selector[c2.lower()]()
        return choice1 > choice2
