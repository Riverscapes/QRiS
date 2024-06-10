from qgis.core import QgsUnitTypes

distance_units ={
    QgsUnitTypes.toString(QgsUnitTypes.DistanceMeters): QgsUnitTypes.DistanceMeters,
    QgsUnitTypes.toString(QgsUnitTypes.DistanceKilometers): QgsUnitTypes.DistanceKilometers,
    QgsUnitTypes.toString(QgsUnitTypes.DistanceFeet): QgsUnitTypes.DistanceFeet,
    QgsUnitTypes.toString(QgsUnitTypes.DistanceYards): QgsUnitTypes.DistanceYards,
    QgsUnitTypes.toString(QgsUnitTypes.DistanceMiles): QgsUnitTypes.DistanceMiles,
    QgsUnitTypes.toString(QgsUnitTypes.DistanceNauticalMiles): QgsUnitTypes.DistanceNauticalMiles,
    QgsUnitTypes.toString(QgsUnitTypes.DistanceMillimeters): QgsUnitTypes.DistanceMillimeters,
    QgsUnitTypes.toString(QgsUnitTypes.DistanceCentimeters): QgsUnitTypes.DistanceCentimeters,
    # QgsUnitTypes.toString(QgsUnitTypes.Inches): QgsUnitTypes.Inches,
}

area_units = {
    QgsUnitTypes.toString(QgsUnitTypes.AreaSquareMeters): QgsUnitTypes.AreaSquareMeters,
    QgsUnitTypes.toString(QgsUnitTypes.AreaSquareKilometers): QgsUnitTypes.AreaSquareKilometers,
    QgsUnitTypes.toString(QgsUnitTypes.AreaSquareFeet): QgsUnitTypes.AreaSquareFeet,
    QgsUnitTypes.toString(QgsUnitTypes.AreaSquareYards): QgsUnitTypes.AreaSquareYards,
    QgsUnitTypes.toString(QgsUnitTypes.AreaSquareMiles): QgsUnitTypes.AreaSquareMiles,
    QgsUnitTypes.toString(QgsUnitTypes.AreaHectares): QgsUnitTypes.AreaHectares,
    QgsUnitTypes.toString(QgsUnitTypes.AreaAcres): QgsUnitTypes.AreaAcres,
    QgsUnitTypes.toString(QgsUnitTypes.AreaSquareNauticalMiles): QgsUnitTypes.AreaSquareNauticalMiles,
    QgsUnitTypes.toString(QgsUnitTypes.AreaSquareCentimeters): QgsUnitTypes.AreaSquareCentimeters,
    QgsUnitTypes.toString(QgsUnitTypes.AreaSquareMillimeters): QgsUnitTypes.AreaSquareMillimeters,
}

volume_units = {
    QgsUnitTypes.toString(QgsUnitTypes.VolumeCubicMeters): QgsUnitTypes.VolumeCubicMeters,
    QgsUnitTypes.toString(QgsUnitTypes.VolumeCubicFeet): QgsUnitTypes.VolumeCubicFeet,
    QgsUnitTypes.toString(QgsUnitTypes.VolumeCubicYards): QgsUnitTypes.VolumeCubicYards,
    QgsUnitTypes.toString(QgsUnitTypes.VolumeBarrel): QgsUnitTypes.VolumeBarrel,
    QgsUnitTypes.toString(QgsUnitTypes.VolumeCubicDecimeter): QgsUnitTypes.VolumeCubicDecimeter,
    QgsUnitTypes.toString(QgsUnitTypes.VolumeLiters): QgsUnitTypes.VolumeLiters,
    QgsUnitTypes.toString(QgsUnitTypes.VolumeGallonUS): QgsUnitTypes.VolumeGallonUS,
    QgsUnitTypes.toString(QgsUnitTypes.VolumeCubicInch): QgsUnitTypes.VolumeCubicInch,
    QgsUnitTypes.toString(QgsUnitTypes.VolumeCubicCentimeter): QgsUnitTypes.VolumeCubicCentimeter,
}

ratio_units = {
    "ratio": 1,
    "percent": .01
}

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
    if from_unit == to_unit:
        return value
    
    # check if they are ratios first
    if from_unit in ratio_units and to_unit in ratio_units:
        conversion_factor = ratio_units[from_unit] * ratio_units[to_unit]
        if invert:
            conversion_factor = 1 / conversion_factor
        return value / conversion_factor

    # get the base unit type from 
    if from_unit in distance_units:
        from_unit_type = distance_units[from_unit]
    elif from_unit in area_units:
        from_unit_type = area_units[from_unit]
    elif from_unit in volume_units:
        from_unit_type = volume_units[from_unit]
    else:
        raise ValueError(f'Unknown unit type: {from_unit}')
    
    if to_unit in distance_units:
        to_unit_type = distance_units[to_unit]
    elif to_unit in area_units:
        to_unit_type = area_units[to_unit]
    elif to_unit in volume_units:
        to_unit_type = volume_units[to_unit]
    else:
        raise ValueError(f'Unknown unit type: {to_unit}')
    
    # get conversion factor
    conversion_factor = QgsUnitTypes.fromUnitToUnitFactor(from_unit_type, to_unit_type)
    if invert:
        conversion_factor = 1 / conversion_factor

    return value / conversion_factor
