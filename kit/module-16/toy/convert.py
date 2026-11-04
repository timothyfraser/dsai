# convert.py
# Unit conversions for a pressure and temperature sensor log.
# Course kit, module 16
#
# This is the toy project the local agent works on. One function has a bug,
# and one test in tests/test_convert.py fails because of it. The agent's job
# is to find it and fix it, editing this file and nothing else.

# 0. SETUP ###################################

# One pound per square inch (psi) is 6.894757 kilopascals (kPa).
KPA_PER_PSI = 6.894757

# 1. PRESSURE ###################################

def psi_to_kpa(psi):
    """Convert a pressure in psi to kPa."""
    return psi / KPA_PER_PSI

def kpa_to_psi(kpa):
    """Convert a pressure in kPa to psi."""
    return kpa / KPA_PER_PSI

# 2. TEMPERATURE ###################################

def celsius_to_kelvin(celsius):
    """Convert a temperature in degrees Celsius to kelvin."""
    return celsius + 273.15
