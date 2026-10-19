"""Shell preflight tests: isolated state, read-only Git, no network or sudo."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "ubuntu_setup/bootstrap.sh"
BASH = shutil.which("bash")
GIT = shutil.which("git")


@unittest.skipUnless(BASH and GIT, "Bash and Git are required")
class ShellBootstrap(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.machine = self.root / "machine"
        self.home = self.machine / "home with spaces"
        self.cwd = self.machine / "work"
        self.bin = self.machine / "bin"
        for directory in (self.home, self.cwd, self.bin):
            directory.mkdir(parents=True)
        self.log = self.root / "calls.jsonl"
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_")}
        self.env.update(HOME=str(self.home), PATH=str(self.bin),
                        GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_OPTIONAL_LOCKS="0", TEST_LOG=str(self.log),
                        TEST_GIT=GIT, TEST_MKDIR=shutil.which("mkdir"),
                        TEST_MISSING="[]", TEST_DRY="1")
        stub = f"#!{sys.executable}\n" + '''import json, os, subprocess, sys
from pathlib import Path
name, args = Path(sys.argv[0]).name, sys.argv[1:]
with open(os.environ["TEST_LOG"], "a") as log:
    log.write(json.dumps([name, *args]) + "\\n")
dry = os.environ["TEST_DRY"] == "1"
if name in {"sudo", "apt-get", "mkdir"} or (name == "git" and args[0] == "clone"):
    if dry:
        sys.exit("Mutation attempted in dry run")
if name == "uname":
    print("Linux")
elif name == "dpkg-query":
    if args[-1] in json.loads(os.environ["TEST_MISSING"]):
        sys.exit(1)
    print("install ok installed")
elif name == "git":
    if args[0] == "clone":
        Path(args[-1]).mkdir()
    else:
        sys.exit(subprocess.call([os.environ["TEST_GIT"], *args]))
elif name == "mkdir":
    sys.exit(subprocess.call([os.environ["TEST_MKDIR"], *args]))
elif name == "python3":
    if dry and "--dry-run" not in args:
        sys.exit("Python invoked without --dry-run")
    if os.environ.get("TEST_REAL_PYTHON") == "1":
        sys.exit(subprocess.call([sys.executable, *args]))
'''
        for name in ("uname", "dpkg-query", "apt-get", "sudo", "git", "python3", "mkdir"):
            executable = self.bin / name
            executable.write_text(stub)
            executable.chmod(0o700)
        (self.bin / "dirname").symlink_to(shutil.which("dirname"))

    def git(self, destination, *args):
        return subprocess.run([GIT, "-C", str(destination), *args],
                              env=self.env, check=True, capture_output=True)

    def checkout(self, destination=None, origin="https://github.com/Bloblblobl/dotfiles.git"):
        destination = destination or self.home / "git/dotfiles"
        destination.mkdir(parents=True)
        self.git(destination, "init", "-q")
        setup = destination / "ubuntu_setup"
        setup.mkdir()
        (setup / "bootstrap.py").write_bytes(SCRIPT.with_suffix(".py").read_bytes())
        (setup / "symlink_fs").mkdir()
        (setup / "symlink_fs/.testconfig").write_text("test\n")
        self.git(destination, "add", ".")
        self.git(destination, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
        self.git(destination, "remote", "add", "origin", origin)
        return destination

    def snapshot(self):
        # Ignore access times; reads may update those. Include index/config, modes,
        # modification times, symlinks and directories to catch incidental writes.
        result = {}
        for p in [self.machine, *self.machine.rglob("*")]:
            stat = p.lstat()
            content = os.readlink(p) if p.is_symlink() else p.read_bytes() if p.is_file() else None
            result[str(p.relative_to(self.machine))] = (stat.st_mode, stat.st_mtime_ns, content)
        return result

    def run_shell(self, entered="", dry=True, options=(), real_python=False, dry_flag="--dry-run"):
        self.env["TEST_DRY"] = "1" if dry else "0"
        self.env["TEST_REAL_PYTHON"] = "1" if real_python else "0"
        before = self.snapshot()
        result = subprocess.run([BASH, str(SCRIPT), *([dry_flag] if dry else []), *options],
                                input=entered + "\n", text=True, capture_output=True,
                                cwd=self.cwd, env=self.env)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        if dry:
            self.assertEqual(before, self.snapshot(), "Dry run changed machine state")
            self.assertFalse(any(c[0] in {"sudo", "apt-get", "mkdir"} or
                                 c[:2] == ["git", "clone"] for c in calls), calls)
        return result, calls

    def assert_skipped(self, result, calls, status):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(status, result.stdout)
        self.assertIn("Python dry-run skipped", result.stdout)
        self.assertFalse(any(c[0] == "python3" for c in calls))

    def assert_live_blocked(self, entered, destination):
        before = self.snapshot()
        result, calls = self.run_shell(entered, dry=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"Destination already exists: {destination}", result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(any(c[0] in {"sudo", "apt-get", "mkdir", "python3"} or
                             c[:2] == ["git", "clone"] for c in calls), calls)

    def test_ready_runs_real_python_dry_run_without_writes(self):
        self.checkout()
        result, calls = self.run_shell(real_python=True, options=("--skip-github",))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[OK] Repository checkout verified", result.stdout)
        self.assertIn("create link:", result.stdout)
        self.assertEqual(sum(c[0] == "python3" for c in calls), 1)
        self.assertIn("--skip-github", next(c for c in calls if c[0] == "python3"))

    def test_short_dry_run_option(self):
        self.checkout()
        result, calls = self.run_shell(dry_flag="-d")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(c[0] == "python3" and "--dry-run" in c for c in calls))

    def test_missing_dependencies(self):
        self.checkout()
        for package in ("git", "python3", "ca-certificates"):
            with self.subTest(package=package):
                self.env["TEST_MISSING"] = json.dumps([package])
                result, calls = self.run_shell()
                self.assert_skipped(result, calls, f"[PENDING] {package}")

    def test_missing_executable(self):
        self.checkout()
        for name in ("git", "python3"):
            with self.subTest(command=name):
                executable = self.bin / name
                stub = executable.read_bytes()
                executable.unlink()
                result, calls = self.run_shell()
                self.assert_skipped(result, calls, f"[PENDING] {name}")
                executable.write_bytes(stub)
                executable.chmod(0o700)

    def test_missing_directories(self):
        result, calls = self.run_shell()
        self.assert_skipped(result, calls, f"[PENDING] {self.home / 'git'} does not exist")
        self.assertIn("[PENDING] Repository not cloned", result.stdout)

    def test_missing_repository(self):
        (self.home / "git").mkdir()
        result, calls = self.run_shell()
        self.assert_skipped(result, calls, "[PENDING] Repository not cloned")
        self.assertIn(f"[OK] {self.home / 'git'} exists", result.stdout)

    def test_unrelated_directory(self):
        (self.home / "git/dotfiles").mkdir(parents=True)
        self.assert_skipped(*self.run_shell(), "[BLOCKED] Not a usable dotfiles checkout")

    def test_wrong_repository(self):
        self.checkout(origin="https://github.com/example/other.git")
        self.assert_skipped(*self.run_shell(), "[BLOCKED] Checkout origin")

    def test_invalid_head(self):
        destination = self.home / "git/dotfiles"
        destination.mkdir(parents=True)
        self.git(destination, "init", "-q")
        self.assert_skipped(*self.run_shell(), "[BLOCKED] Not a usable dotfiles checkout")

    def test_missing_python_entry_point(self):
        destination = self.checkout()
        (destination / "ubuntu_setup/bootstrap.py").unlink()
        self.assert_skipped(*self.run_shell(), "[BLOCKED] Not a usable dotfiles checkout")

    def test_missing_configuration_tree(self):
        destination = self.checkout()
        config = destination / "ubuntu_setup/symlink_fs"
        (config / ".testconfig").unlink()
        config.rmdir()
        self.assert_skipped(*self.run_shell(), "[BLOCKED] Not a usable dotfiles checkout")

    def test_nested_directory_is_not_checkout_root(self):
        destination = self.checkout()
        (destination / "nested").mkdir()
        self.assert_skipped(*self.run_shell(str(destination / "nested")),
                            "[BLOCKED] Not a usable dotfiles checkout")

    def test_file_destination(self):
        destination = self.home / "git/dotfiles"
        destination.parent.mkdir()
        destination.write_text("preserve")
        self.assert_skipped(*self.run_shell(), "[BLOCKED]")

    def test_dangling_destination_in_both_modes(self):
        destination = self.home / "git/dotfiles"
        destination.parent.mkdir()
        destination.symlink_to(self.home / "missing")
        result, calls = self.run_shell()
        self.assert_skipped(result, calls, "[BLOCKED] Destination is a dangling symlink")
        self.assert_live_blocked("", destination)
        self.assertTrue(destination.is_symlink())
        self.assertFalse((self.home / "missing").exists())

    def test_blocked_parent(self):
        (self.home / "git").symlink_to(self.home / "missing")
        self.assert_skipped(*self.run_shell(), "[BLOCKED]")

    def path_cases(self):
        return [("", self.home / "git/dotfiles"),
                 ("~/projects/dotfiles", self.home / "projects/dotfiles"),
                 (str(self.machine / "absolute/dotfiles"), self.machine / "absolute/dotfiles"),
                 ("relative/dotfiles", self.cwd / "relative/dotfiles"),
                 ("~/space projects/dotfiles", self.home / "space projects/dotfiles"),
                 (str(self.machine / "absolute space/dotfiles"), self.machine / "absolute space/dotfiles"),
                 ("relative space/dotfiles", self.cwd / "relative space/dotfiles"),
                 ("relative~name/dotfiles", self.cwd / "relative~name/dotfiles")]

    def test_path_resolution_and_forwarding(self):
        # All paths refer to an actual checkout, not a mocked Git response.
        for entered, destination in self.path_cases():
            with self.subTest(path=entered):
                self.checkout(destination)
                self.log.unlink(missing_ok=True)
                result, calls = self.run_shell(entered, options=("--skip-github",))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("[OK] Repository checkout verified", result.stdout)
                forwarded = next(c for c in calls if c[0] == "python3")
                resolved = str(destination) if not entered or entered.startswith(("~/", "/")) else entered
                self.assertEqual(forwarded, ["python3", resolved + "/ubuntu_setup/bootstrap.py",
                                             "--dry-run", "--skip-github"])

    def test_live_clone_and_forwarding(self):
        for entered, destination in self.path_cases():
            with self.subTest(path=entered):
                self.log.unlink(missing_ok=True)
                result, calls = self.run_shell(entered, dry=False, options=("--skip-github",))
                resolved = str(destination) if not entered or entered.startswith(("~/", "/")) else entered
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(["sudo", "apt-get", "update"], calls)
                self.assertIn(["sudo", "apt-get", "install", "-y", "git", "python3", "ca-certificates"], calls)
                self.assertIn(["git", "clone", "https://github.com/Bloblblobl/dotfiles.git", resolved], calls)
                self.assertIn(["python3", resolved + "/ubuntu_setup/bootstrap.py", "--skip-github"], calls)

    def test_live_refuses_occupied_destinations_before_mutations(self):
        for kind in ("file", "directory", "file-link", "directory-link"):
            with self.subTest(kind=kind):
                destination = self.home / (kind + " with spaces")
                if kind == "file":
                    destination.write_text("preserve")
                elif kind == "directory":
                    destination.mkdir()
                else:
                    target = self.home / (kind + " target")
                    if kind == "file-link":
                        target.write_text("preserve")
                    else:
                        target.mkdir()
                    destination.symlink_to(target)
                self.log.unlink(missing_ok=True)
                self.assert_live_blocked("~/" + destination.name, destination)

    def test_ssh_origin_is_satisfied(self):
        self.checkout(origin="git@github.com:Bloblblobl/dotfiles.git")
        result, calls = self.run_shell()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[OK] Repository checkout verified", result.stdout)
        self.assertTrue(any(c[0] == "python3" for c in calls))

    def test_live_refuses_existing_checkout(self):
        destination = self.checkout()
        self.assert_live_blocked("", destination)


if __name__ == "__main__":
    unittest.main()
