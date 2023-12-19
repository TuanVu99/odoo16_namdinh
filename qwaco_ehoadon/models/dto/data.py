import json


class DataDTO:
    def __init__(
        self,
        CmdType=None,
        CommandObject=None,
    ):
        self.CmdType = CmdType
        self.CommandObject = CommandObject

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        json_dict = json.loads(json_str)
        return cls(**json_dict)