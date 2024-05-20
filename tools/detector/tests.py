import sys
import unittest
from pathlib import Path

import yaml

from config import Config, Rule, MatchedTool, Tool, Matcher, CompoundRule
from detect import _check_image, _load_config, detect_tools


class ConfigTest(unittest.TestCase):
    def test_tool_invalid(self):
        tool_src = '''
        name: tool1
        desc: desc1
        tags: [tag1]
        version: 1.0
        '''
        self.assertRaises(ValueError, Tool.from_dict, yaml.safe_load(tool_src))

    def test_tool(self):
        tool_src = '''
        name: tool1
        desc: desc1
        tags: [tag1]
        version: "1.0"
        '''
        tool = Tool.from_dict(yaml.safe_load(tool_src))
        self.assertEqual(tool.name, 'tool1')
        self.assertEqual(tool.desc, 'desc1')
        self.assertEqual(tool.tags, ['tag1'])
        self.assertEqual(tool.version, '1.0')

    def test_matcher(self):
        matcher_src = '''
        value: value1
        cond: cond1
        '''
        matcher = Matcher.from_dict(yaml.safe_load(matcher_src))
        self.assertEqual(matcher.value, 'value1')
        self.assertEqual(matcher.cond, 'cond1')

    def test_matched_tool(self):
        tool_src = '''
        name: tool1
        weight: 1
        '''
        tool = MatchedTool.from_dict(yaml.safe_load(tool_src))
        self.assertEqual(tool.name, 'tool1')
        self.assertEqual(tool.weight, 1)

    def test_matched_tool_invalid(self):
        tool_src = '''
        name: tool1
        weight: "1"
        '''
        self.assertRaises(ValueError, MatchedTool.from_dict, yaml.safe_load(tool_src))

    def test_rule(self):
        rule_src = '''
        name: rule1
        desc: desc1
        tags: [tag1]
        match: match1
        tools: [{name: tool1, weight: 1}]
        next: null
        '''
        rule = Rule.from_dict(yaml.safe_load(rule_src))
        self.assertEqual(rule.name, 'rule1')
        self.assertEqual(rule.desc, 'desc1')
        self.assertEqual(rule.tags, ['tag1'])
        self.assertEqual(rule.match, 'match1')
        self.assertEqual(len(rule.tools), 1)
        self.assertEqual(rule.tools[0].name, 'tool1')
        self.assertEqual(rule.tools[0].weight, 1)
        self.assertIsNone(rule.next)

    def test_rule_invalid(self):
        rule_src = '''
        name: rule1
        desc: desc1
        tags: [tag1]
        match: 0
        tools: [{name: tool1, weight: 1}]
        next: null
        '''
        self.assertRaises(ValueError, Rule.from_dict, yaml.safe_load(rule_src))

    def test_compound_rule(self):
        rule_src = '''
        name: rule1
        desc: desc1
        tags: [tag1]
        operator: any
        rules: [{name: rule2, desc: desc2, tags: [tag2], match: match2, tools: [{name: tool2, weight: 2}], next: null}]
        '''
        rule = CompoundRule.from_dict(yaml.safe_load(rule_src))
        self.assertEqual(rule.name, 'rule1')
        self.assertEqual(rule.desc, 'desc1')
        self.assertEqual(rule.tags, ['tag1'])
        self.assertEqual(rule.operator, 'any')
        self.assertEqual(len(rule.rules), 1)
        self.assertEqual(rule.rules[0].name, 'rule2')
        self.assertEqual(rule.rules[0].desc, 'desc2')
        self.assertEqual(rule.rules[0].tags, ['tag2'])
        self.assertEqual(rule.rules[0].match, 'match2')
        self.assertEqual(len(rule.rules[0].tools), 1)
        self.assertEqual(rule.rules[0].tools[0].name, 'tool2')
        self.assertEqual(rule.rules[0].tools[0].weight, 2)
        self.assertIsNone(rule.rules[0].next)

    def test_compound_rule_invalid(self):
        rule_src = '''
        name: rule1
        desc: desc1
        tags: [tag1]
        operator: and
        rules: [{name: rule2, desc: desc2, tags: [tag2], match: match2, tools: [{name: tool2, weight: 2}], next: null}]
        '''
        self.assertRaises(ValueError, CompoundRule.from_dict, yaml.safe_load(rule_src))

    def test_config(self):
        config_src = '''
        isd: "1"
        tools:
          - name: tool1
            desc: desc1
            tags: [tag1]
            version: "1.0"
        rules:
          - name: rule1
            desc: desc1
            tags: [tag1]
            match: match1
            tools: [{name: tool1, weight: 1}]
            next: null
        '''
        config = Config.from_dict(yaml.safe_load(config_src))
        self.assertEqual(config.isd, '1')
        self.assertEqual(len(config.tools), 1)
        self.assertEqual(config.tools[0].name, 'tool1')
        self.assertEqual(config.tools[0].desc, 'desc1')
        self.assertEqual(config.tools[0].tags, ['tag1'])
        self.assertEqual(config.tools[0].version, '1.0')
        self.assertEqual(len(config.rules), 1)
        self.assertEqual(config.rules[0].name, 'rule1')
        self.assertEqual(config.rules[0].desc, 'desc1')
        self.assertEqual(config.rules[0].tags, ['tag1'])
        self.assertEqual(config.rules[0].match, 'match1')
        self.assertEqual(len(config.rules[0].tools), 1)
        self.assertEqual(config.rules[0].tools[0].name, 'tool1')
        self.assertEqual(config.rules[0].tools[0].weight, 1)
        self.assertIsNone(config.rules[0].next)

    def test_config_invalid(self):
        config_src = '''
        isd: 1
        tools:
          - name: tool1
            desc: desc1
            tags: [tag1]
            version: "1.0"
        rules:
          - name: rule1
            desc: desc1
            tags: [tag1]
            match: match1
            tools: [{name: tool1, weight: 1}]
            next: null
        '''
        self.assertRaises(ValueError, Config.from_dict, yaml.safe_load(config_src))


class DetectTest(unittest.TestCase):
    def test_check_image(self):
        self.assertFalse(_check_image(Path('not_a_file')))

    def test_load_config(self):
        _config = _load_config(Path('rules/stegoapps.yaml'))
        self.assertIsInstance(_config, Config)

    def test_detect_tools(self):
        sys.path.append('../aletheia')
        base_path = Path('../../datasets/StegoAppDB_stegos_20240309-030352')
        pairs = [(base_path / 'covers' / '260507.png', base_path / 'stegos' / '260508.png')]
        config = Path('rules/stegoapps.yaml')
        errors = []
        for result in detect_tools(pairs, config, debug=True, handle_errors=lambda e: errors.extend(e)):
            self.assertEqual(result.cover, pairs[0][0])
            self.assertEqual(result.stego, pairs[0][1])
            self.assertIsInstance(result.weights, dict)
            self.assertIsInstance(result.matched_rules, list)
            self.assertEqual(len(result.matched_rules), 3)
            self.assertEqual(result.matched_rules[0], 'ISA.PocketStego-MobiStego.File-Size-Diff')
            self.assertEqual(result.matched_rules[1], 'ISA.MobiStego.LSB-Signature')
            self.assertEqual(result.matched_rules[2], 'ISA.MobiStego.Metadata-Diff')
            self.assertEqual(result.weights['PocketStego'], 1)
            self.assertEqual(result.weights['MobiStego'], 3)
        if len(errors) > 0:
            for error in errors:
                print(error)
        self.assertEqual(0, len(errors))



if __name__ == '__main__':
    unittest.main()
