import os
from pathlib import Path
from time import sleep

import click
from PIL import Image

from config import Config, Rule, CompoundRule


class ImageFile:
    def __init__(self, path):
        self.path = Path(path)
        self.image = Image.open(self.path)


class Evaluator:
    def __init__(self, config: Config, *, debug: bool = False, _globals=None, limit=1000):
        self.config = config
        self.cover = self.stego = None
        self.weights = {}
        self.debug = debug
        self.limit = limit

        import aletheialib.attacks as attacks
        self._globals = _globals or {'os': os, 'attacks': attacks}

    def check(self, cover_path, stego_path):
        self.weights = {}
        self.cover = ImageFile(cover_path)
        self.stego = ImageFile(stego_path)
        return [self._eval_rule(rule) for rule in self.config.rules]

    def _eval_rule(self, rule, /, level=0):
        if isinstance(rule, Rule):
            self._debug_begin(rule, level)
            _locals = {'cover': self.cover, 'stego': self.stego}
            try:
                if isinstance(rule.match, str):
                    res = eval(rule.match, self._globals, _locals)
                else:
                    value = eval(rule.match.value, self._globals, _locals)
                    self._debug_value(value, level)
                    res = eval(rule.match.cond, self._globals, {**_locals, 'value': value})

                if res:
                    self._debug_end(True)
                    for tool in rule.tools:
                        self.weights[tool.name] = self.weights.get(tool.name, 0) + tool.weight
                    return self._eval_rule(rule.next, level + 1) if rule.next else True
                else:
                    self._debug_end(False)
            except Exception as e:
                self._debug_end(False, level, e)

        elif isinstance(rule, CompoundRule):
            return self._eval_compound_rule(rule, level + 1)

        return False

    def _eval_compound_rule(self, rule: CompoundRule, /, level=0):
        next_level = level + 1
        match rule.operator:
            case 'any':
                return any(self._eval_rule(r, next_level) for r in rule.rules)
            case 'all':
                return all(self._eval_rule(r, next_level) for r in rule.rules)
            case 'none':
                return not any(self._eval_rule(r, next_level) for r in rule.rules)
            case _:
                return False

    def _debug_begin(self, rule, level):
        if self.debug:
            if isinstance(rule, Rule):
                click.echo(
                    f'{" " * level}╰ {rule.name} := {rule.match} -> [{", ".join(f"{t.name} ({t.weight})" for t in rule.tools)}]',
                    nl=False)
            elif isinstance(rule, CompoundRule):
                middle = rule.name if rule.name else ''
                click.echo(f'{" " * level}|- {middle} => {rule.operator}:')

    def _debug_value(self, value, level):
        value = str(value)
        if self.debug:
            click.echo()
            click.echo(f'{" " * level}  value : {value[:self.limit] + "..." * (len(value) > self.limit)}', nl=False)

    def _debug_end(self, success, level=0, error_msg=None):
        if self.debug:
            if success:
                click.secho(' ✓', fg='green')
            else:
                click.secho(' ✕', fg='red')
                if error_msg:
                    sleep(0.1)
                    click.echo(f'{" " * level} ! {error_msg}', err=True)
