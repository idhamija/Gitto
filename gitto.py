import argparse
from datetime import datetime
import difflib
import hashlib
import json
import os


class VCS:
    def __str__(self) -> str:
        return f"vcs{{dir: '{self.directory}'}}"

    def __init__(self, directory):
        self.directory = os.path.abspath(directory if directory is not None else ".")
        self.objects_path = os.path.join(self.directory, ".gitto", "objects")
        self.index_path = os.path.join(self.directory, ".gitto", "index")
        self.head_path = os.path.join(self.directory, ".gitto", "HEAD")

    def generate_hash(self, content) -> str:
        return hashlib.sha1(content.encode("utf-8")).hexdigest()

    def init(self):
        try:
            os.makedirs(self.objects_path)
        except OSError:
            print(f"Gitto repository already initialized in {self.directory}")
            return

        if not os.path.exists(self.head_path):
            open(self.head_path, "w").close()

        if not os.path.exists(self.index_path):
            with open(self.index_path, "w") as f:
                json.dump({}, f)

        print(f"Initialized empty Gitto repository in {self.directory}")

    def add(self, paths):
        staged_files = self.get_staged_files()
        tracked_files, tracked_files_with_changes = self.get_tracked_files(staged_files)
        untracked_files = self.get_untracked_files(staged_files, tracked_files)
        addAll = False
        for path in paths:
            if path == ".":
                addAll = True
            elif (
                not path in staged_files
                and path not in tracked_files
                and path not in untracked_files
            ):
                print(f"'{path}' did not match any files")
                return

        if addAll:
            for path in tracked_files_with_changes:
                self.add_file(path)
            for path in untracked_files:
                self.add_file(path)
        else:
            for path in paths:
                if path in tracked_files_with_changes or path in untracked_files:
                    self.add_file(path)
                else:
                    print(f"'{path}' already added to staging area")

    def add_file(self, file_path):
        with open(file_path, "r") as f:
            file_data = f.read()
        file_hash = self.generate_hash(file_data)
        with open(os.path.join(self.objects_path, file_hash), "w", encoding="utf-8") as f:
            f.write(file_data)
        self.append_to_staging_area(file_path, file_hash)
        print(f"'{file_path}' added to staging area")

    def unstage(self, paths):
        staged_files = self.get_staged_files()
        for path in paths:
            if path in staged_files:
                self.unstage_file(path)
            else:
                print(f"'{path}' is not in the staging area")

    def unstage_file(self, file_path):
        with open(self.index_path, "r", encoding="utf-8") as f:
            index = json.load(f)

        rel_path = os.path.relpath(file_path, self.directory)
        if rel_path in index:
            del index[rel_path]
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(index, f)
            print(f"'{file_path}' unstaged")
        else:
            print(f"'{file_path}' is not in the staging area")

    def restore(self, paths):
        head = self.get_current_head()
        if not head:
            print("No commit found")

        staged_files = self.get_staged_files()
        tracked_files, tracked_files_with_changes = self.get_tracked_files(staged_files)
        for path in paths:
            if path in tracked_files_with_changes:
                self.restore_file(path)
            elif path in tracked_files:
                print(f"'{path}' has no changes to be restored")
            else:
                print(f"'{path}' is not being tracked")

    def restore_file(self, path):
        head = self.get_current_head()
        commit_json = self.get_commit_data(head)
        if commit_json:
            committed_data_files = json.loads(commit_json)["files"]
            for file in committed_data_files.keys():
                file_path = os.path.relpath(os.path.join(self.directory, file))
                if path == file_path:
                    file_hash = committed_data_files[file]
                    committed_file_content = self.get_file_content(file_hash)
                    with open(file_path, "w") as f:
                        f.write(committed_file_content)
                    print(f"'{path}' restored to last commit version")
                    return

    def append_to_staging_area(self, file_path, file_hash):
        with open(self.index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        index[os.path.relpath(file_path, self.directory)] = file_hash
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(index, f)

    def get_current_head(self):
        with open(self.head_path, "r", encoding="utf-8") as f:
            head = f.read().strip()
        if head == "":
            return None
        return head

    def get_staged_files(self):
        staged_files = set()
        with open(self.index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        for file_path in index.keys():
            rel_path = os.path.relpath(os.path.join(self.directory, file_path))
            staged_files.add(rel_path)
        return staged_files

    def get_tracked_files(self, staged_files):
        tracked_files = set()
        tracked_files_with_changes = set()

        head = self.get_current_head()
        if head:
            commit_json = self.get_commit_data(head)
            if commit_json:
                committed_data_files = json.loads(commit_json)["files"]
                for file in committed_data_files.keys():
                    file_path = os.path.relpath(os.path.join(self.directory, file))
                    if file_path not in staged_files:
                        tracked_files.add(file_path)
                        with open(file_path, "r") as f:
                            content = f.read()
                        if self.generate_hash(content) != committed_data_files[file]:
                            tracked_files_with_changes.add(file_path)

        with open(self.index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        for file_path in staged_files:
            if file_path not in tracked_files:
                with open(file_path, "r") as f:
                    content = f.read()
                if (
                    self.generate_hash(content)
                    != index[os.path.relpath(file_path, self.directory)]
                ):
                    tracked_files_with_changes.add(file_path)
        return tracked_files, tracked_files_with_changes

    def get_untracked_files(self, staged_files, tracked_files):
        untracked_files = set()
        for root, _, files in os.walk(self.directory):
            if ".gitto" in root:
                continue
            for file in files:
                if file == "gitto.py":
                    continue
                file_path = os.path.relpath(os.path.join(root, file))
                if file_path not in staged_files and file_path not in tracked_files:
                    with open(file, "r") as f:
                        file_hash = self.generate_hash(f.read())
                    if not os.path.exists(os.path.join(self.objects_path, file_hash)):
                        untracked_files.add(os.path.relpath(file_path, self.directory))
        return untracked_files

    def get_staged_and_unstaged_files(self):
        unstaged_files = set()
        staged_files = self.get_staged_files()
        for root, _, files in os.walk(self.directory):
            for file in files:
                file_path = os.path.relpath(os.path.join(root, file))
                if file_path not in staged_files:
                    unstaged_files.add(file_path)
        return staged_files, unstaged_files

    def status(self):
        staged_files = self.get_staged_files()
        tracked_files, tracked_files_with_changes = self.get_tracked_files(staged_files)
        untracked_files = self.get_untracked_files(staged_files, tracked_files)

        if not staged_files and not tracked_files_with_changes and not untracked_files:
            print("nothing to commit, working tree clean")
            return

        if staged_files:
            print("Changes to be committed:")
            for file in staged_files:
                print(f"\033[92m\t{file}\033[0m")
            print()

        if tracked_files_with_changes:
            print("Changes not staged for commit:")
            for file in tracked_files_with_changes:
                print(f"\033[91m\t{file}\033[0m")
            print()

        if untracked_files:
            print("Untracked files:")
            for file in untracked_files:
                print(f"\033[91m\t{file}\033[0m")

    def get_commit_data(self, commit_hash):
        commit_path = os.path.join(self.objects_path, commit_hash)
        if os.path.exists(commit_path):
            with open(commit_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def update_head(self, commit_hash):
        with open(self.head_path, "w", encoding="utf-8") as f:
            f.write(commit_hash)

    def commit(self, message):
        with open(self.index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        if not f:
            print("No changes to commit ")
            return

        parent_commit = self.get_current_head()
        commit_json = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "files": index,
            "parent": parent_commit,
        }
        commit_hash = self.generate_hash(json.dumps(commit_json))
        commit_path = os.path.join(self.objects_path, commit_hash)
        with open(commit_path, "w", encoding="utf-8") as f:
            json.dump(commit_json, f)
        self.update_head(commit_hash)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump({}, f)
        print(f"Commit successfully created with commit hash: {commit_hash}")

    def log(self):
        head = self.get_current_head()
        if head:
            while head:
                commit_json = self.get_commit_data(head)
                if commit_json is None:
                    raise ValueError(f"Commit data for hash {head} not found.")
                commit_json = json.loads(commit_json)
                timestamp = datetime.fromisoformat(commit_json["timestamp"])
                formatted_date = timestamp.strftime("%d %b %Y  %H:%M:%S %z")
                print(
                    f"Commit:\t{head}\nDate:\t{formatted_date}\n\n\t{commit_json['message']}\n"
                )
                head = commit_json.get("parent")
        else:
            print("Gitto repository does not have any commits yet")

    def get_file_content(self, file_hash):
        object_path = os.path.join(self.objects_path, file_hash)
        with open(object_path, "r", encoding="utf-8") as f:
            return f.read()

    def show_commit_diff(self, commit_hash):
        commit_data = self.get_commit_data(commit_hash)
        if commit_data is None:
            print("Commit not found")
            return

        commit_json = json.loads(commit_data)
        if not commit_json["parent"]:
            print("First commit")
            return

        print("Changes from the last commit: ")
        files = commit_json["files"]

        for file_path in files:
            print(f"File: {file_path}")
            file_content = self.get_file_content(files[file_path])

            if commit_json["parent"]:
                parent_commit_data = self.get_commit_data(commit_json["parent"])

                if parent_commit_data is None:
                    print("Parent commit not found")
                    return

                parent_commit_json = json.loads(parent_commit_data)

                if file_path in parent_commit_json["files"]:
                    parent_file_content = self.get_file_content(
                        parent_commit_json["files"][file_path]
                    )

                    if parent_file_content is not None:
                        diff = difflib.unified_diff(
                            parent_file_content.splitlines(),
                            file_content.splitlines(),
                            lineterm="",
                        )

                        for line in diff:
                            if line.startswith("+"):
                                print(f"\033[92m+{line[0]} {line[1:]}\033[0m")
                            elif line.startswith("-"):
                                print(f"\033[91m-{line[0]} {line[1:]}\033[0m")
                            else:
                                print(f"\033[90m{line}\033[0m")
                    else:
                        print("Parent file content not found")
            #     else:
            #         print("File not found in parent commit")
            # else:
            # print("First commit")

            if file_path not in parent_commit_json["files"]:
                print("New file in this commit")
            print()


def parsed_arguments():
    parser = argparse.ArgumentParser(description="Gitto version control system")
    subparsers = parser.add_subparsers(dest="command")

    parser_init = subparsers.add_parser("init", help="Initialize the repository")
    parser_init.add_argument(
        "directory", type=str, nargs="?", default=".", help="Directory to be tracked"
    )

    parser_add = subparsers.add_parser("add", help="Add file(s)")
    parser_add.add_argument("files", nargs="+", type=str, help="File(s) to be added")

    parser_restore = subparsers.add_parser("restore", help="Restore file(s)")
    parser_restore.add_argument(
        "--staged", action="store_true", help="Unstage the given file(s)"
    )
    parser_restore.add_argument(
        "files", nargs="+", type=str, help="File(s) to be restored or unstaged"
    )

    parser_commit = subparsers.add_parser("commit", help="Commit changes")
    parser_commit.add_argument("message", type=str, help="Commit message")

    parser_log = subparsers.add_parser("log", help="Show commit log")

    parser_show = subparsers.add_parser("show-diff", help="Show commit diff")
    parser_show.add_argument(
        "commit_hash", type=str, help="Commit hash to show diff for"
    )

    parser_status = subparsers.add_parser("status", help="Show the working tree status")

    return parser.parse_args()


def find_repo_dir():
    current_path = os.getcwd()
    while current_path != os.path.dirname(current_path):
        if os.path.exists(os.path.join(current_path, ".gitto")):
            return os.path.join(current_path)
        current_path = os.path.dirname(current_path)
    return None


def main():
    args = parsed_arguments()

    if args.command == "init":
        if not os.path.exists(args.directory):
            os.makedirs(args.directory)
        vcs = VCS(args.directory)
        vcs.init()
        return

    directory = find_repo_dir()
    if not directory:
        print("Not a gitto repository (or any of the parent directories)")
        return

    vcs = VCS(directory)
    if args.command == "add":
        vcs.add(args.files)
    elif args.command == "restore":
        if args.staged:
            vcs.unstage(args.files)
        else:
            vcs.restore(args.files)
    elif args.command == "status":
        vcs.status()
    elif args.command == "commit":
        vcs.commit(args.message)
    elif args.command == "log":
        vcs.log()
    elif args.command == "show-diff":
        vcs.show_commit_diff(args.commit_hash)


if __name__ == "__main__":
    main()
