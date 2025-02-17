import os
import re
import git
import typer
from slapp.constants import VERSION_TYPES


def extract_changelogs(message: str):
    changelog_regex = re.compile(r'\* (.*)(?:$|\n)')
    return changelog_regex.findall(message)


def parse_changelogs_from_repo(repo: git.Repo) -> list:
    changelogs = []
    if repo.tags:
        last_tag = max(repo.tags, key=lambda t: t.commit.count())
        last_tag_commit_hexsha = last_tag.commit.hexsha
        for commit in repo.iter_commits():
            if commit.hexsha == last_tag_commit_hexsha:
                break
            changelogs.extend(extract_changelogs(commit.message))
    else:
        for commit in repo.iter_commits():
            changelogs.extend(extract_changelogs(commit.message))

    return changelogs


def echo_changelog(version, changelogs):
    if changelogs:
        typer.echo(typer.style(
            f'{version} changelog:',
            fg=typer.colors.BLUE,
            bold=True
        ))
        typer.echo('\n'.join(changelogs))
    else:
        typer.echo(typer.style('No changelog provided.', fg=typer.colors.YELLOW))


def write_changelogs_to_file(
    version, changelogs, changelog_file,
    divider: 'str' = '='*10, bullet: str = '*'
):
    def touchopen(filename, *args, **kwargs):
        if not os.path.isfile(filename):
            open(filename, "a").close()
        return open(filename, *args, **kwargs)

    rendered_changelog = "\n".join(
        [f'{bullet} {item}' for item in changelogs if item]
    )

    with touchopen(changelog_file, 'r+') as f:
        content = f.read()
        f.seek(0)
        f.write(f'{version}\n{divider}\n{rendered_changelog}\n\n{content}')
        f.truncate()


def increment_version(old_version: str, version_type: str):
    major, minor, patch = [int(i) for i in old_version.split('.')]
    if version_type == VERSION_TYPES[0]:
        major, minor, patch = major + 1, 0, 0
    elif version_type == VERSION_TYPES[1]:
        minor, patch = minor + 1, 0
    else:
        patch += 1

    return f'{major}.{minor}.{patch}'


def get_autoincremented_version(changelog_file: str, version_type: str):
    DEFAULT_VERSION = '0.1.0'
    VERSION_REGEX = r'\d{1,}\.\d{1,}\.\d{1,}'
    DEFAULT_ERR = "Couldn't generate a version number."

    if version_type not in VERSION_TYPES:
        typer.echo(
            typer.style(
                f'Version type is invalid, you should use one of theese: {", ".join(VERSION_TYPES)}',
                fg=typer.colors.RED
            )
        )
        return

    if not os.path.isfile(changelog_file):
        return DEFAULT_VERSION
    try:
        with open(changelog_file, "r") as file:
            first_line = file.readline()
    # TODO: use more specific exception
    except Exception:
        typer.echo(typer.style(DEFAULT_ERR, fg=typer.colors.RED))
        return

    match = re.match(VERSION_REGEX, first_line)
    if not match:
        typer.echo(typer.style(DEFAULT_ERR, fg=typer.colors.RED))
        return

    return increment_version(match.string, version_type)
