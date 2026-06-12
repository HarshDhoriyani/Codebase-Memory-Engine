import re
import tempfile
import subprocess
from dataclasses import dataclass, field
from git import Repo, InvalidGitRepositoryError
from ..parser.models import FunctionNode
from .classifier import classify_commits, primary_category


@dataclass
class FunctionProvenance:
    function_id: str
    function_name: str
    file_path: str
    change_count: int = 0
    last_author: str = ""
    last_changed: str = ""
    first_seen: str = ""
    last_commit_msg: str = ""
    authors: list[str] = field(default_factory=list)
    commit_message: list[str] = field(default_factory=list)
    primary_category: str = "unknown"
    category_counts: dict = field(default_factory=dict)


def _parse_changed_lines(diff_text: str) -> set[int]:
    """
    Parse unified diff output and return the set of line numbers that were added or modified in the new version.

    Unified diff hunk header looks like:
        @@ -old_start,old_count +new_start,new_count @@
    We track new_start line numbers for added lines.
    """

    changed = set()
    current_line = 0

    for line in diff_text.split("\n"):
        hunk = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if hunk:
            current_line = int(hunk.group(1))
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            changed.add(current_line)
            current_line += 1
        elif line.startswith("-"):
            pass
        else:
            current_line += 1
    
    return changed

def _function_was_touched(
        fn: FunctionNode,
        changed_lines: set[int]
) -> bool:
    fn_lines = set(range(fn.start_line, fn.end_line+1))
    return bool(fn_lines & changed_lines)

def mine_file_history(
        repo: Repo,
        file_path: str,
        functions: list[FunctionNode],
        max_commits: int = 200,
) -> list[FunctionProvenance]:
    """
    Walk commit history for a single file.
    For each commit, check which functions were modified.
    Returns a list of FunctionProvenance - one per function.
    """

    if not functions:
        return []
    
    provenance: dict[str,FunctionProvenance] = {}
    for fn in functions:
        fid = f"{fn.file_path}::{fn.name}::{fn.start_line}"
        provenance[fid] = FunctionProvenance(
            function_id=fid,
            function_name=fn.name,
            file_path=fn.file_path,
        )

    try:
        commits = list(repo.iter_commits(
            paths=file_path,
            max_count=max_commits,
        ))
    except Exception:
        return list(provenance.values())
    
    for commit in commits:
        committed_dt = commit.committed_datetime.isoformat()
        author = commit.author.name or "unknown"
        message = (commit.message or "").strip().split("\n")[0]

        diff_text = ""
        try:
            if commit.parents:
                diffs = commit.parents[0].diff(
                    commit,
                    paths=file_path,
                    create_patch=True,
                )
                for d in diffs:
                    if d.diff:
                        diff_text = d.diff.decode("utf-8", errors="replace")
            else:
                diff_text = ""
        except Exception:
            pass

        changed_lines = _parse_changed_lines(diff_text) if diff_text else set()


        for fn in functions:
            fid = f"{fn.file_path}::{fn.name}::{fn.start_line}"
            prov = provenance[fid]

            touched = (
                not commit.parents
                or not diff_text
                or _function_was_touched(fn, changed_lines)
            )

            if touched:
                prov.change_count += 1
                prov.commit_message.append(message)
                if author not in prov.authors:
                    prov.authors.append(author)

                if not prov.last_changed:
                    prov.last_changed = committed_dt
                    prov.last_author = author
                    prov.last_commit_msg = message

                prov.first_seen = committed_dt


    for prov in provenance.values():
        if prov.commit_message:
            prov.category_counts = classify_commits(prov.commit_message)
            prov.primary_category = primary_category(prov.commit_message)

    return list(provenance.values())


def mine_repo_history(
        repo_path: str,
        parse_results: list,
        max_commits_per_file: int = 100,
) -> list[FunctionProvenance]:
    """
    Mine git history for an entire repo.
    Returns provenance records for every function.
    """

    try:
        repo = Repo(repo_path)
    except InvalidGitRepositoryError:
        print(f"Not a git repo: {repo_path}")
        return []
    
    all_provenance: list[FunctionProvenance] = []
    total_files = len([r for r in parse_results if r.functions])
    done = 0

    for result in parse_results:
        if not result.functions or result.language != "python":
            continue
        file_prov = mine_file_history(
            repo,
            result.file_path,
            result.functions,
            max_commits=max_commits_per_file,
        )
        all_provenance.extend(file_prov)
        done += 1
        if done % 20 == 0:
            print(f"Mined {done}/{total_files} files....")

    print(f"Git archaeology complete - {len(all_provenance)} functions enriched")
    return all_provenance