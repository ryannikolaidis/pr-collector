"""Application module for pr-collector."""

from __future__ import annotations

import os
import re
from pathlib import Path

import git
from github import Github

from . import __version__

PROJECT_NAME = "pr-collector"
PROJECT_DESCRIPTION = "Collect PR diffs and metadata into markdown files"


def sanitize_filename(filename: str) -> str:
    """Sanitize a string to be safe for use as a filename."""

    # Replace spaces with hyphens and remove/replace unsafe characters
    sanitized = re.sub(r"[^\w\s\-_.]", "", filename)
    sanitized = re.sub(r"[-\s]+", "-", sanitized)
    return sanitized.strip("-")


def get_pr_info(repo_url: str, pr_number: int, token: str | None = None) -> dict[str, str]:
    """Get PR information from GitHub API."""

    # Extract owner and repo name from URL
    match = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", repo_url)
    if not match:
        raise ValueError(f"Could not parse GitHub URL: {repo_url}")

    owner, repo_name = match.groups()

    # Initialize GitHub client
    g = Github(token) if token else Github()

    try:
        repo = g.get_repo(f"{owner}/{repo_name}")
        pr = repo.get_pull(pr_number)

        return {
            "title": pr.title,
            "description": pr.body or "",
            "author": pr.user.login,
            "created_at": pr.created_at.isoformat() if pr.created_at else "",
            "updated_at": pr.updated_at.isoformat() if pr.updated_at else "",
            "state": pr.state,
            "base_branch": pr.base.ref,
            "head_branch": pr.head.ref,
            "url": pr.html_url,
            "number": str(pr.number),
        }
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg and not token:
            raise RuntimeError(
                f"Repository '{owner}/{repo_name}' or PR #{pr_number} not found, or repository is private. "
                "Please provide a GitHub token using --token or set GITHUB_TOKEN environment variable."
            )
        else:
            raise RuntimeError(f"Failed to fetch PR info: {e}")


def get_git_diff(
    repo_path: str, base_branch: str, head_branch: str, target_dir: str | None = None
) -> str:
    """Get git diff for specified directory or entire repo."""

    try:
        repo = git.Repo(repo_path)

        # Ensure we have the latest refs
        repo.remotes.origin.fetch()

        # Create diff command
        if target_dir:
            # Make target_dir relative to repo root if it's absolute
            if os.path.isabs(target_dir):
                repo_root = repo.working_tree_dir
                if repo_root and target_dir.startswith(str(repo_root)):
                    target_dir = os.path.relpath(target_dir, repo_root)

            diff = repo.git.diff(f"origin/{base_branch}...origin/{head_branch}", "--", target_dir)
        else:
            diff = repo.git.diff(f"origin/{base_branch}...origin/{head_branch}")

        return diff
    except Exception as e:
        raise RuntimeError(f"Failed to get git diff: {e}")


def generate_markdown(
    pr_info: dict[str, str], diff_content: str, target_dir: str | None = None
) -> str:
    """Generate markdown content from PR info and diff."""

    markdown_lines = [
        f"# {pr_info['title']}",
        "",
        f"**PR #{pr_info['number']}** - {pr_info['state'].title()}",
        f"**Author:** {pr_info['author']}",
        f"**Created:** {pr_info['created_at']}",
        f"**Updated:** {pr_info['updated_at']}",
        f"**Base Branch:** {pr_info['base_branch']}",
        f"**Head Branch:** {pr_info['head_branch']}",
        f"**URL:** {pr_info['url']}",
        "",
    ]

    if target_dir:
        markdown_lines.extend(
            [
                f"**Target Directory:** `{target_dir}`",
                "",
            ]
        )

    if pr_info["description"].strip():
        markdown_lines.extend(
            [
                "## Description",
                "",
                pr_info["description"],
                "",
            ]
        )

    markdown_lines.extend(
        [
            "## Changes",
            "",
            "```diff",
            diff_content,
            "```",
        ]
    )

    return "\n".join(markdown_lines)


def get_current_pr_number(repo_path: str, token: str | None = None) -> int:
    """Get the PR number for the current branch."""

    owner = None
    repo_name = None
    current_branch = None
    try:
        repo = git.Repo(repo_path)
        current_branch = repo.active_branch.name
        remote_url = repo.remotes.origin.url

        # Convert SSH URL to HTTPS if needed
        if remote_url.startswith("git@github.com:"):
            remote_url = remote_url.replace("git@github.com:", "https://github.com/")
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]

        # Extract owner and repo name from URL
        match = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", remote_url)
        if not match:
            raise ValueError(f"Could not parse GitHub URL: {remote_url}")

        owner, repo_name = match.groups()

        # Initialize GitHub client
        g = Github(token) if token else Github()

        repo_obj = g.get_repo(f"{owner}/{repo_name}")

        # Get the remote tracking branch for the current branch
        try:
            current_branch_obj = repo.heads[current_branch]
            tracking_branch = current_branch_obj.tracking_branch()
            if tracking_branch:
                # Extract the remote branch name (e.g., "origin/feature-branch" -> "feature-branch")
                remote_branch_name = tracking_branch.remote_head
            else:
                remote_branch_name = current_branch
        except Exception:
            # Fallback to current branch name if tracking branch detection fails
            remote_branch_name = current_branch

        # Search for PRs with the remote branch as head
        pulls = repo_obj.get_pulls(state="open", head=f"{owner}:{remote_branch_name}")
        pulls_list = list(pulls)

        if not pulls_list:
            # Try without owner prefix in case of forks
            pulls = repo_obj.get_pulls(state="open", head=remote_branch_name)
            pulls_list = list(pulls)

        if not pulls_list:
            # Iterate through all open PRs and find one with matching head branch
            all_pulls = repo_obj.get_pulls(state="open")
            for pr in all_pulls:
                if pr.head.ref == remote_branch_name:
                    return pr.number

            # If we get here, no PR was found by iterating through all PRs
            raise ValueError(
                f"No open PR found for branch '{current_branch}' "
                f"(remote: '{remote_branch_name}'). "
                f"Make sure there's an open PR for this branch."
            )

        # Return the first (most recent) PR
        return pulls_list[0].number

    except Exception as e:
        error_msg = str(e)

        # Try to get variables that may not be in scope if error occurred early
        try:
            owner_repo = f"{owner}/{repo_name}"
            branch = current_branch
        except (AttributeError, KeyError, ValueError):
            # Fallback to default values if variables are not in scope
            owner_repo = "repository"
            branch = "current branch"
        if "404" in error_msg and not token:
            raise RuntimeError(
                f"Repository '{owner_repo}' not found or is private. "
                "Please provide a GitHub token using --token or set GITHUB_TOKEN environment variable."
            )
        elif "404" in error_msg:
            raise RuntimeError(
                f"Repository '{owner_repo}' not found, or no open PR exists for branch '{branch}'. "
                "Make sure the repository exists and has an open PR for this branch."
            )
        else:
            raise RuntimeError(f"Failed to get current branch PR: {e}")


def collect_pr_data(
    repo_path: str,
    pr_number: int | None,
    output_path: str | None = None,
    target_dir: str | None = None,
    token: str | None = None,
) -> tuple[str | None, str]:
    """Main function to collect PR data and generate markdown file."""

    try:
        # Auto-detect PR number if not provided
        if pr_number is None:
            pr_number = get_current_pr_number(repo_path, token)

        repo = git.Repo(repo_path)
        remote_url = repo.remotes.origin.url

        # Convert SSH URL to HTTPS if needed
        if remote_url.startswith("git@github.com:"):
            remote_url = remote_url.replace("git@github.com:", "https://github.com/")
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]

        # Get PR information
        pr_info = get_pr_info(remote_url, pr_number, token)

        # Get diff
        diff_content = get_git_diff(
            repo_path, pr_info["base_branch"], pr_info["head_branch"], target_dir
        )

        # Generate markdown
        markdown_content = generate_markdown(pr_info, diff_content, target_dir)

        # Handle output path
        if output_path:
            # If output_path is provided, use it as-is (could be a file or directory)
            output_path_obj = Path(output_path)
            if output_path_obj.is_dir() or output_path.endswith("/"):
                # It's a directory, generate filename
                safe_title = sanitize_filename(pr_info["title"])
                filename = f"pr-{pr_number}-{safe_title}.md"
                final_output_path = output_path_obj / filename
            else:
                # It's a full file path
                final_output_path = output_path_obj

            # Ensure parent directory exists
            final_output_path.parent.mkdir(parents=True, exist_ok=True)
            final_output_path.write_text(markdown_content)
            return str(final_output_path), markdown_content
        else:
            # No file output, just return the content
            return None, markdown_content

    except Exception as e:
        # Re-raise with proper error context
        raise RuntimeError(f"Failed to collect PR data: {e}") from e


def list_open_prs(repo_path: str, token: str | None = None) -> list[dict[str, str]]:
    """List all open PRs for the repository."""

    try:
        repo = git.Repo(repo_path)
        remote_url = repo.remotes.origin.url

        # Convert SSH URL to HTTPS if needed
        if remote_url.startswith("git@github.com:"):
            remote_url = remote_url.replace("git@github.com:", "https://github.com/")
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]

        # Extract owner and repo name from URL
        match = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", remote_url)
        if not match:
            raise ValueError(f"Could not parse GitHub URL: {remote_url}")

        owner, repo_name = match.groups()

        # Initialize GitHub client
        g = Github(token) if token else Github()
        repo_obj = g.get_repo(f"{owner}/{repo_name}")

        # Get all open PRs
        all_pulls = repo_obj.get_pulls(state="open")
        pr_list = []

        for pr in all_pulls:
            pr_list.append(
                {
                    "number": str(pr.number),
                    "title": pr.title,
                    "branch": pr.head.ref,
                    "author": pr.user.login,
                    "created": pr.created_at.strftime("%Y-%m-%d"),
                    "url": pr.html_url,
                }
            )

        return pr_list

    except Exception as e:
        raise RuntimeError(f"Failed to list PRs: {e}")


def get_application_info() -> dict[str, str]:
    """Return basic metadata about the application."""

    return {
        "name": PROJECT_NAME,
        "description": PROJECT_DESCRIPTION,
        "version": __version__,
    }
