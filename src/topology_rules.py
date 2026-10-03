from analysis_result import AnalysisResult


def check_net_connectivity(model):
    """
    Check whether expected component pins are connected
    to a net.
    """
    results = []

    for component in model.components:
        reference = component.get("reference", "Unknown")

        unconnected_pins = model.get_unconnected_pins(
            reference
        )

        for pin in unconnected_pins:
            results.append(
                AnalysisResult(
                    "NET_001",
                    "warning",
                    reference,
                    (
                        f"Component {reference} has "
                        f"unconnected pin {pin}."
                    ),
                    (
                        "Connect the pin to the intended "
                        "net or verify that the connection "
                        "is intentionally left unused."
                    ),
                )
            )

    return results
