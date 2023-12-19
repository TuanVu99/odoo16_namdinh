import json


class InvoiceDTO:
    def __init__(
        self,
        InvoiceTypeID=None,
        InvoiceDate=None,
        BuyerName=None,
        BuyerTaxCode=None,
        BuyerUnitName=None,
        BuyerAddress=None,
        BuyerBankAccount=None,
        PayMethodID=None,
        ReceiveTypeID=None,
        ReceiverEmail=None,
        ReceiverMobile=None,
        ReceiverAddress=None,
        ReceiverName=None,
        Note=None,
        BillCode=None,
        CurrencyID=None,
        ExchangeRate=None,
        InvoiceForm=None,
        InvoiceSerial=None,
        InvoiceNo=None,
        UserDefine=None,
        OriginalInvoiceIdentify=None
    ):
        self.InvoiceTypeID = InvoiceTypeID
        self.InvoiceDate = InvoiceDate
        self.BuyerName = BuyerName
        self.BuyerTaxCode = BuyerTaxCode
        self.BuyerUnitName = BuyerUnitName
        self.BuyerAddress = BuyerAddress
        self.BuyerBankAccount = BuyerBankAccount
        self.PayMethodID = PayMethodID
        self.ReceiveTypeID = ReceiveTypeID
        self.ReceiverEmail = ReceiverEmail
        self.ReceiverMobile = ReceiverMobile
        self.ReceiverAddress = ReceiverAddress
        self.ReceiverName = ReceiverName
        self.Note = Note
        self.BillCode = BillCode
        self.CurrencyID = CurrencyID
        self.ExchangeRate = ExchangeRate
        self.InvoiceForm = InvoiceForm
        self.InvoiceSerial = InvoiceSerial
        self.InvoiceNo = InvoiceNo
        if UserDefine:
            self.UserDefine = UserDefine
        if OriginalInvoiceIdentify:
            self.OriginalInvoiceIdentify = OriginalInvoiceIdentify

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        json_dict = json.loads(json_str)
        return cls(**json_dict)