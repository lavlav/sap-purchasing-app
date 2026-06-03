from enum import Enum


class Icons(Enum):
    SAVE = ("Save", "assets/svg/save.svg")
    DELETE = ("Delete", "assets/svg/x.svg")
    DOWNLOAD = ("Download", "assets/svg/download.svg")
    REFRESH = ("Refresh", "assets/svg/refresh-cw.svg")
    TRASH = ("Trash", "assets/svg/trash-2.svg")
    LEFT_ARROW = ("Left Arrow", "assets/svg/arrow-left.svg")
    RIGHT_ARROW = ("Right Arrow", "assets/svg/arrow-right.svg")
    CORNER_RIGHT_UP = ("Corner Right Up", "assets/svg/corner-right-up.svg")
    EDIT = ("Edit", "assets/svg/edit.svg")
    EDIT_PENCIL = ("Edit Pencil", "assets/svg/edit-2.svg")

    def __new__(cls, value, path):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.path = path
        return obj