import os

from click.testing import CliRunner

from jupyter_cache.cache import JupyterCacheBase
from jupyter_cache.cli.commands import cmd_main, cmd_cache

NB_PATH = os.path.join(os.path.realpath(os.path.dirname(__file__)), "notebooks")


def test_base():
    runner = CliRunner()
    result = runner.invoke(cmd_main.jcache, "-v")
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    assert "jupyter-cache version" in result.output.strip(), result.output


def test_clear_cache(tmp_path):
    JupyterCacheBase(str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cmd_cache.clear_cache, ["-p", tmp_path], input="y")
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    assert "Cache cleared!" in result.output.strip(), result.output


def test_list_commits(tmp_path):
    db = JupyterCacheBase(str(tmp_path))
    db.commit_notebook_file(
        path=os.path.join(NB_PATH, "basic.ipynb"),
        uri="basic.ipynb",
        check_validity=False,
    )
    runner = CliRunner()
    result = runner.invoke(cmd_cache.list_commits, ["-p", tmp_path])
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    assert "basic.ipynb" in result.output.strip(), result.output


def test_commit_with_artifact(tmp_path):
    JupyterCacheBase(str(tmp_path))
    nb_path = os.path.join(NB_PATH, "basic.ipynb")
    a_path = os.path.join(NB_PATH, "artifact_folder", "artifact.txt")
    runner = CliRunner()
    result = runner.invoke(
        cmd_cache.commit_nb, ["-p", tmp_path, "--no-validate", "-nb", nb_path, a_path]
    )
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    assert "basic.ipynb" in result.output.strip(), result.output
    result = runner.invoke(cmd_cache.show_commit, ["-p", tmp_path, "1"])
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    assert "- artifact_folder/artifact.txt" in result.output.strip(), result.output


def test_commit_nbs(tmp_path):
    db = JupyterCacheBase(str(tmp_path))
    path = os.path.join(NB_PATH, "basic.ipynb")
    runner = CliRunner()
    result = runner.invoke(
        cmd_cache.commit_nbs, ["-p", tmp_path, "--no-validate", path]
    )
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    assert "basic.ipynb" in result.output.strip(), result.output
    assert db.list_commit_records()[0].uri == path


def test_remove_commits(tmp_path):
    db = JupyterCacheBase(str(tmp_path))
    db.commit_notebook_file(
        path=os.path.join(NB_PATH, "basic.ipynb"),
        uri="basic.ipynb",
        check_validity=False,
    )
    runner = CliRunner()
    result = runner.invoke(cmd_cache.remove_commits, ["-p", tmp_path, "1"])
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    assert "Success" in result.output.strip(), result.output
    assert db.list_commit_records() == []


def test_diff_nbs(tmp_path):
    db = JupyterCacheBase(str(tmp_path))
    path = os.path.join(NB_PATH, "basic.ipynb")
    path2 = os.path.join(NB_PATH, "basic_failing.ipynb")
    db.commit_notebook_file(path, check_validity=False)
    # nb_bundle = db.get_commit_bundle(1)
    # nb_bundle.nb.cells[0].source = "# New Title"
    # db.stage_notebook_bundle(nb_bundle)

    runner = CliRunner()
    result = runner.invoke(cmd_cache.diff_nb, ["-p", tmp_path, "1", path2])
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    print(result.output.splitlines()[2:])
    assert result.output.splitlines()[1:] == [
        "--- committed pk=1",
        f"+++ other: {path2}",
        "## inserted before nb/cells/0:",
        "+  code cell:",
        "+    source:",
        "+      raise Exception('oopsie!')",
        "",
        "## deleted nb/cells/0:",
        "-  code cell:",
        "-    execution_count: 2",
        "-    source:",
        "-      a=1",
        "-      print(a)",
        "-    outputs:",
        "-      output 0:",
        "-        output_type: stream",
        "-        name: stdout",
        "-        text:",
        "-          1",
        "",
        "",
        "Success!",
    ]


def test_stage_nbs(tmp_path):
    db = JupyterCacheBase(str(tmp_path))
    path = os.path.join(NB_PATH, "basic.ipynb")
    runner = CliRunner()
    result = runner.invoke(cmd_cache.stage_nbs, ["-p", tmp_path, path])
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    assert "basic.ipynb" in result.output.strip(), result.output
    assert db.list_staged_records()[0].uri == path


def test_unstage_nbs(tmp_path):
    db = JupyterCacheBase(str(tmp_path))
    path = os.path.join(NB_PATH, "basic.ipynb")
    runner = CliRunner()
    result = runner.invoke(cmd_cache.stage_nbs, ["-p", tmp_path, path])
    result = runner.invoke(cmd_cache.unstage_nbs, ["-p", tmp_path, path])
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    assert "basic.ipynb" in result.output.strip(), result.output
    assert db.list_staged_records() == []


def test_list_staged(tmp_path):
    db = JupyterCacheBase(str(tmp_path))
    db.commit_notebook_file(
        path=os.path.join(NB_PATH, "basic.ipynb"), check_validity=False
    )
    db.stage_notebook_file(path=os.path.join(NB_PATH, "basic.ipynb"))
    db.stage_notebook_file(path=os.path.join(NB_PATH, "basic_failing.ipynb"))

    runner = CliRunner()
    result = runner.invoke(cmd_cache.list_staged, ["-p", tmp_path])
    assert result.exception is None, result.output
    assert result.exit_code == 0, result.output
    print(result.output.strip())
    assert "basic.ipynb" in result.output.strip(), result.output
