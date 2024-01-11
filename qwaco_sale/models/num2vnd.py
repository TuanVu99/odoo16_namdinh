# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
import math


ones = ["", "một ", "hai ", "ba ", "bốn ", "năm ", "sáu ", "bảy ", "tám ", "chín ", "mười ", "mười một ", "mười hai ",
        "mười ba ", "mười bốn ", "mười lăm ", "mười sáu ", "mười bảy ", "mười tám ", "mười chín "]
twenties = ["", "", "hai mươi ", "ba mươi ", "bốn mươi ", "năm mươi ", "sáu mươi ", "bảy mươi ", "tám mươi ", "chín mươi "]
thousands = ["", "nghìn ", "triệu ", "tỉ ", "nghìn ", "triệu ", "tỉ "]


def num999(n, next):
    c = n % 10  # singles digit
    b = int(((n % 100) - c) / 10)  # tens digit
    a = int(((n % 1000) - (b * 10) - c) / 100)  # hundreds digit
    t = ""
    h = ""
    if a != 0 and b == 0 and c == 0:
        t = ones[a] + "trăm "
    elif a != 0:
        t = ones[a] + "trăm "
    elif a == 0 and b == 0 and c == 0:
        t = ""
    elif a == 0 and next != '':
        t = "không trăm "
    if b == 1:
        h = ones[n % 100]
    if b == 0:
        if a > 0 and c > 0:
            h = "linh " + ones[n % 100]
        else:
            h = ones[n % 100]
    elif b > 1:
        if c == 4:
            tmp = "tư "
        elif c == 1:
            tmp = "mốt "
        else:
            tmp = ones[c]
        h = twenties[b] + tmp
    st = t + h
    return st


def num2word(num):
    try:
        num = math.ceil(num)
    except:
        raise ValidationError("Number to convert to words must be numeric")
    if num == 0: return 'Không'
    is_neg = False
    if num < 0:
        is_neg = True
        num = abs(num)
    i = 3
    n = str(num)
    word = ""
    k = 0
    while i == 3:
        nw = n[-i:]
        n = n[:-i]
        int_nw = int(float(nw))
        if int_nw == 0:
            word = num999(int_nw, n) + thousands[int_nw] + word
        else:
            word = num999(int_nw, n) + thousands[k] + word
        if n == '':
            i += 1
        k += 1
    if is_neg:
        return ('Âm ' + word[:-1]).capitalize()
    return word[:-1].capitalize()
