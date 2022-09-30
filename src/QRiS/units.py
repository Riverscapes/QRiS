from math import pow
from typing import Union
from scipy import constants


# https://docs.scipy.org/doc/scipy/reference/constants.html?highlight=length

LENGTHS = {
    'inch': ('Inch', 'in', constants.inch),
    'meter': ('Meter', 'm', 1.0),
    'foot': ('Foot', 'ft', constants.foot),
    'yard': ('Yard', 'yd', constants.yard),
    'mile': ('Mile', 'mi', constants.mile),
    'survey_foot': ('Survey Foot', 'usft', constants.survey_foot),
}

AREAS = {
    'square_meter': ('Square Meter', 'sqm', 1),
    'square_foot': ('Square Foot', 'sqft', pow(constants.foot, 2)),
    'square_yard': ('Square Yard', 'sqyd', pow(constants.yard, 2)),
    'hectare': ('Hectare', 'ha', constants.hectare),
    'acre': ('Acre', 'ac', constants.acre),
}


class Units:

    def __init__(self, length_unit: str, area_unit: str):

        if length_unit not in LENGTHS:
            raise Exception(f'Invalid length unit: {length_unit}')

        if area_unit not in AREAS:
            raise Exception(f'Invalid area unit {area_unit}')

        self.length_unit = length_unit
        self.area_unit = area_unit

    def get_length(self, value_in_metres: Union[float, int], desired_units: str) -> Union[float, int]:
        return value_in_metres / LENGTHS[desired_units][2]

    def get_area(self, value_in_square_metres: Union[float, int], desired_units: str) -> Union[float, int]:
        return value_in_square_metres / AREAS[desired_units][2]


def get_lengths():
    return {vals[0]: key for key, vals in LENGTHS.items()}


def get_areas():
    return {vals[0]: key for key, vals in AREAS.items()}
