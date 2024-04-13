from dataclasses import dataclass
from typing import List, Optional, Union


def _check_is_type(rule_dict, key: str, _type):
    name = rule_dict[key]
    if not isinstance(name, _type):
        _type_name = 'string' if _type is str else _type
        raise ValueError(f'The "{key}" field must be a {_type_name}')
    return name


@dataclass
class Tool:
    name: str
    desc: Optional[str]
    tags: List[str]
    version: Optional[str] = None

    @staticmethod
    def from_dict(technique_dict):
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
    value: str
    cond: str

    def __str__(self):
        return self.cond + ' with value = ' + self.value

    @staticmethod
    def from_dict(match_dict) -> Union[str, 'Matcher']:
        if isinstance(match_dict, str):
            return match_dict
        elif isinstance(match_dict, dict):
            return Matcher(match_dict['value'], match_dict['cond'])
        else:
            raise ValueError(f'Not a valid expression or dictionary: {match_dict}')


@dataclass
class MatchedTool:
    name: str
    weight: int

    @staticmethod
    def from_dict(tech_dict):
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
    name: str
    desc: str
    tags: List[str]
    match: str | Matcher
    tools: List[MatchedTool]
    next: Optional[Union['Rule', 'CompoundRule']]

    @staticmethod
    def from_dict(rule_dict: dict) -> Union['Rule', 'CompoundRule']:
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
    name: Optional[str]
    desc: Optional[str]
    tags: List[str]
    operator: str
    rules: List[Union['Rule', 'CompoundRule']]

    @staticmethod
    def from_dict(rule_dict) -> 'CompoundRule':
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
    isd: str
    techniques: List[Tool]
    rules: List[Rule | CompoundRule]

    @staticmethod
    def from_dict(config_dict):
        if "isd" not in config_dict:
            raise ValueError("Missing 'isd' with a version number")

        if config_dict['isd'] not in Config._versions():
            raise ValueError(f"Unsupported version '{config_dict['isd']}'")
        isd = config_dict['isd']

        if "tools" not in config_dict:
            raise ValueError("Missing 'tools'")
        techniques = [Tool.from_dict(tech) for tech in config_dict['tools']]

        if "rules" not in config_dict:
            raise ValueError("Missing 'rules'")
        rules = [Rule.from_dict(rule) for rule in config_dict['rules']]

        return Config(isd, techniques, rules)

    @staticmethod
    def _versions():
        return ["1", "1.0", "1.0.0"]
