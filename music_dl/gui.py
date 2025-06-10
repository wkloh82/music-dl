# GUI module for music-dl

from __future__ import annotations

import sys
import logging
from typing import List

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QCheckBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QTextEdit,
    QProgressBar,
    QMessageBox,
    QSpinBox,
)
from PyQt6.QtCore import Qt

from .source import MusicSource
from .song import BasicSong
from . import config


class MainWindow(QMainWindow):
    """Main GUI window for music-dl."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("music-dl")

        self.ms = MusicSource()
        config.init()

        self._setup_ui()
        self._connect_signals()

        self.songs: List[BasicSong] = []

    def _setup_ui(self) -> None:
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)

        # Input fields
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("Keyword search")
        self.single_edit = QLineEdit()
        self.single_edit.setPlaceholderText("Single song URL")
        self.playlist_edit = QLineEdit()
        self.playlist_edit.setPlaceholderText("Playlist URL")

        layout.addWidget(QLabel("Keyword:"))
        layout.addWidget(self.keyword_edit)
        layout.addWidget(QLabel("Single URL:"))
        layout.addWidget(self.single_edit)
        layout.addWidget(QLabel("Playlist URL:"))
        layout.addWidget(self.playlist_edit)

        # Options layout
        opts_layout = QHBoxLayout()
        layout.addLayout(opts_layout)

        self.source_combo = QComboBox()
        self.source_combo.addItems(["baidu", "kugou", "netease", "qq", "migu"])
        opts_layout.addWidget(QLabel("Source:"))
        opts_layout.addWidget(self.source_combo)

        self.number_spin = QSpinBox()
        self.number_spin.setRange(1, 50)
        self.number_spin.setValue(5)
        opts_layout.addWidget(QLabel("Number:"))
        opts_layout.addWidget(self.number_spin)

        self.lyrics_check = QCheckBox("Lyrics")
        opts_layout.addWidget(self.lyrics_check)
        self.cover_check = QCheckBox("Cover")
        opts_layout.addWidget(self.cover_check)

        # Search button
        self.search_button = QPushButton("Search")
        layout.addWidget(self.search_button)

        # Table for results
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Title",
            "Singer",
            "Album",
            "Size",
            "Source",
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Download button
        self.download_button = QPushButton("Download Selected")
        layout.addWidget(self.download_button)

        # Progress and log
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        layout.addWidget(self.log_edit)

    def _connect_signals(self) -> None:
        self.search_button.clicked.connect(self.do_search)
        self.download_button.clicked.connect(self.download_selected)

    # Helper to log messages
    def log(self, msg: str) -> None:
        self.log_edit.append(msg)

    def do_search(self) -> None:
        keyword = self.keyword_edit.text().strip()
        single_url = self.single_edit.text().strip()
        playlist_url = self.playlist_edit.text().strip()

        config.set("lyrics", self.lyrics_check.isChecked())
        config.set("cover", self.cover_check.isChecked())
        config.set("number", self.number_spin.value())

        if keyword:
            config.set("keyword", keyword)
            sources = [self.source_combo.currentText()]
            self.songs = self.ms.search(keyword, sources)[: self.number_spin.value()]
        elif single_url:
            config.set("url", single_url)
            song = self.ms.single(single_url)
            self.songs = [song] if song else []
        elif playlist_url:
            config.set("playlist", playlist_url)
            self.songs = self.ms.playlist(playlist_url)
        else:
            QMessageBox.warning(self, "music-dl", "Please provide search keyword or URL")
            return

        self.populate_table()

    def populate_table(self) -> None:
        self.table.setRowCount(0)
        for i, song in enumerate(self.songs):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(song.title))
            self.table.setItem(i, 1, QTableWidgetItem(song.singer))
            self.table.setItem(i, 2, QTableWidgetItem(song.album))
            self.table.setItem(i, 3, QTableWidgetItem(str(song.size)))
            self.table.setItem(i, 4, QTableWidgetItem(song.source))

    def download_selected(self) -> None:
        rows = sorted(set(idx.row() for idx in self.table.selectedIndexes()))
        if not rows:
            QMessageBox.information(self, "music-dl", "No items selected")
            return

        self.progress.setMaximum(len(rows))
        self.progress.setValue(0)
        for count, row in enumerate(rows, 1):
            song = self.songs[row]
            self.log(f"Downloading: {song.title} - {song.singer}")
            try:
                song.download()
                self.log("Finished: " + song.song_fullname)
            except Exception as e:
                logging.exception(e)
                self.log(f"Error: {e}")
            self.progress.setValue(count)
        self.log("Done")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
