from dataclasses import dataclass
from typing import List, Optional, Union


def _check_is_type(rule_dict, key: str, _type):
    """Check if the key in the rule_dict is of the given type. If not, raise a ValueError."""
    name = rule_dict[key]
    if not isinstance(name, _type):
        _type_name = 'string' if _type is str else _type
        raise ValueError(f'The "{key}" field must be a {_type_name}')
    return name


@dataclass
class Tool:
    """Represents a stego tool."""

    name: str
    """The name of the tool."""

    desc: Optional[str]
    """The description of the tool."""
    tags: List[str]
    """The tags of the tool like "App", "CLI", "LSB", etc."""

    version: Optional[str] = None
    """The version of the tool."""

    @staticmethod
    def from_dict(technique_dict):
        """Create a Tool object from a dictionary."""

        if 'name' not in technique_dict:
            raise ValueError('Missing "name" field (the name of the tool)')
        else:
            name = _check_is_type(technique_dict, 'name', str)

        desc = _check_is_type(technique_dict, 'desc', str) if 'desc' in technique_dict else None

        if 'tags' not in technique_dict:
            raise ValueError('Missing "tags" field (the tags of the tool like "tool", "cli", "mobile", etc.)')
        else:
            tags = _check_is_type(technique_dict, 'tags', list)

        version = _check_is_type(technique_dict, 'version', str) if 'version' in technique_dict else None

        return Tool(name, desc, tags, version)


@dataclass
class Matcher:
    """Represents a match expression that is split into a value to be evaluated and a condition to be checked."""

    value: str
    """The value to be evaluated."""

    cond: str
    """The condition to check the value against."""

    def __str__(self):
        return self.cond + ' with value = ' + self.value

    @staticmethod
    def from_dict(match_dict) -> Union[str, 'Matcher']:
        """Create a Matcher object from a dictionary."""

        if isinstance(match_dict, str):
            return match_dict
        elif isinstance(match_dict, dict):
            return Matcher(match_dict['value'], match_dict['cond'])
        else:
            raise ValueError(f'Not a valid expression or dictionary: {match_dict}')


@dataclass
class MatchedTool:
    """Represents a tool that can be matched by a rule."""

    name: str
    """The name of the tool."""

    weight: int
    """The weight of this match for the evidence of this tool being used in the image."""

    @staticmethod
    def from_dict(tech_dict):
        """Create a MatchedTool object from a dictionary."""

        if 'name' not in tech_dict:
            raise ValueError('Missing "name" field (the name of the tool as defined in the techniques section)')
        else:
            name = _check_is_type(tech_dict, 'name', str)

        if 'weight' not in tech_dict:
            raise ValueError('Missing "weight" field (the weight of this match for the evidence of this tool '
                             'being used in the image)')
        else:
            weight = _check_is_type(tech_dict, 'weight', int)

        return MatchedTool(name, weight)


@dataclass
class Rule:
    """Represents a rule that can be applied to detect a stego tool in an image."""

    name: str
    """The name of the rule."""

    desc: str
    """The description of the rule."""

    tags: List[str]
    """The tags of the rule."""

    match: str | Matcher
    """The match expression of the rule."""

    tools: List[MatchedTool]
    """The tools that may be identified by this rule."""

    next: Optional[Union['Rule', 'CompoundRule']]
    """The next rule to be applied after this rule."""

    @staticmethod
    def from_dict(rule_dict: dict) -> Union['Rule', 'CompoundRule']:
        """Create a Rule object from a dictionary."""

        if 'operator' in rule_dict and 'rules' in rule_dict:
            return CompoundRule.from_dict(rule_dict)

        if rule_dict is None:
            raise ValueError('Invalid rule dict')

        if 'name' not in rule_dict:
            raise ValueError('Missing "name" field (the name of the rule)')
        else:
            name = _check_is_type(rule_dict, 'name', str)

        if 'desc' not in rule_dict:
            raise ValueError('Missing "desc" field (the description of the rule)')
        else:
            desc = _check_is_type(rule_dict, 'desc', str)

        tags = _check_is_type(rule_dict, 'tags', list) if 'tags' in rule_dict else []

        if 'match' not in rule_dict:
            raise ValueError('Missing "match" field (the match expression of the rule)')
        else:
            match = Matcher.from_dict(rule_dict['match'])

        if 'tools' not in rule_dict:
            raise ValueError('Missing "tools" field (the tools that may be identified by this rule)')
        else:
            tools = [MatchedTool.from_dict(t) for t in rule_dict['tools']]

        _next = Rule.from_dict(rule_dict['next']) if 'next' in rule_dict else None

        return Rule(name, desc, tags, match, tools, _next)


@dataclass
class CompoundRule:
    """Represents a compound rule that will apply to a list of rules according to the operator."""

    name: Optional[str]
    """The name of the rule."""

    desc: Optional[str]
    """The description of the rule."""

    tags: List[str]
    """The tags of the rule."""

    operator: str
    """The operator to apply to the rules (one of "any", "all", "none" or "each").
    
    - "any": At least one rule must match.
    - "all": All rules must match.
    - "none": None of the rules must match.
    - "each": Each rule will be applied whether the previous rule matched or not.
    """

    rules: List[Union['Rule', 'CompoundRule']]
    """The sub-rules of this rule."""

    @staticmethod
    def from_dict(rule_dict) -> 'CompoundRule':
        """Create a CompoundRule object from a dictionary."""

        name = _check_is_type(rule_dict, 'name', str) if 'name' in rule_dict else None
        desc = _check_is_type(rule_dict, 'desc', str) if 'desc' in rule_dict else None
        tags = _check_is_type(rule_dict, 'tags', list) if 'tags' in rule_dict else []

        if 'operator' not in rule_dict:
            raise ValueError('Missing "operator" field (one of "any", "all", "none" or "each")')
        else:
            operator = rule_dict['operator'] if rule_dict['operator'] in ['any', 'all', 'none', 'each'] else None

        if 'rules' not in rule_dict:
            raise ValueError('Missing "rules" field (the sub-rules of this rule)')
        else:
            rules = _check_is_type(rule_dict, 'rules', list)
            rules = [Rule.from_dict(rule) for rule in rules]

        return CompoundRule(name, desc, tags, operator, rules)


@dataclass
class Config:
    """Represents the configuration for the detector."""

    isd: str
    """The identifier and version of the configuration.
    
    `isd` stands for "Image Steganography Detector".
    
    Current versions: "1", "1.0", "1.0.0
    """

    tools: List[Tool]
    """The list of stego tools that can be detected."""

    rules: List[Rule | CompoundRule]
    """The list of rules to be applied to detect stego tools.
    
    This corresponds to a compound rule with the operator "each".    
    """

    @staticmethod
    def from_dict(config_dict):
        """Create a Config object from a dictionary."""

        if "isd" not in config_dict:
            raise ValueError("Missing 'isd' with a version number")

        if config_dict['isd'] not in Config._versions():
            raise ValueError(f"Unsupported version '{config_dict['isd']}'")
        isd = config_dict['isd']

        if "tools" not in config_dict:
            raise ValueError("Missing 'tools'")
        tools = [Tool.from_dict(tech) for tech in config_dict['tools']]

        if "rules" not in config_dict:
            raise ValueError("Missing 'rules'")
        rules = [Rule.from_dict(rule) for rule in config_dict['rules']]

        return Config(isd, tools, rules)

    @staticmethod
    def _versions():
        return ["1", "1.0", "1.0.0"]
