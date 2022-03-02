import click
import logging
from pathlib import Path

from .cmake_extention import CmakeExtension
from .data_store import DataStore

@click.group()
@click.option("--datastore", default=Path(".xsteps"), show_default=True, type=click.Path(exists=False),
        help="Path to root datastore location")
@click.pass_context
def cli(ctx, datastore):
    # ctx.ensure_object(dict)
    root_datastore = DataStore("", datastore)
    ctx.obj = root_datastore
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)


# TODO: ??? Create pass context decorator for DataStore and ExtensionCore ???


@cli.group()
@click.option("--local-conan-cache", default=True, show_default=True, type=bool,
        help="If we should use local conan cache placed in datastore folder instead of the system folder.")
@click.pass_context
def cmake(ctx, local_conan_cache):
    root_datastore = ctx.obj
    ctx.obj = CmakeExtension(local_conan_cache, "cmake", root_datastore.path)


@cmake.command()
@click.argument("reference", required=False, type=str)
@click.pass_context
def install(ctx, reference):
    cmake = ctx.obj
    cmake.install(reference)


@cmake.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('cmake_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def execute(ctx, cmake_args):
    cmake = ctx.obj
    cmake.execute(list(cmake_args))


def main():
    cli()

if __name__ == "__main__":
    main()

