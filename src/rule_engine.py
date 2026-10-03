from component_classifier import classify_component_with_support


class RuleEngine:
    """
    Central engine for running CircuitSense analysis rules.

    Each registered rule is a callable that receives a
    CircuitModel and returns a list of AnalysisResult objects.

    Rules may optionally declare which component families
    they apply to. This allows the engine to skip rules
    that are not relevant to a circuit.
    """

    def __init__(self):
        self.rules = []

    def register_rule(
        self,
        rule,
        rule_id=None,
        name=None,
        applies_to=None,
    ):
        """
        Register an analysis rule.

        Args:
            rule:
                Callable that receives a CircuitModel.

            rule_id:
                Optional identifier such as 'RES_002'.

            name:
                Optional human-readable rule name.

            applies_to:
                Optional component family or list of component
                families that this rule applies to.

                Examples:
                    "resistor"
                    ["led", "resistor"]

                If None, the rule is considered general and
                is always executed.
        """

        if not callable(rule):
            raise TypeError(
                "Rule must be callable."
            )

        if applies_to is None:
            applicable_types = None

        elif isinstance(applies_to, str):
            applicable_types = [applies_to]

        else:
            applicable_types = list(applies_to)

        rule_info = {
            "rule": rule,
            "rule_id": rule_id,
            "name": name or rule.__name__,
            "applies_to": applicable_types,
        }

        self.rules.append(rule_info)

    def _rule_is_applicable(self, rule_info, model):
        """
        Determine whether a rule should run for the
        supplied CircuitModel.

        Rules without an applies_to declaration are
        always applicable.

        Component families are determined through the
        existing CircuitSense component classifier.
        """

        applicable_types = rule_info.get("applies_to")

        if not applicable_types:
            return True

        for component in model.components:
            recognition = classify_component_with_support(
                component
            )

            component_type = recognition.get("type")

            if component_type in applicable_types:
                return True

        return False

    def run(self, model):
        """
        Run all applicable registered rules.

        Each rule receives the CircuitModel and should
        return a list of AnalysisResult objects.
        """

        results = []

        for rule_info in self.rules:

            if not self._rule_is_applicable(
                rule_info,
                model
            ):
                continue

            rule = rule_info["rule"]

            rule_results = rule(model)

            if rule_results is None:
                continue

            results.extend(rule_results)

        return results

    def clear(self):
        """Remove all registered rules."""
        self.rules.clear()

    def count(self):
        """Return the number of registered rules."""
        return len(self.rules)

    def get_rule_info(self):
        """Return metadata for all registered rules."""

        return [
            {
                "rule_id": rule_info["rule_id"],
                "name": rule_info["name"],
                "applies_to": rule_info["applies_to"],
            }
            for rule_info in self.rules
        ]
