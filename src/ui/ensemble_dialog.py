from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QCheckBox, QLabel, QComboBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from src.ui.style import COLORS

class EnsembleConfigDialog(QDialog):
    def __init__(self, available_models, selected_models=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ensemble Configuration")
        self.resize(400, 500)
        self.setStyleSheet(f"background-color: {COLORS['background']}; color: {COLORS['text']};")
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Select Models to Ensemble:"))
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"background-color: {COLORS['surface']}; border: 1px solid #333; border-radius: 8px;")
        
        if selected_models is None:
            selected_models = []
            
        for model in available_models:
            item = QListWidgetItem(model)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if model in selected_models:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)
            
        layout.addWidget(self.list_widget)
        
        # Algorithm selection
        algo_layout = QHBoxLayout()
        algo_layout.addWidget(QLabel("Algorithm:"))
        self.combo_algo = QComboBox()
        self.combo_algo.addItems(["Average (Mean)", "Max (Aggressive)", "Min (Conservative)"])
        self.combo_algo.setStyleSheet(f"background-color: {COLORS['surface']}; color: {COLORS['text']}; border: 1px solid #333; padding: 5px;")
        algo_layout.addWidget(self.combo_algo)
        layout.addLayout(algo_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_selected_models(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected

    def get_algorithm(self):
        return self.combo_algo.currentText()
