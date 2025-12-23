"""
Settings page for HandyMouse application.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox, QSlider, QDoubleSpinBox, QSpinBox, 
    QScrollArea, QFrame, QGroupBox, QPushButton, QMessageBox,
    QSizePolicy
)
from PySide6.QtCore import Qt, QEvent, QObject, Signal, QSize
from core.config_manager import config


class ScrollPassthroughFilter(QObject):
    """
    Event filter that passes scroll wheel events to the parent scroll area
    instead of adjusting slider/spinbox values.
    """
    def __init__(self, scroll_area: QScrollArea, parent=None):
        super().__init__(parent)
        self.scroll_area = scroll_area

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            if self.scroll_area and self.scroll_area.verticalScrollBar():
                scroll_bar = self.scroll_area.verticalScrollBar()
                delta = event.angleDelta().y()
                scroll_bar.setValue(scroll_bar.value() - delta // 2)
            return True
        return False


class ResettableLabel(QLabel):
    """Label that changes to 'Reset?' on hover and emits signal on click."""
    
    reset_requested = Signal(str)

    def __init__(self, key, text, parent=None):
        super().__init__(text, parent)
        self.key = key
        self.original_text = text
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("color: #c0c0c0;")
        
        # Calculate fixed size to prevent hitbox flickering
        fm = self.fontMetrics()
        w_orig = fm.horizontalAdvance(text)
        w_reset = fm.horizontalAdvance("Reset?")
        self.setMinimumWidth(max(w_orig, w_reset) + 10)

    def enterEvent(self, event):
        self.setText("Reset?")
        self.setStyleSheet("color: #3a8fff; font-weight: 500;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setText(self.original_text)
        self.setStyleSheet("color: #c0c0c0;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.reset_requested.emit(self.key)


class SettingsPage(QWidget):
    """Settings page with configuration options."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        content.setStyleSheet("background-color: #0a0a0a;")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(12)
        
        self.scroll_filter = ScrollPassthroughFilter(self.scroll)
        
        # Container for dynamic settings
        self.settings_container = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_container)
        self.settings_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_layout.setSpacing(0)
        
        self.content_layout.addWidget(self.settings_container)
        
        # Populate settings
        self.refresh_settings()
        
        self.content_layout.addStretch()
        
        # Footer with actions
        self._add_footer()
        
        self.scroll.setWidget(content)
        main_layout.addWidget(self.scroll)

    def _add_footer(self):
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 20, 12, 0)
        footer_layout.setSpacing(16)
        
        # Show Developer Settings Toggle
        self.dev_btn = QPushButton()
        self.dev_btn.setCheckable(True)
        self.dev_btn.clicked.connect(self.toggle_developer_settings)
        self._update_dev_btn_text()
        self.dev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dev_btn.setMinimumHeight(36)
        
        # Reset Defaults Button
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_to_defaults)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setMinimumHeight(36)
        
        footer_layout.addWidget(self.dev_btn)
        footer_layout.addWidget(reset_btn)
        
        self.content_layout.addWidget(footer)

    def _update_dev_btn_text(self):
        is_dev = config.get("SHOW_DEVELOPER_SETTINGS")
        self.dev_btn.setText("Hide Developer Settings" if is_dev else "Show Developer Settings")
        self.dev_btn.setChecked(is_dev)

    def toggle_developer_settings(self):
        current = config.get("SHOW_DEVELOPER_SETTINGS")
        config.set("SHOW_DEVELOPER_SETTINGS", not current)
        self._update_dev_btn_text()
        self.refresh_settings()

    def reset_to_defaults(self):
        confirm = QMessageBox.question(
            self, 
            "Reset Settings", 
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            config.reset_to_defaults()
            self._update_dev_btn_text()
            self.refresh_settings()
            
    def _on_single_reset(self, key):
        """Handle reset of a single setting."""
        config.reset_setting(key)
        self.refresh_settings()

    def refresh_settings(self):
        # Clear existing settings
        while self.settings_layout.count():
            child = self.settings_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self._populate_settings()

    def _populate_settings(self):
        for key, item in config._default_config.items():
            if isinstance(item, dict) and "content" in item:
                if key == "DEVELOPER_SETTINGS" and not config.get("SHOW_DEVELOPER_SETTINGS"):
                    continue
                self._add_category(key, item)

    def _add_category(self, category_key: str, category_data: dict):
        display_name = category_key.replace("_", " ").title()
        
        group = QGroupBox(display_name)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(0)
        group_layout.setContentsMargins(12, 16, 12, 12)
        
        if "description" in category_data:
            desc = QLabel(category_data["description"])
            desc.setStyleSheet("color: #606060; margin-bottom: 12px;")
            desc.setWordWrap(True)
            desc.setFont(self.font())  # Inherit font size/family
            # Make font slightly smaller/italic if desired
            f = desc.font()
            f.setPointSize(f.pointSize() - 1)
            desc.setFont(f)
            group_layout.addWidget(desc)
        
        content = category_data.get("content", {})
        items_added = 0
        
        for key, default_item in content.items():
            current_value = config.get(key)
            
            if isinstance(default_item, dict) and "value" in default_item:
                if items_added > 0:
                    separator = QFrame()
                    separator.setFrameShape(QFrame.Shape.HLine)
                    separator.setFixedHeight(1)
                    separator.setStyleSheet("background-color: #1a1a1a;")
                    group_layout.addWidget(separator)
                
                widget = self._create_setting_widget(key, default_item, current_value)
                group_layout.addWidget(widget)
                items_added += 1
        
        self.settings_layout.addWidget(group)

    def _create_setting_widget(self, key: str, item_metadata: dict, current_value) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background-color: transparent;")
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 12, 0, 12)
        row_layout.setSpacing(6)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        
        # Resettable Label
        label_text = key.replace("_", " ").title()
        lbl = ResettableLabel(key, label_text)
        lbl.reset_requested.connect(self._on_single_reset)
        top_row.addWidget(lbl, 1, Qt.AlignmentFlag.AlignTop)
        
        control = self._create_control(key, item_metadata, current_value)
        top_row.addWidget(control, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        row_layout.addLayout(top_row)
        
        if "description" in item_metadata and item_metadata["description"]:
            desc_lbl = QLabel(item_metadata["description"])
            desc_lbl.setStyleSheet("color: #505050; font-size: 11px;")
            desc_lbl.setWordWrap(True)
            row_layout.addWidget(desc_lbl)
        
        return row

    def _create_control(self, key: str, item_metadata: dict, current_value) -> QWidget:
        value_type = type(current_value)
        rng = item_metadata.get("range")
        
        if value_type == bool:
            return self._create_toggle(key, current_value)
        elif value_type == int and rng:
            return self._create_int_slider(key, current_value, rng)
        elif value_type == float and rng:
            return self._create_float_slider(key, current_value, rng)
        elif value_type in (int, float):
            return self._create_spinbox(key, current_value, value_type)
        
        return QLabel(str(current_value))

    def _create_toggle(self, key: str, current_value: bool) -> QWidget:
        chk = QCheckBox()
        chk.setChecked(current_value)
        chk.stateChanged.connect(lambda state, k=key: config.set(k, bool(state)))
        return chk

    def _create_int_slider(self, key: str, current_value: int, rng: list) -> QWidget:
        container = QWidget()
        container.setFixedWidth(220)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        min_val, max_val = int(rng[0]), int(rng[1])
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(current_value)
        slider.setMinimumWidth(120)
        slider.installEventFilter(self.scroll_filter)
        
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(current_value)
        spin.setFixedWidth(70)
        spin.installEventFilter(self.scroll_filter)
        
        def on_slider_dragging(v, s=spin):
            # Update spinbox display while dragging (visual feedback only)
            s.blockSignals(True)
            s.setValue(v)
            s.blockSignals(False)
        
        def on_slider_released(s=slider, k=key):
            # Only update config when slider is released
            v = s.value()
            config.set(k, v)
        
        def on_spin_change(v, s=slider, k=key):
            # Spinbox changes apply immediately
            config.set(k, v)
            s.blockSignals(True)
            s.setValue(v)
            s.blockSignals(False)
        
        # Update spinbox display while dragging (but don't save config)
        slider.valueChanged.connect(on_slider_dragging)
        # Only save config when slider is released
        slider.sliderReleased.connect(on_slider_released)
        spin.valueChanged.connect(on_spin_change)
        
        layout.addWidget(slider)
        layout.addWidget(spin)
        
        return container

    def _create_float_slider(self, key: str, current_value: float, rng: list) -> QWidget:
        container = QWidget()
        container.setFixedWidth(240)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        min_val, max_val = float(rng[0]), float(rng[1])
        steps = 100
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, steps)
        slider_val = int((current_value - min_val) / (max_val - min_val) * steps) if (max_val > min_val) else 0
        slider.setValue(slider_val)
        slider.setMinimumWidth(120)
        slider.installEventFilter(self.scroll_filter)
        
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep((max_val - min_val) / steps)
        spin.setValue(current_value)
        spin.setDecimals(3)
        spin.setFixedWidth(80)
        spin.installEventFilter(self.scroll_filter)
        
        def on_slider_dragging(v, s=spin, mn=min_val, mx=max_val, st=steps):
            # Update spinbox display while dragging (visual feedback only)
            val = mn + (v / st) * (mx - mn)
            s.blockSignals(True)
            s.setValue(val)
            s.blockSignals(False)
        
        def on_slider_released(s=slider, k=key, mn=min_val, mx=max_val, st=steps):
            # Only update config when slider is released
            v = s.value()
            val = mn + (v / st) * (mx - mn)
            config.set(k, val)
        
        def on_spin_change(v, s=slider, k=key, mn=min_val, mx=max_val, st=steps):
            # Spinbox changes apply immediately
            config.set(k, v)
            if mx > mn:
                slider_val = int((v - mn) / (mx - mn) * st)
                s.blockSignals(True)
                s.setValue(slider_val)
                s.blockSignals(False)
        
        # Update spinbox display while dragging (but don't save config)
        slider.valueChanged.connect(on_slider_dragging)
        # Only save config when slider is released
        slider.sliderReleased.connect(on_slider_released)
        spin.valueChanged.connect(on_spin_change)
        
        layout.addWidget(slider)
        layout.addWidget(spin)
        
        return container

    def _create_spinbox(self, key: str, current_value, value_type) -> QWidget:
        if value_type == int:
            spin = QSpinBox()
            spin.setRange(-9999, 9999)
            spin.setValue(current_value)
            spin.valueChanged.connect(lambda v, k=key: config.set(k, v))
        else:
            spin = QDoubleSpinBox()
            spin.setRange(-9999.0, 9999.0)
            spin.setValue(current_value)
            spin.setDecimals(3)
            spin.valueChanged.connect(lambda v, k=key: config.set(k, v))
        
        spin.setFixedWidth(80)
        spin.installEventFilter(self.scroll_filter)
        return spin
