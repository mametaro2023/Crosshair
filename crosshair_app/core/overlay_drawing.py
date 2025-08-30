import os
import json
from PyQt5 import QtCore, QtGui, QtWidgets

class OverlayDrawingMixin:
    def render_crshr(self, painter, path):
        """カスタムの.crshrファイルを描画する"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            pixels = data.get("pixels", [])
            original_size = data.get("size", [40, 40]) # Get original size from .crshr file

            # Create a QImage from pixel data
            image = QtGui.QImage(original_size[0], original_size[1], QtGui.QImage.Format_ARGB32)
            image.fill(QtCore.Qt.transparent) # Fill with transparent background

            for pixel in pixels:
                pos = pixel.get("pos")
                color_str = pixel.get("color")
                if pos and color_str:
                    color = QtGui.QColor(color_str)
                    # Ensure pixel is within bounds
                    if 0 <= pos[0] < original_size[0] and 0 <= pos[1] < original_size[1]:
                        image.setPixelColor(pos[0], pos[1], color)
            
            pixmap = QtGui.QPixmap.fromImage(image)
            
            if not pixmap.isNull():
                # Scale the pixmap to the desired size
                scaled_pixmap = pixmap.scaled(self.image_crosshair_size, self.image_crosshair_size, 
                                              QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                
                # Calculate target rectangle to center the scaled pixmap
                target_rect = QtCore.QRect(self.center_x - scaled_pixmap.width() // 2, 
                                           self.center_y - scaled_pixmap.height() // 2, 
                                           scaled_pixmap.width(), scaled_pixmap.height())
                
                painter.setOpacity(self.crosshair_alpha) # Apply overall crosshair alpha
                painter.drawPixmap(target_rect, scaled_pixmap)

        except Exception as e:
            print(f"カスタムクロスヘアの描画に失敗: {path}, {e}")

    def _draw_crosshair(self, painter):
        ch_alpha = self.crosshair_alpha
        if self.fade_on_shoot_enabled and self.is_shooting:
            ch_alpha *= 0.3

        if self.crosshair_visible:
            painter.setOpacity(ch_alpha)
            
            image_path = None
            if self.crosshair_shape == "MAME":
                image_path = "mame.png"
            elif self.crosshair_shape == "カスタム画像":
                image_path = self.crosshair_image_path

            if image_path and os.path.exists(image_path):
                pixmap = QtGui.QPixmap(image_path)
                if not pixmap.isNull():
                    target_size = self.image_crosshair_size
                    target_rect = QtCore.QRect(self.center_x - target_size // 2, self.center_y - target_size // 2, target_size, target_size)
                    painter.drawPixmap(target_rect, pixmap)
            else:
                color = QtGui.QColor(self.crosshair_color)
                color.setAlphaF(ch_alpha)
                
                if self.crosshair_shape == "十字":
                    # 輪郭の描画 (長方形で描画)
                    if self.crosshair_outline_enabled:
                        painter.setPen(QtCore.Qt.NoPen) # 輪郭のペンは不要
                        outline_color = QtGui.QColor(QtCore.Qt.black)
                        outline_color.setAlphaF(self.crosshair_outline_alpha)
                        painter.setBrush(QtGui.QBrush(outline_color)) # 輪郭の色

                        # floatになる可能性があるのでroundで丸める
                        outline_offset = round((self.crosshair_thickness / 2) + self.crosshair_outline_width)

                        # 縦線 (上) の輪郭
                        painter.drawRect(
                            round(self.center_x - outline_offset),
                            round(self.center_y - self.crosshair_gap - self.crosshair_vline_length - self.crosshair_outline_width), # 上端
                            round(outline_offset * 2), # 幅
                            round(self.crosshair_vline_length + self.crosshair_outline_width * 2) # 高さ
                        )
                        # 縦線 (下) の輪郭
                        painter.drawRect(
                            round(self.center_x - outline_offset),
                            round(self.center_y + self.crosshair_gap - self.crosshair_outline_width), # 上端
                            round(outline_offset * 2), # 幅
                            round(self.crosshair_vline_length + self.crosshair_outline_width * 2) # 高さ
                        )
                        # 横線 (左) の輪郭
                        painter.drawRect(
                            round(self.center_x - self.crosshair_gap - self.crosshair_hline_length - self.crosshair_outline_width), # 左端
                            round(self.center_y - outline_offset),
                            round(self.crosshair_hline_length + self.crosshair_outline_width * 2), # 幅
                            round(outline_offset * 2) # 高さ
                        )
                        # 横線 (右) の輪郭
                        painter.drawRect(
                            round(self.center_x + self.crosshair_gap - self.crosshair_outline_width), # 左端
                            round(self.center_y - outline_offset),
                            round(self.crosshair_hline_length + self.crosshair_outline_width * 2), # 幅
                            round(outline_offset * 2) # 高さ
                        )

                    # 本体の描画
                    if self.crosshair_thickness == 0:
                        pen = QtCore.Qt.NoPen
                    else:
                        pen = QtGui.QPen(color, self.crosshair_thickness, QtCore.Qt.SolidLine, QtCore.Qt.FlatCap)
                    
                    painter.setPen(pen)
                    painter.setBrush(QtCore.Qt.NoBrush) # 本体の描画は塗りつぶしなし

                    # 1pxの線の場合、アンチエイリアシングを一時的に無効にする
                    if self.crosshair_thickness == 1:
                        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)

                    # 縦線 (上)
                    painter.drawLine(self.center_x, self.center_y - self.crosshair_gap - self.crosshair_vline_length,
                                     self.center_x, self.center_y - self.crosshair_gap)
                    # 縦線 (下)
                    painter.drawLine(self.center_x, self.center_y + self.crosshair_gap,
                                     self.center_x, self.center_y + self.crosshair_gap + self.crosshair_vline_length)
                    # 横線 (左)
                    painter.drawLine(self.center_x - self.crosshair_gap - self.crosshair_hline_length, self.center_y,
                                     self.center_x - self.crosshair_gap, self.center_y)
                    # 横線 (右)
                    painter.drawLine(self.center_x + self.crosshair_gap, self.center_y,
                                     self.center_x + self.crosshair_gap + self.crosshair_hline_length, self.center_y)
                    
                    # アンチエイリアシングを元に戻す
                    if self.crosshair_thickness == 1:
                        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

                elif self.crosshair_shape == "円":
                    # 直径は線の内側から測定されるため、描画上の中心半径を計算
                    # 線の中心は (直径/2 + 太さ/2) の位置に来る
                    center_radius = (self.circle_diameter + self.circle_thickness) / 2.0
                    
                    # 描画用の矩形を計算
                    rect = QtCore.QRectF(
                        self.center_x - center_radius,
                        self.center_y - center_radius,
                        center_radius * 2,
                        center_radius * 2
                    )

                    # 輪郭の描画
                    if self.circle_outline_enabled and self.circle_outline_width > 0:
                        # 輪郭は、本体の線の両側に描画される
                        # そのため、輪郭を含めた全体の太さは 本体の太さ + 輪郭の太さ * 2
                        outline_pen_width = self.circle_thickness + self.circle_outline_width * 2
                        outline_color = QtGui.QColor(QtCore.Qt.black)
                        outline_color.setAlphaF(self.circle_outline_alpha)
                        outline_pen = QtGui.QPen(outline_color, outline_pen_width, QtCore.Qt.SolidLine, QtCore.Qt.FlatCap)
                        painter.setPen(outline_pen)
                        painter.setBrush(QtCore.Qt.NoBrush)
                        painter.drawEllipse(rect)

                    # 本体の描画
                    if self.circle_thickness > 0:
                        pen = QtGui.QPen(color, self.circle_thickness, QtCore.Qt.SolidLine, QtCore.Qt.FlatCap)
                        painter.setPen(pen)
                        painter.setBrush(QtCore.Qt.NoBrush)
                        painter.drawEllipse(rect)
                elif self.crosshair_shape == "矢印 (シェブロン)":
                    # 線の太さ
                    if self.chevron_thickness == 0:
                        pen = QtCore.Qt.NoPen
                    else:
                        pen = QtGui.QPen(color, self.chevron_thickness, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap)
                    
                    # 輪郭の描画
                    if self.chevron_outline_enabled and self.chevron_outline_width > 0:
                        outline_pen_width = self.chevron_thickness + self.chevron_outline_width * 2
                        outline_color = QtGui.QColor(QtCore.Qt.black)
                        outline_color.setAlphaF(self.chevron_outline_alpha)
                        outline_pen = QtGui.QPen(outline_color, outline_pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap)
                        painter.setPen(outline_pen)
                        # アンチエイリアシングを一時的に無効にする (1pxの場合)
                        if outline_pen_width == 1:
                            painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
                        
                        # シェブロンのポイントを計算
                        points = [
                            QtCore.QPoint(self.center_x - self.chevron_length, self.center_y + self.chevron_length),
                            QtCore.QPoint(self.center_x, self.center_y),
                            QtCore.QPoint(self.center_x + self.chevron_length, self.center_y + self.chevron_length)
                        ]
                        painter.drawPolyline(QtGui.QPolygon(points))
                        
                        # アンチエイリアシングを元に戻す
                        if outline_pen_width == 1:
                            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

                    painter.setPen(pen)
                    # アンチエイリアシングを一時的に無効にする (1pxの場合)
                    if self.chevron_thickness == 1:
                        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)

                    # シェブロンのポイントを計算
                    points = [
                        QtCore.QPoint(self.center_x - self.chevron_length, self.center_y + self.chevron_length),
                        QtCore.QPoint(self.center_x, self.center_y),
                        QtCore.QPoint(self.center_x + self.chevron_length, self.center_y + self.chevron_length)
                    ]
                    painter.drawPolyline(QtGui.QPolygon(points))

                    # アンチエイリアシングを元に戻す
                    if self.chevron_thickness == 1:
                        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

    def _draw_dot(self, painter):
        dot_alpha = self.dot_alpha
        if self.fade_on_shoot_enabled and self.is_shooting:
            dot_alpha *= 0.3

        if self.dot_visible and self.dot_radius > 0:
            painter.setOpacity(1.0) # Reset opacity for dot
            outer_color = QtGui.QColor(self.dot_outer_color)
            outer_color.setAlphaF(dot_alpha)
            painter.setBrush(QtGui.QBrush(outer_color))
            painter.setPen(QtGui.QPen(outer_color))
            painter.drawEllipse(QtCore.QRect(self.center_x - self.dot_radius, self.center_y - self.dot_radius, self.dot_radius * 2, self.dot_radius * 2))
            if self.dot_radius > 1:
                inner_r = self.dot_radius - 1
                inner_color = QtGui.QColor(self.dot_inner_color)
                inner_color.setAlphaF(dot_alpha)
                painter.setBrush(QtGui.QBrush(inner_color)); painter.setPen(QtGui.QPen(inner_color))
                painter.drawEllipse(QtCore.QRect(self.center_x - inner_r, self.center_y - inner_r, inner_r * 2, inner_r * 2))

    def paintEvent(self, event):
        if not self.master_enabled:
            return
        
        self.center_x = self.width() // 2
        self.center_y = self.height() // 2
                
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # --- カスタム形状 (.crshr) の描画 --- #
        shape = self.crosshair_shape
        crshr_path = os.path.join(self.shape_preset_folder, shape + ".crshr")

        if os.path.exists(crshr_path):
            self.render_crshr(painter, crshr_path)
            # .crshrを描画した場合は、以降の描画処理をスキップ
        else:
            # --- 標準形状の描画 --- #
            if self.drawing_order == "crosshair_on_top":
                self._draw_dot(painter)
                self._draw_crosshair(painter)
            else: # "dot_on_top" or default
                self._draw_crosshair(painter)
                self._draw_dot(painter)
