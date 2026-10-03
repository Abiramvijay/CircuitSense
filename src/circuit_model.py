from specification_extractor import extract_specifications


class CircuitModel:
    """
    General representation of a KiCad circuit.

    This model organizes:
    - Components
    - Nets
    - Component-to-net relationships
    - Component-to-component relationships
    - Component specifications

    It does not perform electrical analysis.
    """

    def __init__(self, circuit):
        self.components = circuit.get("components", [])
        self.nets = circuit.get("nets", [])

        self.component_map = {}
        self.net_map = {}
        self.component_pin_nets = {}
        self.component_specifications = {}

        self._build_model()
        self._extract_specifications()

    def _build_model(self):
        """Build indexed component and net relationships."""

        for component in self.components:
            reference = component.get("reference")

            if reference:
                self.component_map[reference] = component

        for net in self.nets:
            name = net.get("name")

            if name:
                self.net_map[name] = net

        for net in self.nets:
            net_name = net.get("name")

            for node in net.get("nodes", []):
                reference = node.get("reference")
                pin = node.get("pin")

                if not reference or pin is None:
                    continue

                if reference not in self.component_pin_nets:
                    self.component_pin_nets[reference] = {}

                self.component_pin_nets[reference][
                    str(pin)
                ] = net_name

    def _extract_specifications(self):
        """Extract available specifications for every component."""

        for reference, component in self.component_map.items():
            specification_data = extract_specifications(
                component
            )

            self.component_specifications[
                reference
            ] = specification_data.get(
                "specifications",
                {}
            )

    def get_component(self, reference):
        """Return a component by reference."""

        return self.component_map.get(reference)

    def get_net(self, name):
        """Return a net by name."""

        return self.net_map.get(name)

    def get_component_pin_nets(self, reference):
        """Return pin-to-net mapping for a component."""

        return self.component_pin_nets.get(
            reference,
            {}
        )


    def get_unconnected_pins(self, reference):
        """Return expected component pins that are not connected to any net."""
        component = self.get_component(reference)

        if component is None:
            return []

        expected_pins = set(
            str(pin)
            for pin in component.get("pins", [])
        )

        connected_pins = set(
            str(pin)
            for pin in self.get_component_pin_nets(reference)
        )

        return sorted(
            expected_pins - connected_pins,
            key=lambda pin: (
                int(pin) if pin.isdigit() else pin
            )
        )

    def get_component_nets(self, reference):
        """Return all nets connected to a component."""

        return set(
            self.get_component_pin_nets(
                reference
            ).values()
        )

    def get_net_nodes(self, name):
        """Return all nodes belonging to a net."""

        net = self.get_net(name)

        if net is None:
            return []

        return net.get("nodes", [])

    def get_net_connections(self, name):
        """Return component/pin connections on a net."""

        nodes = self.get_net_nodes(name)

        return [
            {
                "reference": node.get("reference"),
                "pin": str(node.get("pin")),
            }
            for node in nodes
            if (
                node.get("reference")
                and node.get("pin") is not None
            )
        ]

    def get_components_on_net(self, name):
        """Return component references connected to a net."""

        connections = self.get_net_connections(name)

        return [
            connection["reference"]
            for connection in connections
        ]

    def get_connected_components(self, reference):
        """
        Return components sharing at least one net
        with the specified component.
        """

        connected = set()

        for net_name in self.get_component_nets(
            reference
        ):
            for other_reference in (
                self.get_components_on_net(net_name)
            ):
                if other_reference != reference:
                    connected.add(other_reference)

        return sorted(connected)

    def get_shared_nets(
        self,
        first_reference,
        second_reference,
    ):
        """
        Return nets shared directly by two components.

        An empty set means the components do not share
        a direct electrical net.
        """

        first_nets = self.get_component_nets(
            first_reference
        )

        second_nets = self.get_component_nets(
            second_reference
        )

        return first_nets & second_nets

    def are_components_directly_connected(
        self,
        first_reference,
        second_reference,
    ):
        """
        Return True when two components share at least
        one electrical net.
        """

        return bool(
            self.get_shared_nets(
                first_reference,
                second_reference,
            )
        )

    def get_connected_components_by_type(
        self,
        reference,
        component_type,
    ):
        """
        Return directly connected components that match
        a specified CircuitSense component family.

        Component recognition is performed using the
        existing component classifier.
        """

        from component_classifier import (
            classify_component_with_support
        )

        connected_references = (
            self.get_connected_components(reference)
        )

        matching = []

        for connected_reference in connected_references:
            component = self.get_component(
                connected_reference
            )

            if component is None:
                continue

            recognition = (
                classify_component_with_support(
                    component
                )
            )

            if recognition.get("type") == component_type:
                matching.append(
                    connected_reference
                )

        return matching

    def get_component_connections(self, reference):
        """
        Return detailed connections for a component.
        """

        connections = []

        pin_nets = self.get_component_pin_nets(
            reference
        )

        for pin, net_name in pin_nets.items():

            nodes = self.get_net_nodes(
                net_name
            )

            for node in nodes:

                other_reference = node.get(
                    "reference"
                )

                other_pin = node.get("pin")

                if other_reference == reference:
                    continue

                connections.append(
                    {
                        "reference": reference,
                        "pin": pin,
                        "net": net_name,
                        "connected_reference":
                            other_reference,
                        "connected_pin":
                            str(other_pin),
                    }
                )

        return connections

    def get_component_specifications(
        self,
        reference,
    ):
        """Return extracted specifications."""

        return self.component_specifications.get(
            reference,
            {}
        )

    def get_component_specification_data(
        self,
        reference,
        specification,
    ):
        """Return complete specification metadata."""

        specifications = (
            self.get_component_specifications(
                reference
            )
        )

        return specifications.get(
            specification
        )

    def get_component_specification(
        self,
        reference,
        specification,
    ):
        """Return only the numeric specification value."""

        specification_data = (
            self.get_component_specification_data(
                reference,
                specification,
            )
        )

        if specification_data is None:
            return None

        return specification_data.get("value")

    def get_component_references(self):
        """Return all component references."""

        return list(
            self.component_map.keys()
        )

    def get_net_names(self):
        """Return all net names."""

        return list(
            self.net_map.keys()
        )

    def summary(self):
        """Return a high-level circuit summary."""

        return {
            "component_count":
                len(self.component_map),

            "net_count":
                len(self.net_map),

            "components":
                self.get_component_references(),

            "nets":
                self.get_net_names(),
        }
