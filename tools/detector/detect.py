import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import click
import yaml

from eval import Evaluator
from config import Config


@dataclass
class Detection:
    cover: Path
    stego: Path
    weights: dict
    matched_rules: List[str]


@click.command()
@click.option("-i", "--cover-image", type=click.Path(exists=True, path_type=Path),
              help="Path to a cover image")
@click.option("-s", "--stego-image", type=click.Path(exists=True, path_type=Path),
              help="Path to a stego image")
@click.option("--from-stdin", is_flag=True,
              help="Read cover and stego images from stdin as pairs of paths separated by a comma")
@click.option("-c", "--config", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help="Path to the config file in YAML format")
@click.option("--aletheia",
              default='../aletheia',
              type=click.Path(exists=True, file_okay=False, path_type=Path),
              help="Path to the Aletheia root folder")
def detect(cover_image: Path, stego_image: Path, from_stdin: bool, config: Path, aletheia: Path):
    """Detects the used stego tool to hide data in the image.

    The tool uses a config file to define rules for detecting the stego tool.
    Cover and stego images can be provided as arguments or read from stdin.
    If the images are read from stdin, they should be provided as pairs of paths separated by a comma.
    Only the first two values that are separated by a comma are considered and the rest is currently discarded.

    The config file should be in YAML format and contain a list of rules.
    Each rule should have a match condition and a list of tools with their weights.
    The match condition can be a string or an object with a value and a condition.
    The value is evaluated first and then the condition is evaluated with the value.

    Example config file:

    .. code-block:: text

        isd: "1"
        tools:
          - name: PixelKnot
            tags: [ Android, F5 ]
        rules:
          - name: ISA.PixelKnot.File-Size-Diff
            desc: Check if the file size difference is maximum -3%.
            tools:
              - name: PixelKnot
                weight: 5
            match:
              value: attacks.size_diff([(cover.path, stego.path)])[0][3]
              cond: -3 <= value < 0
    """
    sys.path.append(str(aletheia))

    if from_stdin:
        pairs = _get_pairs_from_stdin()
    else:
        if not _check_image(cover_image) or not _check_image(stego_image):
            raise click.BadParameter("Either provide the cover and stego images or use --from-stdin")
        pairs = [(cover_image, stego_image)]

    config = _load_config(config)
    evaluator = Evaluator(config, debug=True)
    for cover_image, stego_image in pairs:
        try:
            evaluator.check(cover_image, stego_image)
        except Exception as e:
            click.echo(e, err=True)

        click.echo()
        click.echo(f"Cover: {cover_image.name}, Stego: {stego_image.name}")
        for tool, weight in evaluator.weights.items():
            click.echo(f"-> {tool}: {weight:}")
        click.echo()


def detect_tools(pairs: List[Tuple[Path, Path]], config: Path, *, debug=False) -> List[Exception]:
    """Detects the used stego tool to hide data in the image.

    :param pairs: List of pairs of cover and stego images
    :param config: Path to the config file in YAML format
    :param debug: Whether to print debug information
    """

    config = _load_config(config)
    evaluator = Evaluator(config, debug=debug)
    errors = []
    for cover_image, stego_image in pairs:
        try:
            evaluator.check(cover_image, stego_image)
            yield Detection(
                cover=cover_image,
                stego=stego_image,
                weights=evaluator.weights,
                matched_rules=[r.name for r in evaluator.matched_rules]
            )
        except Exception as e:
            errors.append(e)
    return errors


def _get_pairs_from_stdin():
    with click.get_text_stream('stdin') as stdin:
        for line in stdin:
            cover, stego = [Path(p.strip()) for p in line.strip().split(",")][:2]
            if not _check_image(cover) or not _check_image(stego):
                continue
            yield cover, stego


def _check_image(image_path: Path):
    image_valid = True
    if not image_path.is_file():
        click.echo(f"Not a file: {image_path}")
        image_valid = False

    return image_valid


def _load_config(config_path: Path) -> Config:
    return Config.from_dict(yaml.safe_load(config_path.open("rb")))


if __name__ == '__main__':
    detect()
