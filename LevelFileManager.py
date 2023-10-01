import yaml

class LevelFileManager:

    PATH = "levels/beat_levels.yaml"
    BEAT = {}

    @staticmethod
    def init():
        with open(LevelFileManager.PATH, "r") as f:
            LevelFileManager.BEAT = yaml.safe_load(f)

    @staticmethod
    def beat_level(number):
        LevelFileManager.BEAT[number]=True
        LevelFileManager.save()

    @staticmethod
    def save():
        with open(LevelFileManager.PATH, "w") as f:
            yaml.safe_dump(LevelFileManager.BEAT, f)

    @staticmethod
    def level_has_been_beat(number):
        if number not in LevelFileManager.BEAT:
            return False
        return LevelFileManager.BEAT[number]
