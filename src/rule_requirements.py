class RuleRequirement:
    """
    Describes a specification required by an analysis rule.
    """

    def __init__(
        self,
        specification,
        description,
        required=True,
    ):
        self.specification = specification
        self.description = description
        self.required = required

    def to_dict(self):
        return {
            "specification": self.specification,
            "description": self.description,
            "required": self.required,
        }


class RuleRequirements:
    """
    Stores the specification requirements for one rule.
    """

    def __init__(self, rule_id):
        self.rule_id = rule_id
        self.requirements = []

    def add(
        self,
        specification,
        description,
        required=True,
    ):
        requirement = RuleRequirement(
            specification,
            description,
            required,
        )

        self.requirements.append(
            requirement
        )

    def get_all(self):
        return self.requirements

    def get_required(self):
        return [
            requirement
            for requirement in self.requirements
            if requirement.required
        ]

    def get_optional(self):
        return [
            requirement
            for requirement in self.requirements
            if not requirement.required
        ]

    def check_component(
        self,
        model,
        reference,
    ):
        """
        Check which specifications are available
        and which required or optional specifications
        are missing.
        """

        specifications = (
            model.get_component_specifications(
                reference
            )
        )

        available = []
        missing_required = []
        missing_optional = []

        for requirement in self.requirements:
            specification = requirement.specification

            if specification in specifications:
                available.append(
                    specification
                )

            elif requirement.required:
                missing_required.append(
                    specification
                )

            else:
                missing_optional.append(
                    specification
                )

        return {
            "reference": reference,
            "available": available,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
        }

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "requirements": [
                requirement.to_dict()
                for requirement in self.requirements
            ],
        }