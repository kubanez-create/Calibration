# -*- coding: utf-8 -*-
import re

def validate_creating(ans):
    return re.fullmatch(
        (r"^[a-яА-ЯЁё\w.?,!'\s]{1,200};\s+[a-яА-ЯЁё\w]{1,50};\s+[a-яА-ЯЁё\w]{1,30};"
         r"\s[+-]?(\d*\.)?\d+;\s[+-]?(\d*\.)?\d+;\s[+-]?(\d*\.)?\d+;"
         r"\s[+-]?(\d*\.)?\d+$"),
        ans
    )

def validate_updating(ans):
    return re.fullmatch(
        (r"^\d+;\s[+-]?(\d*\.)?\d+;\s[+-]?(\d*\.)?\d+;\s[+-]?(\d*\.)?\d+;"
         r"\s[+-]?(\d*\.)?\d+$"),
        ans
    )
    

def validate_calibration(ans):
    return re.fullmatch(
        r"^[a-яА-ЯЁё\w]{1,50}$",
        ans
    )

def validate_deletion(ans):
    return re.fullmatch(
        r"^\d+$",
        ans
    )

def validate_outcome(ans):
    return re.fullmatch(
        r"^\d+;\s[+-]?(\d*\.)?\d+$",
        ans
    )
