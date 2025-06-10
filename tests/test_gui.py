import os
from music_dl import gui


def test_import_gui():
    assert gui.MainWindow is not None


def test_gui_launch(capsys):
    """Launch the GUI in a minimal way."""
    # Use Qt's offscreen platform to avoid the need for a display
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        app = gui.QApplication([])
    except Exception:
        # Qt might not be available in test environment
        return
    window = gui.MainWindow()
    window.show()
    app.processEvents()
    # immediately exit
    window.close()
    app.exit()
    out, err = capsys.readouterr()
    assert err == ""

def test_gui_download(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        app = gui.QApplication([])
    except Exception:
        return
    gui.config.init()
    gui.config.set("outdir", str(tmp_path))
    gui.config.set("verbose", True)

    window = gui.MainWindow()
    song = gui.BasicSong()
    song.title = "cheering"
    song.singer = "crowd"
    song.ext = "mp3"
    song.album = "sample"
    song.rate = 128
    song.source = "sample"
    song.duration = 28
    song.song_url = "https://github.com/0xHJK/music-dl/raw/master/static/sample.mp3"
    window.songs = [song]
    window.populate_table()
    window.table.selectRow(0)
    window.download_selected()
    assert (tmp_path / "crowd - cheering.mp3").exists()
    app.exit()
