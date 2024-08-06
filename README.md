# Gitto - A Simple Version Control System

Gitto is a simple version control system implemented in Python. It provides basic functionalities such as initializing a repository, adding files, committing changes, viewing commit logs, and restoring files to their previous commit state. This project demonstrates the core concepts of version control and can be a useful learning tool.

## Features

- Initialize a Gitto repository
- Add files to the staging area
- Unstage files from the staging area
- Restore files to their previous commit state
- Commit changes with a message
- Show current status
- View the commit log
- Show differences made for a commits

## Installation

To use Gitto, simply clone this repository and ensure you have Python 3.6 or newer installed on your system.

```
git clone https://github.com/yourusername/gitto.git
cd gitto
```

## Usage

### Initialize a Repository

To initialize a new Gitto repository, use the init command:

```
python ../gitto.py init [directory]
```

If no directory is specified, the current directory will be used.

### Add Files

To add files to the staging area, use the add command:

```
python ../gitto.py add [file1] [file2] ...
```

### Restore Files

To restore files to their state in the previous commit, use the restore command:

```
python ../gitto.py restore [file1] [file2] ...
```

#### To unstage files from the staging area, use the restore --staged command:

```
python ../gitto.py restore --staged [file1] [file2] ...
```

### Commit Changes

To commit the changes in the staging area, use the commit command with a commit message:

```
python ../gitto.py commit "Your commit message"
```

### Show Status

To show the working tree status, use the status command:

```
python ../gitto.py status
```

### View Commit Log

To view the commit log, use the log command:

```
python ../gitto.py log
```

### Show Commit Differences

To show the differences between a specific commit and its parent, use the show-diff command with the commit hash:

```
python ../gitto.py show-diff [commit_hash]
```

## Example

Here is an example workflow:

```bash
# Create an example directory and navigate to directory
mkdir example/
cd example/

# Initialize a new Gitto repository in current directory
python ../gitto.py init

# Create a new file
echo "Hello, Gitto!" > hello.txt

# Add the file to the staging area
python ../gitto.py add hello.txt

# Commit the file
python ../gitto.py commit "Initial commit"

# View the commit log
python ../gitto.py log

# Show the status
python ../gitto.py status

# Modify the file
echo "Hello, Gitto! This is a change." >> hello.txt

# Show the status
python ../gitto.py status

# Add the modified file to the staging area
python ../gitto.py add hello.txt

# Show the status
python ../gitto.py status

# Commit the changes
python ../gitto.py commit "Updated hello.txt"

# View the commit log
python ../gitto.py log

# Show differences between the last commit and its parent
python ../gitto.py show-diff <last_commit_hash>

# Modify the file
echo "Gibbrish" >> hello.txt

# Add the modified file to the staging area
python ../gitto.py add hello.txt

# Show the status
python ../gitto.py status

# Unstage the file
python ../gitto.py restore --staged hello.txt

# Show the status
python ../gitto.py status

# print hello.txt
cat hello.txt

# Restore the file to the previous commit
python ../gitto.py restore hello.txt

# print hello.txt
cat hello.txt
```

## License

This project is licensed under the MIT License.
