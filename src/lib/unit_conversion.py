from qgis.core import QgsUnitTypes

from ..compat import (
    UNIT_AREA_ACRES,
    UNIT_AREA_HECTARES,
    UNIT_AREA_SQUARE_CENTIMETERS,
    UNIT_AREA_SQUARE_FEET,
    UNIT_AREA_SQUARE_KILOMETERS,
    UNIT_AREA_SQUARE_METERS,
    UNIT_AREA_SQUARE_MILES,
    UNIT_AREA_SQUARE_MILLIMETERS,
    UNIT_AREA_SQUARE_NAUTICAL_MILES,
    UNIT_AREA_SQUARE_YARDS,
    UNIT_DISTANCE_CENTIMETERS,
    UNIT_DISTANCE_FEET,
    UNIT_DISTANCE_KILOMETERS,
    UNIT_DISTANCE_METERS,
    UNIT_DISTANCE_MILES,
    UNIT_DISTANCE_MILLIMETERS,
    UNIT_DISTANCE_NAUTICAL_MILES,
    UNIT_DISTANCE_YARDS,
    UNIT_VOLUME_BARREL,
    UNIT_VOLUME_CUBIC_CENTIMETER,
    UNIT_VOLUME_CUBIC_DECIMETER,
    UNIT_VOLUME_CUBIC_FEET,
    UNIT_VOLUME_CUBIC_INCH,
    UNIT_VOLUME_CUBIC_METERS,
    UNIT_VOLUME_CUBIC_YARDS,
    UNIT_VOLUME_GALLON_US,
    UNIT_VOLUME_LITERS,
)

distance_units = {
    QgsUnitTypes.toString(UNIT_DISTANCE_METERS): UNIT_DISTANCE_METERS,
    QgsUnitTypes.toString(UNIT_DISTANCE_KILOMETERS): UNIT_DISTANCE_KILOMETERS,
    QgsUnitTypes.toString(UNIT_DISTANCE_FEET): UNIT_DISTANCE_FEET,
    QgsUnitTypes.toString(UNIT_DISTANCE_YARDS): UNIT_DISTANCE_YARDS,
    QgsUnitTypes.toString(UNIT_DISTANCE_MILES): UNIT_DISTANCE_MILES,
    QgsUnitTypes.toString(UNIT_DISTANCE_NAUTICAL_MILES): UNIT_DISTANCE_NAUTICAL_MILES,
    QgsUnitTypes.toString(UNIT_DISTANCE_MILLIMETERS): UNIT_DISTANCE_MILLIMETERS,
    QgsUnitTypes.toString(UNIT_DISTANCE_CENTIMETERS): UNIT_DISTANCE_CENTIMETERS,
    # QgsUnitTypes.toString(QgsUnitTypes.Inches): QgsUnitTypes.Inches,
}

area_units = {
    QgsUnitTypes.toString(UNIT_AREA_SQUARE_METERS): UNIT_AREA_SQUARE_METERS,
    QgsUnitTypes.toString(UNIT_AREA_SQUARE_KILOMETERS): UNIT_AREA_SQUARE_KILOMETERS,
    QgsUnitTypes.toString(UNIT_AREA_SQUARE_FEET): UNIT_AREA_SQUARE_FEET,
    QgsUnitTypes.toString(UNIT_AREA_SQUARE_YARDS): UNIT_AREA_SQUARE_YARDS,
    QgsUnitTypes.toString(UNIT_AREA_SQUARE_MILES): UNIT_AREA_SQUARE_MILES,
    QgsUnitTypes.toString(UNIT_AREA_HECTARES): UNIT_AREA_HECTARES,
    QgsUnitTypes.toString(UNIT_AREA_ACRES): UNIT_AREA_ACRES,
    QgsUnitTypes.toString(UNIT_AREA_SQUARE_NAUTICAL_MILES): UNIT_AREA_SQUARE_NAUTICAL_MILES,
    QgsUnitTypes.toString(UNIT_AREA_SQUARE_CENTIMETERS): UNIT_AREA_SQUARE_CENTIMETERS,
    QgsUnitTypes.toString(UNIT_AREA_SQUARE_MILLIMETERS): UNIT_AREA_SQUARE_MILLIMETERS,
}

volume_units = {
    QgsUnitTypes.toString(UNIT_VOLUME_CUBIC_METERS): UNIT_VOLUME_CUBIC_METERS,
    QgsUnitTypes.toString(UNIT_VOLUME_CUBIC_FEET): UNIT_VOLUME_CUBIC_FEET,
    QgsUnitTypes.toString(UNIT_VOLUME_CUBIC_YARDS): UNIT_VOLUME_CUBIC_YARDS,
    QgsUnitTypes.toString(UNIT_VOLUME_BARREL): UNIT_VOLUME_BARREL,
    QgsUnitTypes.toString(UNIT_VOLUME_CUBIC_DECIMETER): UNIT_VOLUME_CUBIC_DECIMETER,
    QgsUnitTypes.toString(UNIT_VOLUME_LITERS): UNIT_VOLUME_LITERS,
    QgsUnitTypes.toString(UNIT_VOLUME_GALLON_US): UNIT_VOLUME_GALLON_US,
    QgsUnitTypes.toString(UNIT_VOLUME_CUBIC_INCH): UNIT_VOLUME_CUBIC_INCH,
    QgsUnitTypes.toString(UNIT_VOLUME_CUBIC_CENTIMETER): UNIT_VOLUME_CUBIC_CENTIMETER,
}

ratio_units = {"ratio": 1, "percent": 0.01}

unit_types = {
    "distance": distance_units,
    "area": area_units,
    "volume": volume_units,
    "ratio": ratio_units,
    "count": {"count": 1},
}


def short_unit_name(unit: str) -> str:

    if unit in distance_units:
        return QgsUnitTypes.toAbbreviatedString(distance_units[unit])
    if unit in area_units:
        return QgsUnitTypes.toAbbreviatedString(area_units[unit])
    if unit in volume_units:
        return QgsUnitTypes.toAbbreviatedString(volume_units[unit])
    if unit in ratio_units:
        if unit == "ratio":
            return "ratio"
        if unit == "percent":
            return "%"
    if unit == "count":
        return "#"
    return unit


# subclass of QgsUnitTypes for ratios
class RatioUnit(QgsUnitTypes):
    Ratio = 0

    @classmethod
    def toString(cls, unit: int) -> str:
        if unit == cls.Ratio:
            return "ratio"
        return super().toString(unit)

    @classmethod
    def fromString(cls, unit: str) -> int:
        if unit == "ratio":
            return cls.Ratio
        return super().fromString(unit)

    @classmethod
    def fromUnitToUnitFactor(cls, fromUnit: int, toUnit: int) -> float:
        if fromUnit == cls.Ratio and toUnit == cls.Ratio:
            return 1
        return super().fromUnitToUnitFactor(fromUnit, toUnit)

    @classmethod
    def fromUnitToUnit(cls, value: float, fromUnit: int, toUnit: int) -> float:
        if fromUnit == cls.Ratio and toUnit == cls.Ratio:
            return value
        return super().fromUnitToUnit(value, fromUnit, toUnit)

    @classmethod
    def fromStringToUnit(cls, value: float, unit: str) -> float:
        if unit == "ratio":
            return value
        return super().fromStringToUnit(value, unit)

    @classmethod
    def toStringFromUnit(cls, value: float, unit: int) -> str:
        if unit == cls.Ratio:
            return "ratio"
        return super().toStringFromUnit(value, unit)


def convert_units(value: float, from_unit: str, to_unit: str, invert: bool = False) -> float:
    if value is None:
        return None

    if from_unit == to_unit:
        return value

    # check if they are ratios first
    if from_unit in ratio_units and to_unit in ratio_units:
        # Source * (SourceFactor / TargetFactor)
        conversion_factor = ratio_units[from_unit] / ratio_units[to_unit]
        if invert:
            conversion_factor = 1 / conversion_factor
        return value * conversion_factor

    # get the base unit type from
    if from_unit in distance_units:
        from_unit_type = distance_units[from_unit]
    elif from_unit in area_units:
        from_unit_type = area_units[from_unit]
    elif from_unit in volume_units:
        from_unit_type = volume_units[from_unit]
    else:
        raise ValueError(f"Unknown unit type: {from_unit}")

    if to_unit in distance_units:
        to_unit_type = distance_units[to_unit]
    elif to_unit in area_units:
        to_unit_type = area_units[to_unit]
    elif to_unit in volume_units:
        to_unit_type = volume_units[to_unit]
    else:
        raise ValueError(f"Unknown unit type: {to_unit}")

    # get conversion factor
    conversion_factor = QgsUnitTypes.fromUnitToUnitFactor(from_unit_type, to_unit_type)
    if invert:
        conversion_factor = 1 / conversion_factor

    return value * conversion_factor


# --- Compound unit conversion helpers ---
def convert_count_per_length(value, from_length_unit, to_length_unit):
    """
    Converts a metric in count/from_length_unit to count/to_length_unit.
    Example: count/meter to count/mile.
    """
    if value is None or from_length_unit == to_length_unit:
        return value
    from_type = distance_units[from_length_unit]
    to_type = distance_units[to_length_unit]
    # factor = how many from_length_unit in one to_length_unit
    factor = QgsUnitTypes.fromUnitToUnitFactor(from_type, to_type)
    return value / factor


def convert_count_per_area(value, from_area_unit, to_area_unit):
    """
    Converts a metric in count/from_area_unit to count/to_area_unit.
    Example: count/m² to count/acre.
    """
    if value is None or from_area_unit == to_area_unit:
        return value
    from_type = area_units[from_area_unit]
    to_type = area_units[to_area_unit]
    # factor = how many from_area_unit in one to_area_unit
    factor = QgsUnitTypes.fromUnitToUnitFactor(from_type, to_type)
    return value / factor
