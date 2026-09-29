"""设置对话框。"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QCheckBox, QSpinBox, QGroupBox,
    QFormLayout, QMessageBox, QWidget,
)

from core.ringtone import RingtoneManager


class SettingsDialog(QDialog):
    def __init__(self, settings, stats, ringtone: RingtoneManager, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._stats = stats
        self._ringtone = ringtone
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── 外观 ──
        appearance = QGroupBox("外观")
        app_form = QFormLayout(appearance)
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["深色", "浅色"])
        app_form.addRow("主题", self._theme_combo)

        self._top_check = QCheckBox("窗口始终置顶")
        app_form.addRow(self._top_check)

        opacity_row = QHBoxLayout()
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(40, 100)
        self._opacity_lbl = QLabel("100%")
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_lbl.setText(f"{v}%"))
        opacity_row.addWidget(self._opacity_slider)
        opacity_row.addWidget(self._opacity_lbl)
        app_form.addRow("透明度", opacity_row)

        self._hover_check = QCheckBox("鼠标悬停时临时恢复不透明")
        app_form.addRow(self._hover_check)
        layout.addWidget(appearance)

        # ── 铃声 ──
        sound = QGroupBox("铃声")
        sound_form = QFormLayout(sound)
        self._ringtone_combo = QComboBox()
        self._ringtone_combo.setMinimumWidth(180)
        sound_form.addRow("提醒铃声", self._ringtone_combo)

        preview_row = QHBoxLayout()
        self._preview_btn = QPushButton("试听")
        self._preview_btn.clicked.connect(self._on_preview)
        self._stop_preview_btn = QPushButton("停止")
        self._stop_preview_btn.clicked.connect(self._ringtone.stop)
        preview_row.addWidget(self._preview_btn)
        preview_row.addWidget(self._stop_preview_btn)
        preview_row.addStretch()
        sound_form.addRow(preview_row)

        vol_row = QHBoxLayout()
        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_lbl = QLabel("80%")
        self._vol_slider.valueChanged.connect(
            lambda v: self._vol_lbl.setText(f"{v}%"))
        vol_row.addWidget(self._vol_slider)
        vol_row.addWidget(self._vol_lbl)
        sound_form.addRow("音量", vol_row)

        self._duration_combo = QComboBox()
        self._duration_combo.addItem("响到用户确认", "until_confirm")
        self._duration_combo.addItem("最多响 15 秒", "15s")
        sound_form.addRow("响铃时长", self._duration_combo)

        self._import_btn = QPushButton("导入音频…")
        self._import_btn.clicked.connect(self._on_import)
        sound_form.addRow(self._import_btn)
        layout.addWidget(sound)

        # ── 番茄钟 ──
        pomo = QGroupBox("番茄钟")
        pomo_form = QFormLayout(pomo)
        self._focus_spin = QSpinBox()
        self._focus_spin.setRange(1, 120)
        pomo_form.addRow("专注时长（分）", self._focus_spin)

        self._short_spin = QSpinBox()
        self._short_spin.setRange(1, 60)
        pomo_form.addRow("短休息（分）", self._short_spin)

        self._long_spin = QSpinBox()
        self._long_spin.setRange(1, 120)
        pomo_form.addRow("长休息（分）", self._long_spin)

        self._every_spin = QSpinBox()
        self._every_spin.setRange(1, 20)
        pomo_form.addRow("几个番茄后长休息", self._every_spin)

        self._auto_check = QCheckBox("自动开始下一阶段")
        pomo_form.addRow(self._auto_check)
        layout.addWidget(pomo)

        # ── 系统 ──
        system = QGroupBox("系统")
        sys_form = QFormLayout(system)
        self._tray_check = QCheckBox("关闭按钮最小化到托盘")
        sys_form.addRow(self._tray_check)

        self._autostart_check = QCheckBox("开机自动启动")
        sys_form.addRow(self._autostart_check)
        layout.addWidget(system)

        # ── 统计 ──
        stats_box = QGroupBox("统计")
        stats_layout = QVBoxLayout(stats_box)
        today = self._stats.today_summary()
        total = self._stats.total_summary()
        stats_layout.addWidget(QLabel(f"今日：番茄 {today['pomodoros']} 个 · 专注 {today['minutes']} 分钟"))
        stats_layout.addWidget(QLabel(f"累计：番茄 {total['pomodoros']} 个 · 专注 {total['hours']:.1f} 小时"))
        clear_row = QHBoxLayout()
        clear_row.addStretch()
        self._clear_btn = QPushButton("清空统计")
        self._clear_btn.setObjectName("danger")
        self._clear_btn.clicked.connect(self._on_clear_stats)
        clear_row.addWidget(self._clear_btn)
        stats_layout.addLayout(clear_row)
        layout.addWidget(stats_box)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("取消")
        cancel.setObjectName("flat")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        save = QPushButton("保存")
        save.clicked.connect(self._on_save)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _load_values(self):
        # 外观
        theme = self._settings.get("theme", "dark")
        self._theme_combo.setCurrentIndex(0 if theme == "dark" else 1)
        self._top_check.setChecked(self._settings.get("always_on_top", True))
        self._opacity_slider.setValue(int(self._settings.get("opacity", 0.95) * 100))
        self._hover_check.setChecked(self._settings.get("hover_boost", True))

        # 铃声
        self._refresh_ringtone_list()
        self._vol_slider.setValue(self._settings.get("volume", 80))
        dur = self._settings.get("ring_duration", "until_confirm")
        self._duration_combo.setCurrentIndex(0 if dur == "until_confirm" else 1)

        # 番茄钟
        self._focus_spin.setValue(self._settings.get("pomodoro.focus", 25))
        self._short_spin.setValue(self._settings.get("pomodoro.short_break", 5))
        self._long_spin.setValue(self._settings.get("pomodoro.long_break", 15))
        self._every_spin.setValue(self._settings.get("pomodoro.long_break_every", 4))
        self._auto_check.setChecked(self._settings.get("pomodoro.auto_start_next", True))

        # 系统
        self._tray_check.setChecked(self._settings.get("close_to_tray", True))
        self._autostart_check.setChecked(self._settings.get("autostart", False))

    def _refresh_ringtone_list(self):
        self._ringtone_combo.clear()
        current = self._settings.get("ringtone", "default_1.wav")
        idx = 0
        for rt in self._ringtone.list():
            self._ringtone_combo.addItem(rt.label, rt.name)
            if rt.name == current:
                idx = self._ringtone_combo.count() - 1
        self._ringtone_combo.setCurrentIndex(idx)

    def _on_preview(self):
        name = self._ringtone_combo.currentData()
        if name:
            self._ringtone.preview(name)

    def _on_import(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "导入铃声", "", "音频文件 (*.wav *.mp3)")
        if path:
            new_name = self._ringtone.import_file(path)
            if new_name:
                self._refresh_ringtone_list()
                # 选中新导入的
                for i in range(self._ringtone_combo.count()):
                    if self._ringtone_combo.itemData(i) == new_name:
                        self._ringtone_combo.setCurrentIndex(i)
                        break
            else:
                QMessageBox.warning(self, "导入失败", "不支持的文件格式。")

    def _on_clear_stats(self):
        btn = QMessageBox.question(
            self, "清空统计", "确定清空所有专注记录吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if btn == QMessageBox.StandardButton.Yes:
            self._stats.clear()
            # 刷新统计标签
            today = self._stats.today_summary()
            total = self._stats.total_summary()
            # 简单提示
            QMessageBox.information(self, "已清空", "统计记录已清空。")

    def _on_save(self):
        self._settings.set("theme", "dark" if self._theme_combo.currentIndex() == 0 else "light")
        self._settings.set("always_on_top", self._top_check.isChecked())
        self._settings.set("opacity", self._opacity_slider.value() / 100.0)
        self._settings.set("hover_boost", self._hover_check.isChecked())

        rt_name = self._ringtone_combo.currentData()
        if rt_name:
            self._settings.set("ringtone", rt_name)
        self._settings.set("volume", self._vol_slider.value())
        self._settings.set("ring_duration", self._duration_combo.currentData())

        self._settings.set("pomodoro.focus", self._focus_spin.value())
        self._settings.set("pomodoro.short_break", self._short_spin.value())
        self._settings.set("pomodoro.long_break", self._long_spin.value())
        self._settings.set("pomodoro.long_break_every", self._every_spin.value())
        self._settings.set("pomodoro.auto_start_next", self._auto_check.isChecked())

        self._settings.set("close_to_tray", self._tray_check.isChecked())
        self._settings.set("autostart", self._autostart_check.isChecked())

        self.accept()
