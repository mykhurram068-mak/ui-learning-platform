"""
CRM Desktop — Stage 04
A native PySide6 desktop application with SQLite persistence.
"""
import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QComboBox, QTextEdit, QMessageBox,
    QHeaderView, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPalette

from database import (
    init_db, get_all_customers, get_customer,
    insert_customer, update_customer, delete_customer, get_counts
)


# ─────────────────────────────────────────────
# Theme
# ─────────────────────────────────────────────
DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #0f172a;
    color: #e2e8f0;
}
QLabel {
    color: #e2e8f0;
    font-size: 13px;
}
QLabel#pageTitle {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}
QLabel#kpiLabel {
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QLabel#kpiValue {
    font-size: 28px;
    font-weight: 800;
    color: #ffffff;
}
QFrame#kpiCard {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 16px;
}
QLineEdit, QComboBox, QTextEdit {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 10px;
    color: #e2e8f0;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #61dafb;
}
QPushButton {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 16px;
    color: #e2e8f0;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #334155;
}
QPushButton#primaryBtn {
    background-color: #61dafb;
    color: #0f172a;
    border: none;
}
QPushButton#primaryBtn:hover {
    background-color: #0891b2;
    color: #ffffff;
}
QPushButton#dangerBtn {
    color: #ef4444;
    border: 1px solid #ef4444;
}
QPushButton#dangerBtn:hover {
    background-color: #ef4444;
    color: #ffffff;
}
QTableWidget {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    gridline-color: #334155;
    color: #e2e8f0;
    font-size: 13px;
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #334155;
}
QTableWidget::item:selected {
    background-color: #334155;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #0f172a;
    color: #64748b;
    border: none;
    border-bottom: 1px solid #334155;
    padding: 10px 8px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
}
"""


# ─────────────────────────────────────────────
# Add/Edit Dialog
# ─────────────────────────────────────────────
class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("Edit Customer" if customer else "Add Customer")
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setStyleSheet(DARK_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Required")
        form.addRow("Name *", self.name_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Required")
        form.addRow("Email *", self.email_input)

        self.company_input = QLineEdit()
        form.addRow("Company", self.company_input)

        self.phone_input = QLineEdit()
        form.addRow("Phone", self.phone_input)

        self.status_input = QComboBox()
        self.status_input.addItems(["lead", "active", "inactive"])
        form.addRow("Status", self.status_input)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        form.addRow("Notes", self.notes_input)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setObjectName("primaryBtn")
        save.clicked.connect(self.handle_save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

        if customer:
            self.name_input.setText(customer["name"])
            self.email_input.setText(customer["email"])
            self.company_input.setText(customer["company"] or "")
            self.phone_input.setText(customer["phone"] or "")
            self.status_input.setCurrentText(customer["status"])
            self.notes_input.setPlainText(customer["notes"] or "")

    def handle_save(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required.")
            return
        if not email:
            QMessageBox.warning(self, "Validation", "Email is required.")
            return
        self.data = {
            "name": name,
            "email": email,
            "company": self.company_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "status": self.status_input.currentText(),
            "notes": self.notes_input.toPlainText().strip(),
        }
        self.accept()


# ─────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MAK CRM — Desktop")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(DARK_STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header row
        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customers...")
        self.search_input.setMaximumWidth(280)
        self.search_input.textChanged.connect(self.refresh_table)
        header.addWidget(self.search_input)

        add_btn = QPushButton("+  Add Customer")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self.add_customer)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # KPI cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_total = self._make_kpi("Total customers")
        self.kpi_leads = self._make_kpi("Active leads")
        self.kpi_active = self._make_kpi("Active customers")
        self.kpi_inactive = self._make_kpi("Inactive")

        for card in (self.kpi_total, self.kpi_leads, self.kpi_active, self.kpi_inactive):
            kpi_row.addWidget(card)
        layout.addLayout(kpi_row)

        # Filter chips
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.filter_buttons = []
        for label, value in [("All", "all"), ("Active", "active"), ("Leads", "lead"), ("Inactive", "inactive")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(value == "all")
            btn.setProperty("filter_value", value)
            btn.clicked.connect(self._on_filter_click)
            self.filter_buttons.append(btn)
            filter_row.addWidget(btn)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Name", "Company", "Email", "Status", "Added", "Actions"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 140)

        layout.addWidget(self.table, 1)

        # State
        self.current_filter = "all"
        self.refresh_table()

    def _make_kpi(self, label_text):
        card = QFrame()
        card.setObjectName("kpiCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumHeight(90)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(16, 12, 16, 12)
        vbox.setSpacing(4)

        label = QLabel(label_text)
        label.setObjectName("kpiLabel")
        value = QLabel("0")
        value.setObjectName("kpiValue")

        vbox.addWidget(label)
        vbox.addWidget(value)
        card.value_label = value
        return card

    def _on_filter_click(self):
        sender = self.sender()
        for btn in self.filter_buttons:
            btn.setChecked(btn is sender)
        self.current_filter = sender.property("filter_value")
        self.refresh_table()

    def refresh_table(self):
        # Fetch customers
        customers = get_all_customers()

        # Apply filter + search
        query = self.search_input.text().strip().lower()
        filtered = []
        for c in customers:
            if self.current_filter != "all" and c["status"] != self.current_filter:
                continue
            if query:
                haystack = f"{c['name']} {c['email']} {c['company'] or ''}".lower()
                if query not in haystack:
                    continue
            filtered.append(c)

        # Update table
        self.table.setRowCount(0)
        for row_idx, c in enumerate(filtered):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(c["name"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(c["company"] or "—"))
            self.table.setItem(row_idx, 2, QTableWidgetItem(c["email"]))

            status_item = QTableWidgetItem(c["status"].capitalize())
            status_colors = {
                "active": QColor("#10b981"),
                "lead": QColor("#f59e0b"),
                "inactive": QColor("#64748b"),
            }
            status_item.setForeground(status_colors.get(c["status"], QColor("#94a3b8")))
            self.table.setItem(row_idx, 3, status_item)

            self.table.setItem(row_idx, 4, QTableWidgetItem(self._format_date(c["createdAt"])))

            # Actions cell
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setFixedHeight(26)
            edit_btn.clicked.connect(lambda checked=False, cid=c["id"]: self.edit_customer(cid))
            actions_layout.addWidget(edit_btn)

            del_btn = QPushButton("Delete")
            del_btn.setObjectName("dangerBtn")
            del_btn.setFixedHeight(26)
            del_btn.clicked.connect(lambda checked=False, cid=c["id"]: self.delete_customer(cid))
            actions_layout.addWidget(del_btn)

            actions_layout.addStretch()
            self.table.setCellWidget(row_idx, 5, actions)
            self.table.setRowHeight(row_idx, 44)

        # Update KPIs
        counts = get_counts()
        self.kpi_total.value_label.setText(str(counts["total"]))
        self.kpi_leads.value_label.setText(str(counts["lead"]))
        self.kpi_active.value_label.setText(str(counts["active"]))
        self.kpi_inactive.value_label.setText(str(counts["inactive"]))

    def _format_date(self, iso):
        if not iso:
            return "—"
        try:
            dt = datetime.fromisoformat(iso.replace("Z", ""))
            delta = datetime.utcnow() - dt
            days = delta.days
            if days == 0:
                return "Today"
            if days == 1:
                return "Yesterday"
            if days < 7:
                return f"{days} days ago"
            if days < 30:
                return f"{days // 7} weeks ago"
            return dt.strftime("%b %d")
        except Exception:
            return "—"

    def add_customer(self):
        dialog = CustomerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            insert_customer(dialog.data)
            self.refresh_table()

    def edit_customer(self, customer_id):
        customer = get_customer(customer_id)
        if not customer:
            return
        dialog = CustomerDialog(self, customer)
        if dialog.exec() == QDialog.Accepted:
            update_customer(customer_id, dialog.data)
            self.refresh_table()

    def delete_customer(self, customer_id):
        customer = get_customer(customer_id)
        if not customer:
            return
        reply = QMessageBox.question(
            self, "Delete Customer",
            f'Delete "{customer["name"]}"? This cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_customer(customer_id)
            self.refresh_table()


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("MAK CRM")
    app.setOrganizationName("MAK UI Studio")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
