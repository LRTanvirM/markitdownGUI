"""MarkItDown GUI — native PySide6 desktop app (Nocturne theme).

Documents convert via MarkItDown; images via RapidOCR (see convert.py).
Run:  python app.py          (opens the window)
      python app.py --selftest   (headless engine check, for packaging)
"""
import os
import sys
import tempfile

from convert import convert_file, merge, IMAGE_EXTS

from PySide6.QtCore import (
    Qt, QObject, QRunnable, QThreadPool, Signal, QByteArray, QSize, QRect, QPoint,
    QPointF, QEvent, QTimer,
)
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QPainter, QPen, QFontMetrics
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QCheckBox, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTextBrowser, QPlainTextEdit, QFileDialog, QFrame, QLayout,
    QStyledItemDelegate, QStyle, QAbstractButton,
)

__version__ = "1.0"
ACCEPT_HINT = "Drag & drop files here"
STATUS_ROLE = Qt.UserRole + 1   # "Converting" | "Done" | "Error"
IMG_ROLE = Qt.UserRole + 2      # bool: is this an image (OCR) file

# Lucide-style icon paths (inner SVG), rendered to QIcons via QtSvg.
_ICONS = {
    "up": '<path d="M12 15V3"/><path d="M7 8l5-5 5 5"/><path d="M5 21h14"/>',
    "copy": '<rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/>',
    "folder": '<path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
    "merge": '<path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    "file": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v5h5"/><path d="M9 13h6M9 17h6"/>',
    "image": '<rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="1.6"/><path d="m21 15-4.5-4.5L6 21"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
}


def resource_path(name):
    """Path to a bundled file — works both from source and inside the PyInstaller exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def make_icon(name, color="#ecedf2", size=36, width=1.9):
    """Render one of _ICONS to a QIcon (needs a running QApplication)."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
           f'stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
           f'stroke-linejoin="round">{_ICONS[name]}</svg>')
    r = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    r.render(p)
    p.end()
    return QIcon(pm)


def _check_png():
    """White check drawn to a temp PNG, referenced by the checkbox QSS."""
    pm = make_icon("check", "#ffffff", 14, width=3).pixmap(14, 14)
    path = os.path.join(tempfile.gettempdir(), "markitdown_check.png")
    pm.save(path, "PNG")
    return path.replace("\\", "/")


# Nocturne. bg #0c0d11 · tile #15161c · line #23252d · text #ecedf2 · muted #868b97 · accent(red) #f5352a
STYLE = """
* { font-family: "Segoe UI", sans-serif; font-size: 10pt; color: #ecedf2; }
QMainWindow, QWidget { background: #0c0d11; }

QFrame#tile { background: #15161c; border: 1px solid #23252d; border-radius: 14px; }
QFrame#strip { background: #1b1d24; border: 1px solid #262932; border-radius: 14px; }

QLabel#brandName { font-size: 15pt; font-weight: 700; color: #f4f5f8; }
QLabel#brandSub { color: #868b97; }
QLabel#tileTitle { color: #868b97; font-weight: 600; }
QLabel#source { color: #868b97; }
QLabel#stripLead { color: #b7bcc7; font-weight: 600; }
QLabel#chip { background: #33384a; color: #cbd0de; border: 1px solid #454b60;
    border-radius: 10px; padding: 3px 10px; }
QFrame#drop { border: 1.5px dashed #33353d; border-radius: 12px; background: #101116; }
QFrame#drop:hover { border-color: #f5352a; background: #14161c; }
QLabel#dropTitle { color: #c7cad3; font-weight: 500; }
QLabel#mergedLbl, QLabel#count { color: #868b97; }

QListWidget { background: transparent; border: none; outline: 0; }
QListWidget::item { color: #c7cad3; }   /* row background is painted by RowDelegate */

QListWidget::indicator, QCheckBox::indicator { width: 17px; height: 17px; border-radius: 5px;
    border: 1.5px solid #3a3c45; background: #131319; }
QListWidget::indicator:hover, QCheckBox::indicator:hover { border-color: #565c6b; }
QListWidget::indicator:checked, QCheckBox::indicator:checked {
    background: #f5352a; border-color: #f5352a; image: url(__CHECK__); }

QPushButton { background: #191b21; border: 1px solid #282a32; border-radius: 10px;
    padding: 8px 14px; color: #ecedf2; }
QPushButton:hover { background: #21232b; border-color: #33353d; }
QPushButton:pressed { background: #141519; }
QPushButton:disabled { background: #141519; border-color: #20222a; color: #5a5d67; }
QPushButton:focus { outline: none; }
QPushButton#primary { background: #f5352a; border: 1px solid #f5352a; color: #ffffff; font-weight: 600; }
QPushButton#primary:hover { background: #ff4a3e; border-color: #ff4a3e; }
QPushButton#primary:pressed { background: #db2b21; }
QPushButton#primary:disabled { background: #43201d; border-color: #43201d; color: #9a6b66; }
QPushButton#link { background: transparent; border: none; color: #ff6a5f; padding: 2px 4px; }
QPushButton#link:hover { color: #ff8579; }

QCheckBox { color: #c7cad3; spacing: 8px; }

QTabWidget::pane { border: 1px solid #23252d; border-radius: 12px; background: #101116; top: -1px; }
QTabBar::tab { padding: 7px 16px; margin-right: 4px; color: #868b97; background: transparent;
    border: 1px solid transparent; border-bottom: none;
    border-top-left-radius: 9px; border-top-right-radius: 9px; }
QTabBar::tab:hover { color: #c7cad3; }
QTabBar::tab:selected { background: #101116; color: #f4f5f8; border: 1px solid #23252d; border-bottom: none; }

QTextBrowser, QPlainTextEdit { border: 1px solid #23252d; background: #101116;
    border-radius: 12px; padding: 14px; color: #c7cad3; selection-background-color: #f5352a; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 4px 2px 4px 0; }
QScrollBar::handle:vertical { background: #2c2f38; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #3a3e49; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 0 4px 2px 4px; }
QScrollBar::handle:horizontal { background: #2c2f38; border-radius: 5px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #3a3e49; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
"""

# Qt renders the Markdown preview as its own rich-text document — it ignores widget
# QSS for the content, so it needs this document stylesheet to go dark.
PREVIEW_CSS = """
body { color: #c9cdd6; font-family: 'Segoe UI', sans-serif; font-size: 10.5pt; }
h1 { color: #f4f5f8; font-size: 19pt; font-weight: 700; margin-bottom: 10px; }
h2 { color: #f4f5f8; font-size: 15pt; font-weight: 700; margin-top: 18px; margin-bottom: 8px; }
h3 { color: #ecedf2; font-size: 12.5pt; font-weight: 600; margin-top: 14px; margin-bottom: 6px; }
h4, h5, h6 { color: #ecedf2; font-weight: 600; }
p { margin-bottom: 10px; }
a { color: #ff7d70; text-decoration: none; }
code { font-family: 'Consolas', monospace; font-size: 10pt; background-color: #23252d; color: #ffb59a; }
pre { background-color: #17181f; color: #c7cad3; font-family: 'Consolas', monospace; font-size: 10pt; }
th { background-color: #17181f; color: #f4f5f8; }
th, td { border: 1px solid #2a2c35; padding: 6px; }
blockquote { color: #868b97; }
"""


class WorkerSignals(QObject):
    done = Signal(int, str, str)  # file_id, markdown, error


class ConvertTask(QRunnable):
    def __init__(self, fid, path, signals):
        super().__init__()
        self.fid, self.path, self.signals = fid, path, signals

    def run(self):
        r = convert_file(self.path)
        self.signals.done.emit(self.fid, r["markdown"], r["error"] or "")


class ClickFrame(QFrame):
    """A QFrame that acts like a button — click anywhere in it to fire on_click."""
    def __init__(self, on_click, parent=None):
        super().__init__(parent)
        self._on_click = on_click
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._on_click()
        super().mousePressEvent(e)


class ToggleSwitch(QAbstractButton):
    """Small pill toggle (drop-in for a checkbox: isChecked/setChecked/toggled)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(38, 22)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        on = self.isChecked()
        p.setBrush(QColor("#f5352a") if on else QColor("#2a2c34"))
        p.drawRoundedRect(self.rect(), 11, 11)
        d = 18
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(self.width() - d - 2 if on else 2, 2, d, d)


class FlowLayout(QLayout):
    """Left-to-right layout that wraps to new rows — used for the format chips."""
    def __init__(self, parent=None, spacing=7):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(spacing)
        self._items = []

    def addItem(self, item): self._items.append(item)
    def count(self): return len(self._items)
    def itemAt(self, i): return self._items[i] if 0 <= i < len(self._items) else None
    def takeAt(self, i): return self._items.pop(i) if 0 <= i < len(self._items) else None
    def expandingDirections(self): return Qt.Orientation(0)
    def hasHeightForWidth(self): return True
    def heightForWidth(self, w): return self._lay(QRect(0, 0, w, 0), True)
    def setGeometry(self, rect): super().setGeometry(rect); self._lay(rect, False)
    def sizeHint(self): return self.minimumSize()

    def minimumSize(self):
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        return s

    def _lay(self, rect, test):
        x, y, line_h = rect.x(), rect.y(), 0
        for it in self._items:
            w, h = it.sizeHint().width(), it.sizeHint().height()
            if x + w > rect.right() and line_h > 0:
                x = rect.x(); y += line_h + self.spacing(); line_h = 0
            if not test:
                it.setGeometry(QRect(QPoint(x, y), it.sizeHint()))
            x += w + self.spacing()
            line_h = max(line_h, h)
        return y + line_h - rect.y()


class RowDelegate(QStyledItemDelegate):
    """Single-line queue row: checkbox · icon · name · right-aligned status pill."""
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

    def sizeHint(self, opt, idx):
        return QSize(0, 46)

    @staticmethod
    def _pill(status, is_img):
        if status == "Converting":
            return "Converting", QColor("#ff9d8a"), QColor("#2a1c1c")
        if status == "Error":
            return "Error", QColor("#ff9d8a"), QColor("#2a1c1c")
        if is_img:
            return "OCR", QColor("#3fd39b"), QColor("#12241c")
        return "Done", QColor("#43d19b"), QColor("#12241c")

    @staticmethod
    def _check_box_rect(opt):
        r = opt.rect.adjusted(2, 3, -2, -3)
        return QRect(r.left() + 11, r.center().y() - 8, 17, 17)

    def paint(self, p, opt, idx):
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        r = opt.rect.adjusted(2, 3, -2, -3)
        sel = bool(opt.state & QStyle.State_Selected)
        if sel:
            p.setBrush(QColor("#2a1c1c")); p.setPen(Qt.NoPen); p.drawRoundedRect(r, 9, 9)
        elif opt.state & QStyle.State_MouseOver:
            p.setBrush(QColor("#1b1d24")); p.setPen(Qt.NoPen); p.drawRoundedRect(r, 9, 9)
        cy = r.center().y()

        # checkbox (data() may return int or enum depending on PySide build)
        box = self._check_box_rect(opt)
        cs = idx.data(Qt.CheckStateRole)
        if cs == Qt.Checked or cs == 2:
            p.setBrush(QColor("#f5352a")); p.setPen(Qt.NoPen); p.drawRoundedRect(box, 5, 5)
            pen = QPen(QColor("#ffffff"), 2); pen.setCapStyle(Qt.RoundCap); pen.setJoinStyle(Qt.RoundJoin)
            p.setPen(pen)
            p.drawPolyline([QPointF(box.left() + 4, cy + 0.5), QPointF(box.left() + 7, cy + 4),
                            QPointF(box.left() + 13, cy - 3)])
        else:
            p.setBrush(QColor("#131319")); pen = QPen(QColor("#3a3c45")); pen.setWidthF(1.5)
            p.setPen(pen); p.drawRoundedRect(box, 5, 5)
        x = box.right() + 11

        # file / image icon
        icon = idx.data(Qt.DecorationRole)
        if isinstance(icon, QIcon):
            p.drawPixmap(x, cy - 9, icon.pixmap(18, 18)); x += 27

        # status pill (right-aligned)
        status = idx.data(STATUS_ROLE) or "Done"
        label, fg, bgc = self._pill(status, bool(idx.data(IMG_ROLE)))
        f = QFont(opt.font); f.setPointSizeF(8.0); f.setBold(True)
        glyph = 15 if status in ("Converting", "Done") else 0
        pw = QFontMetrics(f).horizontalAdvance(label) + 18 + glyph
        pill = QRect(r.right() - pw - 8, cy - 11, pw, 22)
        p.setBrush(bgc); p.setPen(Qt.NoPen); p.drawRoundedRect(pill, 11, 11)
        tx = pill.left() + 10
        if status == "Converting":
            p.save(); p.translate(pill.left() + 13, cy + 0.5); p.rotate(self.owner._spin_angle)
            pen = QPen(fg, 1.8); pen.setCapStyle(Qt.RoundCap); p.setPen(pen); p.setBrush(Qt.NoBrush)
            p.drawArc(QRect(-5, -5, 10, 10), 0, 270 * 16); p.restore()
            tx = pill.left() + 22
        elif status == "Done":
            pen = QPen(fg, 1.8); pen.setCapStyle(Qt.RoundCap); pen.setJoinStyle(Qt.RoundJoin); p.setPen(pen)
            p.drawPolyline([QPointF(pill.left() + 7, cy + 0.5), QPointF(pill.left() + 10, cy + 3.5),
                            QPointF(pill.left() + 15, cy - 3)])
            tx = pill.left() + 22
        p.setFont(f); p.setPen(fg)
        p.drawText(QRect(tx, r.top(), pill.right() - tx - 8, r.height()), Qt.AlignVCenter | Qt.AlignLeft, label)

        # name (fills the gap between icon and pill)
        name = idx.data(Qt.DisplayRole) or ""
        p.setFont(opt.font); p.setPen(QColor("#ffffff") if sel else QColor("#c7cad3"))
        avail = max(0, pill.left() - x - 10)
        nm = QFontMetrics(opt.font).elidedText(name, Qt.ElideRight, avail)
        p.drawText(QRect(x, r.top(), avail, r.height()), Qt.AlignVCenter | Qt.AlignLeft, nm)
        p.restore()

    def editorEvent(self, event, model, opt, idx):
        # toggle the check when its box is clicked; let the view handle the rest
        if event.type() == QEvent.MouseButtonRelease and (idx.flags() & Qt.ItemIsUserCheckable):
            if self._check_box_rect(opt).contains(event.position().toPoint()):
                cur = idx.data(Qt.CheckStateRole)
                new = Qt.Unchecked if (cur == Qt.Checked or cur == 2) else Qt.Checked
                model.setData(idx, new, Qt.CheckStateRole)
                return True
        return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"MarkItDown {__version__} — File to Markdown")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.resize(1180, 780)
        self.setMinimumSize(880, 600)
        self.setAcceptDrops(True)

        self.files = {}          # fid -> {path, name, status, markdown, error}
        self.items = {}          # fid -> QListWidgetItem
        self._next = 0
        self.current_id = None

        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(1)   # sequential — avoids MarkItDown thread-safety issues
        self.signals = WorkerSignals()
        self.signals.done.connect(self.on_converted)

        self._spin_angle = 0
        self._spin_timer = QTimer(self)
        self._spin_timer.setInterval(83)
        self._spin_timer.timeout.connect(self._tick_spin)

        self._build_ui()

    # ---- UI ----
    def _build_ui(self):
        root = QWidget()
        # Plain QWidgets don't auto-paint a QSS "background" unless WA_StyledBackground is
        # set (Qt only does this implicitly for widgets with a custom paintEvent), so a bare
        # container can show through to whatever's behind it — belt-and-suspenders it here.
        root.setAttribute(Qt.WA_StyledBackground, True)
        root.setAutoFillBackground(True)
        root.setStyleSheet("background-color: #0c0d11;")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(14)

        # ================= TOP ROW (brand + formats strip — same height, same row) =====
        toprow = QHBoxLayout(); toprow.setSpacing(14)

        # brand tile
        brand = QFrame(); brand.setObjectName("tile")
        brand.setMinimumWidth(300); brand.setMaximumWidth(340)
        bl = QHBoxLayout(brand); bl.setContentsMargins(14, 12, 14, 12); bl.setSpacing(11)
        logo = QLabel(); logo.setPixmap(QIcon(resource_path("icon.ico")).pixmap(40, 40))
        bt = QVBoxLayout(); bt.setSpacing(0)
        nm = QLabel("MarkItDown"); nm.setObjectName("brandName")
        sb = QLabel(f"v{__version__} · Markdown converter"); sb.setObjectName("brandSub")
        bt.addWidget(nm); bt.addWidget(sb)
        bl.addWidget(logo, 0, Qt.AlignVCenter)
        bl.addLayout(bt); bl.setAlignment(bt, Qt.AlignVCenter)
        bl.addStretch(1)
        toprow.addWidget(brand)

        # supported-formats strip (grey) — chip pills, wrap on narrow widths
        strip = QFrame(); strip.setObjectName("strip")
        sl = QHBoxLayout(strip); sl.setContentsMargins(16, 12, 16, 12); sl.setSpacing(12)
        lead = QLabel("Supported file formats"); lead.setObjectName("stripLead")
        chips = QWidget(); chips.setAutoFillBackground(False)
        fl = FlowLayout(chips, spacing=7)
        for fmt in ("PDF", "Word", "PowerPoint", "Excel", "HTML", "CSV", "JSON", "XML",
                    "EPUB", "ZIP", "Images (OCR)"):
            chip = QLabel(fmt); chip.setObjectName("chip")
            fl.addWidget(chip)
        sl.addWidget(lead, 0, Qt.AlignVCenter); sl.addWidget(chips, 1)
        toprow.addWidget(strip, 1)

        outer.addLayout(toprow)

        # ================= MAIN ROW =================
        mainrow = QHBoxLayout(); mainrow.setSpacing(14)

        # ---- LEFT column: drop / queue / actions ----
        left = QWidget()
        left.setAttribute(Qt.WA_StyledBackground, True)
        left.setMinimumWidth(300)
        left.setMaximumWidth(340)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(14)

        # drop tile — dashed zone with an inline "browse" link
        droptile = QFrame(); droptile.setObjectName("tile")
        dl = QVBoxLayout(droptile); dl.setContentsMargins(14, 14, 14, 14); dl.setSpacing(0)
        self.drop = ClickFrame(self.browse); self.drop.setObjectName("drop")
        dz = QVBoxLayout(self.drop); dz.setContentsMargins(12, 20, 12, 20); dz.setSpacing(4)
        up = QLabel(); up.setPixmap(make_icon("up", "#f5352a", 26).pixmap(26, 26)); up.setAlignment(Qt.AlignCenter)
        up.setAttribute(Qt.WA_TransparentForMouseEvents)
        title = QLabel(ACCEPT_HINT); title.setObjectName("dropTitle"); title.setAlignment(Qt.AlignCenter)
        title.setAttribute(Qt.WA_TransparentForMouseEvents)
        browse = QPushButton("or browse files"); browse.setObjectName("link")
        browse.setCursor(Qt.PointingHandCursor); browse.clicked.connect(self.browse)
        dz.addWidget(up); dz.addWidget(title); dz.addWidget(browse, 0, Qt.AlignCenter)
        dl.addWidget(self.drop)
        lv.addWidget(droptile)

        # queue tile
        qtile = QFrame(); qtile.setObjectName("tile")
        ql = QVBoxLayout(qtile); ql.setContentsMargins(14, 12, 14, 12); ql.setSpacing(8)
        qhdr = QHBoxLayout()
        qtitle = QLabel("Queue"); qtitle.setObjectName("tileTitle")
        clear_btn = QPushButton("Clear"); clear_btn.setObjectName("link")
        clear_btn.setCursor(Qt.PointingHandCursor); clear_btn.clicked.connect(self.clear_all)
        qhdr.addWidget(qtitle); qhdr.addStretch(1); qhdr.addWidget(clear_btn)
        ql.addLayout(qhdr)
        self.list = QListWidget()
        self.list.setItemDelegate(RowDelegate(self))
        self.list.setMouseTracking(True)
        self.list.setUniformItemSizes(True)
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.currentItemChanged.connect(self._on_current_changed)
        ql.addWidget(self.list, 1)
        self.select_all = QCheckBox("Select all")
        self.select_all.stateChanged.connect(self._on_select_all)
        ql.addWidget(self.select_all)
        lv.addWidget(qtile, 1)

        # actions tile
        atile = QFrame(); atile.setObjectName("tile")
        av = QVBoxLayout(atile); av.setContentsMargins(14, 10, 14, 12); av.setSpacing(9)
        self.sel_count = QLabel(""); self.sel_count.setObjectName("count")
        av.addWidget(self.sel_count)
        arow = QHBoxLayout(); arow.setSpacing(10)
        self.save_each_btn = QPushButton("  Save each")
        self.save_each_btn.setIcon(make_icon("folder")); self.save_each_btn.clicked.connect(self.save_each)
        self.merge_btn = QPushButton("  Merge && save"); self.merge_btn.setObjectName("primary")
        self.merge_btn.setIcon(make_icon("merge", "#ffffff")); self.merge_btn.clicked.connect(self.merge_and_save)
        arow.addWidget(self.save_each_btn, 1); arow.addWidget(self.merge_btn, 1)
        av.addLayout(arow)
        lv.addWidget(atile)

        mainrow.addWidget(left)

        # ---- RIGHT column: preview ----
        right = QVBoxLayout(); right.setSpacing(14)

        # preview tile
        ptile = QFrame(); ptile.setObjectName("tile")
        pl = QVBoxLayout(ptile); pl.setContentsMargins(14, 12, 14, 14); pl.setSpacing(10)
        phdr = QHBoxLayout()
        self.source = QLabel("No file selected"); self.source.setObjectName("source")
        merged_lbl = QLabel("Merged view"); merged_lbl.setObjectName("mergedLbl")
        self.merged_view = ToggleSwitch(); self.merged_view.toggled.connect(self.refresh_preview)
        phdr.addWidget(self.source, 1); phdr.addWidget(merged_lbl); phdr.addSpacing(8); phdr.addWidget(self.merged_view)
        pl.addLayout(phdr)

        self.tabs = QTabWidget()
        self.preview = QTextBrowser(); self.preview.setOpenExternalLinks(True)
        self.preview.document().setDefaultStyleSheet(PREVIEW_CSS)
        self.raw = QPlainTextEdit(); self.raw.setReadOnly(True); self.raw.setFont(QFont("Consolas", 10))
        self.tabs.addTab(self.preview, "Preview")
        self.tabs.addTab(self.raw, "Markdown")
        pl.addWidget(self.tabs, 1)

        pfoot = QHBoxLayout(); pfoot.addStretch(1)
        self.copy_btn = QPushButton("  Copy"); self.copy_btn.setIcon(make_icon("copy")); self.copy_btn.clicked.connect(self.copy)
        self.dl_btn = QPushButton("  Download .md"); self.dl_btn.setObjectName("primary")
        self.dl_btn.setIcon(make_icon("download", "#ffffff")); self.dl_btn.clicked.connect(self.download_current)
        pfoot.addWidget(self.copy_btn); pfoot.addWidget(self.dl_btn)
        pl.addLayout(pfoot)

        right.addWidget(ptile, 1)
        mainrow.addLayout(right, 1)
        outer.addLayout(mainrow, 1)

        self._update_buttons()

    # ---- drag & drop ----
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        self.add_files([p for p in paths if os.path.isfile(p)])

    # ---- file handling ----
    def browse(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose files to convert")
        self.add_files(paths)

    def add_files(self, paths):
        for path in paths:
            fid = self._next
            self._next += 1
            self.files[fid] = {
                "path": path, "name": os.path.basename(path),
                "status": "Converting…", "markdown": "", "error": None,
            }
            item = QListWidgetItem()
            item.setData(Qt.UserRole, fid)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            is_img = os.path.splitext(path)[1].lower() in IMAGE_EXTS
            item.setData(IMG_ROLE, is_img)
            item.setIcon(make_icon("image" if is_img else "file", "#868b97", 32, 1.7))
            self._set_item_status(fid, item)
            self.list.addItem(item)
            self.items[fid] = item
            if self.current_id is None:
                self.current_id = fid
                self.list.setCurrentItem(item)
            self.pool.start(ConvertTask(fid, path, self.signals))
        self._update_buttons()
        self._update_spinner()
        self.refresh_preview()

    def on_converted(self, fid, markdown, error):
        rec = self.files.get(fid)
        if not rec:
            return
        rec["markdown"] = markdown
        rec["error"] = error or None
        rec["status"] = f"Error: {error}" if error else "Done"
        self._set_item_status(fid, self.items[fid])
        self._update_buttons()
        self._update_spinner()
        if fid == self.current_id or self.merged_view.isChecked():
            self.refresh_preview()

    def _set_item_status(self, fid, item):
        rec = self.files[fid]
        st = "Error" if rec["error"] else ("Done" if rec["status"] == "Done" else "Converting")
        self.list.blockSignals(True)   # setData fires itemChanged otherwise
        item.setText(rec["name"])
        item.setData(STATUS_ROLE, st)
        self.list.blockSignals(False)

    def _tick_spin(self):
        self._spin_angle = (self._spin_angle + 30) % 360
        self.list.viewport().update()

    def _update_spinner(self):
        busy = any(r["status"] == "Converting…" for r in self.files.values())
        if busy and not self._spin_timer.isActive():
            self._spin_timer.start()
        elif not busy and self._spin_timer.isActive():
            self._spin_timer.stop()

    def clear_all(self):
        self.list.clear()
        self.files.clear(); self.items.clear()
        self.current_id = None
        self.select_all.setCheckState(Qt.Unchecked)
        self._update_buttons()
        self._update_spinner()
        self.refresh_preview()

    # ---- selection / checkboxes ----
    def _on_item_changed(self, _item):
        self._update_buttons()
        if self.merged_view.isChecked():
            self.refresh_preview()

    def _on_current_changed(self, cur, _prev):
        if cur is not None:
            self.current_id = cur.data(Qt.UserRole)
            if self.merged_view.isChecked():
                self.merged_view.setChecked(False)  # triggers refresh
            else:
                self.refresh_preview()

    def _on_select_all(self, state):
        self.list.blockSignals(True)
        for item in self.items.values():
            item.setCheckState(Qt.CheckState(state))
        self.list.blockSignals(False)
        self._update_buttons()
        if self.merged_view.isChecked():
            self.refresh_preview()

    def _checked_done(self):
        out = []
        for fid, item in self.items.items():
            rec = self.files[fid]
            if item.checkState() == Qt.Checked and rec["error"] is None and rec["status"] == "Done":
                out.append((fid, rec))
        return out

    # ---- preview ----
    def refresh_preview(self):
        if self.merged_view.isChecked():
            done = self._checked_done()
            text = merge([(os.path.splitext(r["name"])[0], r["markdown"]) for _, r in done])
            self.source.setText(f"Merged · {len(done)} file(s)")
        else:
            rec = self.files.get(self.current_id)
            if rec and rec["error"] is None and rec["status"] == "Done":
                text = rec["markdown"]
            elif rec and rec["error"]:
                text = f"**Conversion failed**\n\n`{rec['error']}`"
            elif rec:
                text = "_Converting…_"
            else:
                text = ""
            self.source.setText(rec["name"] if rec else "No file selected")
        self.preview.setMarkdown(text)
        self.raw.setPlainText(text)

    # ---- actions ----
    def copy(self):
        QApplication.clipboard().setText(self.raw.toPlainText())

    def _current_save_text(self):
        if self.merged_view.isChecked():
            done = self._checked_done()
            return merge([(os.path.splitext(r["name"])[0], r["markdown"]) for _, r in done]), "merged.md"
        rec = self.files.get(self.current_id)
        if rec and rec["status"] == "Done":
            return rec["markdown"], os.path.splitext(rec["name"])[0] + ".md"
        return None, None

    def download_current(self):
        text, default = self._current_save_text()
        if text is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Markdown", default, "Markdown (*.md);;All files (*.*)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    def save_each(self):
        done = self._checked_done()
        if not done:
            return
        folder = QFileDialog.getExistingDirectory(self, "Choose a folder to save each .md")
        if not folder:
            return
        for _, rec in done:
            name = os.path.splitext(rec["name"])[0] + ".md"
            with open(os.path.join(folder, name), "w", encoding="utf-8") as f:
                f.write(rec["markdown"])

    def merge_and_save(self):
        done = self._checked_done()
        if not done:
            return
        text = merge([(os.path.splitext(r["name"])[0], r["markdown"]) for _, r in done])
        path, _ = QFileDialog.getSaveFileName(self, "Save merged Markdown", "merged.md", "Markdown (*.md);;All files (*.*)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    def _update_buttons(self):
        has_done = bool(self._checked_done())
        self.save_each_btn.setEnabled(has_done)
        self.merge_btn.setEnabled(has_done)
        rec = self.files.get(self.current_id)
        self.dl_btn.setEnabled(self.merged_view.isChecked() and has_done
                               or bool(rec and rec["status"] == "Done"))
        self.copy_btn.setEnabled(bool(self.raw.toPlainText()) if hasattr(self, "raw") else False)
        n = sum(1 for it in self.items.values() if it.checkState() == Qt.Checked)
        self.sel_count.setText(f'<span style="color:#3fd39b">●</span>  {n} selected' if n else "")
        self.sel_count.setVisible(n > 0)


def _apply_dark_palette(app):
    # Fusion + a dark palette so unstyled bits (menus, tooltips, text carets) match.
    app.setStyle("Fusion")
    c = {
        "bg": "#0c0d11", "surface": "#15161c", "alt": "#1c1e26",
        "text": "#ecedf2", "muted": "#868b97", "accent": "#f5352a",
    }
    p = QPalette()
    p.setColor(QPalette.Window, QColor(c["bg"]))
    p.setColor(QPalette.WindowText, QColor(c["text"]))
    p.setColor(QPalette.Base, QColor(c["surface"]))
    p.setColor(QPalette.AlternateBase, QColor(c["alt"]))
    p.setColor(QPalette.Text, QColor(c["text"]))
    p.setColor(QPalette.Button, QColor(c["surface"]))
    p.setColor(QPalette.ButtonText, QColor(c["text"]))
    p.setColor(QPalette.ToolTipBase, QColor(c["alt"]))
    p.setColor(QPalette.ToolTipText, QColor(c["text"]))
    p.setColor(QPalette.PlaceholderText, QColor(c["muted"]))
    p.setColor(QPalette.Highlight, QColor(c["accent"]))
    p.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor("#5a5d67"))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#5a5d67"))
    app.setPalette(p)


def main():
    # Windows: give the app its own taskbar identity so it shows OUR icon,
    # not the default Python one, and groups under it.
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MarkItDown.GUI.1")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("icon.ico")))
    _apply_dark_palette(app)
    app.setStyleSheet(STYLE.replace("__CHECK__", _check_png()))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        import convert
        convert.selftest()
    else:
        main()
