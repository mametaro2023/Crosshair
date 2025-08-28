
from PyQt5 import QtCore, QtGui, QtWidgets

class Canvas(QtWidgets.QWidget):
    GRID_SIZE = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 360) # 40x40 grid with 9x9 pixels per cell
        self.grid_data = [[None for _ in range(self.GRID_SIZE)] for _ in range(self.GRID_SIZE)]
        self.pen_color = QtGui.QColor("#00FF66") # Default color
        self.is_eraser = False

        self.setMouseTracking(True) # Allow mouseMoveEvent without button press

    def set_tool(self, tool):
        self.is_eraser = (tool == 'eraser')

    def set_pen_color(self, color):
        self.pen_color = color
        self.is_eraser = False # Color selection implies using the pen

    def get_pixel_data(self):
        """Returns a list of non-transparent pixels for saving."""
        pixels = []
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                if self.grid_data[y][x]:
                    pixels.append({
                        "pos": [x, y],
                        "color": self.grid_data[y][x].name()
                    })
        return pixels

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtCore.Qt.white)

        cell_size = self.width() / self.GRID_SIZE

        # Draw center marker
        center_marker_color = QtGui.QColor(220, 220, 240) # Light blue/gray
        center_start = self.GRID_SIZE // 2 - 1
        painter.fillRect(QtCore.QRectF(center_start * cell_size, center_start * cell_size, 
                                      cell_size * 2, cell_size * 2), center_marker_color)

        # Draw grid lines
        pen = QtGui.QPen(QtGui.QColor(230, 230, 230), 1)
        painter.setPen(pen)
        for i in range(self.GRID_SIZE + 1):
            x = i * cell_size
            painter.drawLine(QtCore.QPointF(x, 0), QtCore.QPointF(x, self.height()))
            painter.drawLine(QtCore.QPointF(0, x), QtCore.QPointF(self.width(), x))

        # Draw pixels
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                if self.grid_data[y][x]:
                    painter.fillRect(QtCore.QRectF(x * cell_size, y * cell_size, cell_size, cell_size), self.grid_data[y][x])

    def _paint_pixel(self, pos):
        cell_size = self.width() / self.GRID_SIZE
        grid_x = int(pos.x() // cell_size)
        grid_y = int(pos.y() // cell_size)

        if 0 <= grid_x < self.GRID_SIZE and 0 <= grid_y < self.GRID_SIZE:
            if self.is_eraser:
                self.grid_data[grid_y][grid_x] = None
            else:
                self.grid_data[grid_y][grid_x] = self.pen_color
            self.update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._paint_pixel(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            self._paint_pixel(event.pos())
