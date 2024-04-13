from pathlib import Path

import click
import pandas as pd


@click.command()
@click.argument('match_file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('-c', '--covers-column', default='cover_image_filename', type=str, help='Column name for cover images')
@click.option('-s', '--stegos-column', default='stego_image_filename', type=str, help='Column name for stego images')
@click.option('-m', '--method-column', default='embedding_method', type=str,
              help='Column name for steganography embedding method')
@click.option('--cover-dir-name', default='covers', type=str, help='Directory name for cover images')
@click.option('--stego-dir-name', default='stegos', type=str, help='Directory name for stego images')
def cover_stego_pairs(
        match_file: Path,
        covers_column: str,
        stegos_column: str,
        method_column: str,
        cover_dir_name: str,
        stego_dir_name: str):
    """Extracts cover-stego pairs from a CSV file

    MATCH_FILE is a CSV file with columns for cover images, stego images, and steganography embedding methods.
    """

    df = pd.read_csv(match_file)
    for _, row in df.iterrows():
        cover = (match_file.parent / cover_dir_name / row[covers_column]).resolve()
        stego = (match_file.parent / stego_dir_name / row[stegos_column]).resolve()
        method = row[method_column]
        click.echo(f'{cover}, {stego}, {method}')


if __name__ == '__main__':
    cover_stego_pairs()
