import constants as c


class LevelLoader:
    LEVELS = []


    class Level:
        def __init__(self, title, hint_words, lines):
            self.title = title
            self.hints = hint_words
            self.lines = lines

    @staticmethod
    def init():
        for path in c.LEVELS:
            path = f"levels/{path}"
            with open(path) as f:
                title = f.readline().strip()
                hints = f.readline().strip().split(",")
                hints = [hint.upper() for hint in hints]
                while "NONE" in hints:
                    hints.remove("NONE")
                lines = [line.strip() for line in f.readlines()]
                LevelLoader.LEVELS.append(LevelLoader.Level(title, hints, lines))

    @staticmethod
    def load_level(num):
        level = LevelLoader.LEVELS[num]
        return level.title, level.hints, level.lines
