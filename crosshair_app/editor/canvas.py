import copy
from PyQt5 import QtCore, QtGui, QtWidgets
import math

class Canvas(QtWidgets.QWidget):
    GRID_SIZE = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 360) # 40x40 grid with 9x9 pixels per cell
        self.grid_data = [[None for _ in range(self.GRID_SIZE)] for _ in range(self.GRID_SIZE)]
        self.pen_color = QtGui.QColor("#00FF66") # Default color
        self.is_eraser = False
        self.current_tool = "pencil" # "pencil", "eraser", "line", "circle"
        self.start_pos = None # 直線・円ツールの開始位置
        self.current_mouse_pos = None # 直線・円ツールの現在のマウス位置 (プレビュー用)
        self.brush_size = 1 # ブラシサイズ (1ピクセル単位)
        self.hover_pos = None # ペン・消しゴムツールのホバー位置 (プレビュー用)

        self.undo_stack = []
        self.redo_stack = []
        self.MAX_HISTORY = 50 # 履歴の最大数

        self.setMouseTracking(True) # Allow mouseMoveEvent without button press

    def set_tool(self, tool):
        self.current_tool = tool
        self.is_eraser = (tool == 'eraser')

    def set_pen_color(self, color):
        self.pen_color = color
        self.is_eraser = False # Color selection implies using the pen
        self.current_tool = "pencil" # 色選択時はペンツールに切り替える

    def set_brush_size(self, size):
        self.brush_size = max(1, min(size, 10)) # サイズを1から10の範囲に制限

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

        # 直線・円ツールのプレビュー描画
        if self.start_pos and self.current_mouse_pos and \
           (self.current_tool == "line" or self.current_tool == "circle"):
            
            preview_color = QtGui.QColor(self.pen_color)
            preview_color.setAlpha(128) # 半透明
            painter.setPen(QtGui.QPen(preview_color, 1)) # 細いペン

            # 描画座標をピクセル単位に変換
            start_x_px = self.start_pos.x() * cell_size + cell_size / 2
            start_y_px = self.start_pos.y() * cell_size + cell_size / 2
            current_x_px = self.current_mouse_pos.x() * cell_size + cell_size / 2
            current_y_px = self.current_mouse_pos.y() * cell_size + cell_size / 2

            if self.current_tool == "line":
                painter.drawLine(QtCore.QPointF(start_x_px, start_y_px), QtCore.QPointF(current_x_px, current_y_px))
            elif self.current_tool == "circle":
                # 中心と半径から円を描画
                radius_px = math.sqrt((current_x_px - start_x_px)**2 + (current_y_px - start_y_px)**2)
                painter.drawEllipse(QtCore.QPointF(start_x_px, start_y_px), radius_px, radius_px)

        # ペン・消しゴムツールのブラシプレビュー
        if self.hover_pos and (self.current_tool == "pencil" or self.current_tool == "eraser"):
            preview_color = QtGui.QColor(self.pen_color)
            preview_color.setAlpha(80) # より薄い半透明
            
            if self.is_eraser:
                preview_color = QtGui.QColor(QtCore.Qt.white)
                preview_color.setAlpha(80)

            painter.setBrush(preview_color)
            
            # 黒い輪郭を追加
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 1)) # 黒いペン、太さ1
            
            # ブラシの左上ピクセル座標を計算
            # _set_pixel_with_brush と同じ計算を使用
            top_left_x = self.hover_pos.x() - (self.brush_size - 1) // 2
            top_left_y = self.hover_pos.y() - (self.brush_size - 1) // 2
            
            # 描画
            painter.drawRect(QtCore.QRectF(top_left_x * cell_size, top_left_y * cell_size,
                                          self.brush_size * cell_size, self.brush_size * cell_size))

    def _paint_pixel(self, pos):
        cell_size = self.width() / self.GRID_SIZE
        grid_x = int(pos.x() // cell_size)
        grid_y = int(pos.y() // cell_size)

        if 0 <= grid_x < self.GRID_SIZE and 0 <= grid_y < self.GRID_SIZE:
            old_color = self.grid_data[grid_y][grid_x]
            new_color = None if self.is_eraser else self.pen_color

            # ブラシサイズに応じてピクセルをセット
            self._set_pixel_with_brush(grid_x, grid_y, new_color)
            self.update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.push_state() # ストローク開始前の状態を保存
            
            cell_size = self.width() / self.GRID_SIZE
            grid_x = int(event.pos().x() // cell_size)
            grid_y = int(event.pos().y() // cell_size)
            self.start_pos = QtCore.QPoint(grid_x, grid_y)

            if self.current_tool == "pencil" or self.current_tool == "eraser":
                self._paint_pixel(event.pos())

    def mouseMoveEvent(self, event):
        cell_size = self.width() / self.GRID_SIZE
        grid_x = int(event.pos().x() // cell_size)
        grid_y = int(event.pos().y() // cell_size)

        # ホバー位置を常に更新し、プレビューを再描画
        if self.hover_pos != QtCore.QPoint(grid_x, grid_y):
            self.hover_pos = QtCore.QPoint(grid_x, grid_y)
            self.update()

        if event.buttons() & QtCore.Qt.LeftButton:
            if self.current_tool == "pencil" or self.current_tool == "eraser":
                self._paint_pixel(event.pos())
            elif self.current_tool == "line" or self.current_tool == "circle":
                # プレビュー用の現在のマウス位置を更新
                self.current_mouse_pos = QtCore.QPoint(grid_x, grid_y)
                self.update() # プレビューを再描画

    def mouseLeaveEvent(self, event):
        self.hover_pos = None
        self.update() # プレビューを非表示

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            cell_size = self.width() / self.GRID_SIZE
            end_x = int(event.pos().x() // cell_size)
            end_y = int(event.pos().y() // cell_size)
            end_pos = QtCore.QPoint(end_x, end_y)

            if self.current_tool == "line":
                self._draw_line(self.start_pos, end_pos, self.pen_color)
            elif self.current_tool == "circle":
                self._draw_circle(self.start_pos, end_pos, self.pen_color)
            
            self.start_pos = None # 描画終了
            self.current_mouse_pos = None # プレビューをクリア
            self.update() # 最終描画を反映

    def _draw_line(self, p1, p2, color):
        """Bresenham's line algorithm"""
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            self._set_pixel_with_brush(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def _draw_circle(self, center, end_point, color):
        """Midpoint circle algorithm"""
        xc, yc = center.x(), center.y()
        radius = int(math.sqrt((end_point.x() - xc)**2 + (end_point.y() - yc)**2))

        x = radius
        y = 0
        err = 0

        while x >= y:
            self._draw_circle_pixels(xc, yc, x, y, color)
            y += 1
            err += 1 + 2*y
            if 2*(err-x) + 1 > 0:
                x -= 1
                err += 1 - 2*x

    def _draw_circle_pixels(self, xc, yc, x, y, color):
        self._set_pixel_with_brush(xc + x, yc + y, color)
        self._set_pixel_with_brush(xc - x, yc + y, color)
        self._set_pixel_with_brush(xc + x, yc - y, color)
        self._set_pixel_with_brush(xc - x, yc - y, color)
        self._set_pixel_with_brush(xc + y, yc + x, color)
        self._set_pixel_with_brush(xc - y, yc + x, color)
        self._set_pixel_with_brush(xc + y, yc - x, color)
        self._set_pixel_with_brush(xc - y, yc - x, color)

    def _set_pixel_with_brush(self, x, y, color):
        """指定された座標を中心にブラシサイズでピクセルをセットする"""
        # ブラシの開始座標を計算
        start_px = x - (self.brush_size - 1) // 2
        start_py = y - (self.brush_size - 1) // 2

        for py in range(start_py, start_py + self.brush_size):
            for px in range(start_px, start_px + self.brush_size):
                if 0 <= px < self.GRID_SIZE and 0 <= py < self.GRID_SIZE:
                    self.grid_data[py][px] = color

    def push_state(self):
        """現在のキャンバスの状態をundoスタックに保存する"""
        if len(self.undo_stack) >= self.MAX_HISTORY:
            self.undo_stack.pop(0) # 古い履歴を削除
        self.undo_stack.append(copy.deepcopy(self.grid_data))
        self.redo_stack.clear() # 新しい操作が行われたらredoスタックはクリア

    def apply_state(self, state):
        """指定された状態をキャンバスに適用する"""
        self.grid_data = copy.deepcopy(state)
        self.update()

    def undo(self):
        """一つ前の状態に戻す"""
        if self.undo_stack:
            self.redo_stack.append(copy.deepcopy(self.grid_data))
            self.apply_state(self.undo_stack.pop())

    def redo(self):
        """やり直し操作を実行する"""
        if self.redo_stack:
            self.undo_stack.append(copy.deepcopy(self.grid_data))
            self.apply_state(self.redo_stack.pop())