from rule_requirements import RuleRequirements


LED_001_REQUIREMENTS = RuleRequirements(
    "LED_001"
)

LED_001_REQUIREMENTS.add(
    "supply_voltage",
    "Voltage supplied to the LED-resistor circuit."
)

LED_001_REQUIREMENTS.add(
    "forward_voltage",
    "LED forward voltage."
)

LED_001_REQUIREMENTS.add(
    "resistance",
    "Series resistance limiting LED current."
)

LED_001_REQUIREMENTS.add(
    "forward_current",
    "LED rated forward current.",
    required=False
)


RES_001_REQUIREMENTS = RuleRequirements(
    "RES_001"
)

RES_001_REQUIREMENTS.add(
    "resistance",
    "Resistor resistance."
)

RES_001_REQUIREMENTS.add(
    "power_rating",
    "Resistor rated power."
)


RES_002_REQUIREMENTS = RuleRequirements(
    "RES_002"
)

RES_002_REQUIREMENTS.add(
    "resistance",
    "Resistor resistance."
)