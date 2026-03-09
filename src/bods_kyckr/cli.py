"""CLI entry point for the Kyckr BODS pipeline."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from bods_kyckr.config import PublisherConfig
from bods_kyckr.pipeline import BODSPipeline


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def main(verbose: bool):
    """Transform Kyckr UBO Verify V2 data into BODS v0.4 format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


@main.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    default="output.json",
    help="Output file path (default: output.json)",
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["json", "jsonl"]),
    default="json",
    help="Output format (default: json)",
)
@click.option(
    "--publisher", "-p",
    default="Kyckr UBO Verify",
    help="Publisher name for BODS metadata",
)
@click.option(
    "--publication-date",
    default=None,
    help="Publication date (YYYY-MM-DD). Defaults to today.",
)
def transform(
    input_path: str,
    output: str,
    output_format: str,
    publisher: str,
    publication_date: str | None,
):
    """Transform Kyckr JSON response(s) into BODS v0.4 statements.

    INPUT_PATH can be a single JSON file or a JSONL file containing
    multiple case hierarchy responses.
    """
    config = PublisherConfig(
        publisher_name=publisher,
        output_path=output,
        output_format=output_format,
    )
    if publication_date:
        config.publication_date = publication_date

    pipeline = BODSPipeline(config)
    total = pipeline.process_json_file(input_path)
    pipeline.finalize()

    click.echo(f"Generated {total} BODS statements -> {output}")


@main.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    default="output.jsonl",
    help="Output file path (default: output.jsonl)",
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["json", "jsonl"]),
    default="jsonl",
    help="Output format (default: jsonl)",
)
@click.option(
    "--publisher", "-p",
    default="Kyckr UBO Verify",
    help="Publisher name for BODS metadata",
)
def batch(
    input_dir: str,
    output: str,
    output_format: str,
    publisher: str,
):
    """Process all JSON files in a directory.

    Reads every .json file in INPUT_DIR and transforms them into
    BODS statements.
    """
    config = PublisherConfig(
        publisher_name=publisher,
        output_path=output,
        output_format=output_format,
    )

    pipeline = BODSPipeline(config)
    input_path = Path(input_dir)

    json_files = sorted(input_path.glob("*.json"))
    if not json_files:
        click.echo(f"No JSON files found in {input_dir}", err=True)
        return

    for json_file in json_files:
        try:
            count = pipeline.process_json_file(json_file)
            click.echo(f"  {json_file.name}: {count} statements")
        except Exception as e:
            click.echo(f"  {json_file.name}: ERROR - {e}", err=True)

    pipeline.finalize()
    click.echo(f"\nTotal: {pipeline.statement_count} BODS statements -> {output}")


if __name__ == "__main__":
    main()
