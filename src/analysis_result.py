
class AnalysisResult:
    def __init__(
        self,
        rule_id,
        severity,
        component,
        message,
        suggestion=None,
        measured=None,
        limit=None
    ):
        self.rule_id = rule_id
        self.severity = severity
        self.component = component
        self.message = message
        self.suggestion = suggestion
        self.measured = measured
        self.limit = limit

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "component": self.component,
            "message": self.message,
            "suggestion": self.suggestion,
            "measured": self.measured,
            "limit": self.limit
        }