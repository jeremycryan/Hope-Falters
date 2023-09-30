class WordManager:
    WORDS = set()

    @staticmethod
    def init():
        with open("assets/words_alpha.txt") as f:
            while line := f.readline():
                line = line.strip().upper()
                if len(line) < 3:
                    continue
                if len(line) > 15:
                    continue
                WordManager.WORDS.add(line)

    @staticmethod
    def contains(string):
        return string in WordManager.WORDS