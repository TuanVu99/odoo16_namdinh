import json


class CommandObjectDTO:
    def __init__(
        self,
        Invoice=None,
        ListInvoiceDetailsWS=None,
        ListInvoiceAttachFileWS=None,
        PartnerInvoiceID=None,
        PartnerInvoiceStringID=None,
        InvoiceAction = None
    ):
        self.Invoice = Invoice
        self.ListInvoiceDetailsWS = ListInvoiceDetailsWS
        self.ListInvoiceAttachFileWS = ListInvoiceAttachFileWS
        self.PartnerInvoiceID = PartnerInvoiceID
        self.PartnerInvoiceStringID = PartnerInvoiceStringID
        self.InvoiceAction = InvoiceAction

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        json_dict = json.loads(json_str)
        return cls(**json_dict)