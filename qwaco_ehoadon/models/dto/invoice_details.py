import json


class InvoiceDetailsDTO:
    def __init__(
        self,
        ItemTypeID=None,
        ItemName=None,
        UnitName=None,
        Qty=None,
        Price=None,
        Amount=None,
        DiscountRate=None,
        DiscountAmount=None,
        TaxRateID=None,
        TaxRate=None,
        TaxAmount=None,
        IsDiscount=None,
        IsIncrease=None
    ):
        self.ItemTypeID = ItemTypeID
        self.ItemName = ItemName
        self.UnitName = UnitName
        self.Qty = Qty
        self.Price = Price
        self.Amount = Amount
        self.DiscountRate = DiscountRate
        self.DiscountAmount = DiscountAmount
        self.TaxRateID = TaxRateID
        self.TaxRate = TaxRate
        self.TaxAmount = TaxAmount
        self.IsDiscount = IsDiscount
        if IsIncrease == False or IsIncrease == True:
            self.IsIncrease = IsIncrease

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        json_dict = json.loads(json_str)
        return cls(**json_dict)