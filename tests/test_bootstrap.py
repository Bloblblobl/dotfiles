import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bootstrap', Path(__file__).resolve().parents[1] / 'ubuntu_setup/bootstrap.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class Links(unittest.TestCase):
    def test_install_idempotence_dry_run_and_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tree, home = root/'tree', root/'home'
            tree.mkdir(); home.mkdir()
            (tree/'a').write_text('a')
            with patch.object(b, 'SYMLINK_DIR', tree), patch.object(Path, 'home', return_value=home):
                b.create_symlinks(True)
                self.assertFalse((home/'a').exists())
                b.create_symlinks()
                self.assertEqual((home/'a').resolve(), tree/'a')
                inode = (home/'a').lstat().st_ino
                b.create_symlinks()
                self.assertEqual(inode, (home/'a').lstat().st_ino)
                (home/'a').unlink(); (home/'a').symlink_to(root/'missing')
                b.create_symlinks()
                self.assertEqual((home/'a').resolve(), tree/'a')
                (tree/'b').write_text('b'); (home/'b').write_text('preserve')
                (home/'a').unlink()
                with self.assertRaises(RuntimeError):
                    b.create_symlinks()
                self.assertFalse((home/'a').exists())
                self.assertEqual((home/'b').read_text(), 'preserve')
                (home/'b').unlink(); (home/'b').mkdir()
                with self.assertRaises(RuntimeError):
                    b.create_symlinks()

    def test_github_dry_run_does_not_execute_commands(self):
        with patch.object(b.subprocess, 'run') as run:
            b.configure_github(True)
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
