import yaml
import sys



class LevelFileManager:

    PATH = "levels/beat_levels.yaml"
    BEAT = {}
    STORAGE_KEY = "HOPE_FALTERS_COMPLETED_LEVELS"
    INITIALIZED = False


    @staticmethod
    def init():
        if not LevelFileManager.is_web_build():
            with open(LevelFileManager.PATH, "r") as f:
                LevelFileManager.BEAT = yaml.safe_load(f)
        else:
            storage = window.localStorage.getItem(LevelFileManager.STORAGE_KEY)
            if storage:
                try:
                    LevelFileManager.BEAT = yaml.safe_load(storage)
                except:
                    pass
        LevelFileManager.INITIALIZED = True

    @staticmethod
    def beat_level(number):
        LevelFileManager.BEAT[number]=True
        LevelFileManager.save()

    @staticmethod
    def save():
        if not LevelFileManager.is_web_build():
            with open(LevelFileManager.PATH, "w") as f:
                yaml.safe_dump(LevelFileManager.BEAT, f)
        else:
            storage = yaml.safe_dump(LevelFileManager.BEAT)
            window.localStorage.setItem(LevelFileManager.STORAGE_KEY, storage)

    @staticmethod
    def level_has_been_beat(number):
        if number not in LevelFileManager.BEAT:
            return False
        return LevelFileManager.BEAT[number]

    @staticmethod
    def is_web_build():
        return sys.platform == "emscripten"


if LevelFileManager.is_web_build():
    from platform import window