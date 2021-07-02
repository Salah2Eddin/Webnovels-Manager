class NoNovelData(Exception):
    "Raised when no novel data found"
    pass


class MissingNovelData(Exception):
    "Raised when any of the novel's data is missing"
    pass


class NoChapterData(Exception):
    "Raised when chapters data is missing"
    pass


class NoChaptersPaths(Exception):
    "Raised when chapters paths file doesn't exist"
    pass
