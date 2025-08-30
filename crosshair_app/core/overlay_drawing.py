import os
import json
import math
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
                color = QtGui.QColor(self.crosshair_color) # Moved here
                color.setAlphaF(ch_alpha) # Moved here
                
                if self.crosshair_shape == "十字":
                    # Debugging: Print values
                    print(f"Debug: hline_length={self.crosshair_hline_length}, vline_length={self.crosshair_vline_length}, gap={self.crosshair_gap}, thickness={self.crosshair_thickness}, outline_width={self.crosshair_outline_width}")

                    # 輪郭の描画
                    if self.crosshair_outline_enabled and self.crosshair_outline_width > 0:
                        outline_color = QtGui.QColor(QtCore.Qt.black)
                        outline_color.setAlphaF(self.crosshair_outline_alpha)
                        painter.setPen(QtCore.Qt.NoPen) # 輪郭は塗りつぶしなのでペンは不要
                        painter.setBrush(QtGui.QBrush(outline_color)) # 輪郭の色で塗りつぶす

                        half_thickness = self.crosshair_thickness / 2.0
                        
                        # 縦線 (上) の輪郭
                        rect_v_top_outline = QtCore.QRectF(
                            self.center_x - (half_thickness + self.crosshair_outline_width),
                            self.center_y - self.crosshair_gap - self.crosshair_vline_length - self.crosshair_outline_width,
                            self.crosshair_thickness + self.crosshair_outline_width * 2,
                            self.crosshair_vline_length + self.crosshair_outline_width * 2
                        )
                        painter.drawRect(rect_v_top_outline)

                        # 縦線 (下) の輪郭
                        rect_v_bottom_outline = QtCore.QRectF(
                            self.center_x - (half_thickness + self.crosshair_outline_width),
                            self.center_y + self.crosshair_gap - self.crosshair_outline_width,
                            self.crosshair_thickness + self.crosshair_outline_width * 2,
                            self.crosshair_vline_length + self.crosshair_outline_width * 2
                        )
                        painter.drawRect(rect_v_bottom_outline)

                        # 横線 (左) の輪郭
                        rect_h_left_outline = QtCore.QRectF(
                            self.center_x - self.crosshair_gap - self.crosshair_hline_length - self.crosshair_outline_width,
                            self.center_y - (half_thickness + self.crosshair_outline_width),
                            self.crosshair_hline_length + self.crosshair_outline_width * 2,
                            self.crosshair_thickness + self.crosshair_outline_width * 2
                        )
                        painter.drawRect(rect_h_left_outline)

                        # 横線 (右) の輪郭
                        rect_h_right_outline = QtCore.QRectF(
                            self.center_x + self.crosshair_gap - self.crosshair_outline_width,
                            self.center_y - (half_thickness + self.crosshair_outline_width),
                            self.crosshair_hline_length + self.crosshair_outline_width * 2,
                            self.crosshair_thickness + self.crosshair_outline_width * 2
                        )
                        painter.drawRect(rect_h_right_outline)
                        
                    # 本体の描画
                    # 内側の透明度を適用
                    inner_color = QtGui.QColor(self.crosshair_color)
                    inner_color.setAlphaF(self.crosshair_inner_alpha)
                    painter.setPen(QtCore.Qt.NoPen) # 本体は塗りつぶしなのでペンは不要
                    painter.setBrush(QtGui.QBrush(inner_color)) # 本体の色で塗りつぶす

                    # 縦線 (上)
                    rect_v_top_main = QtCore.QRectF(
                        self.center_x - half_thickness,
                        self.center_y - self.crosshair_gap - self.crosshair_vline_length,
                        self.crosshair_thickness,
                        self.crosshair_vline_length
                    )
                    painter.drawRect(rect_v_top_main)

                    # 縦線 (下)
                    rect_v_bottom_main = QtCore.QRectF(
                        self.center_x - half_thickness,
                        self.center_y + self.crosshair_gap,
                        self.crosshair_thickness,
                        self.crosshair_vline_length
                    )
                    painter.drawRect(rect_v_bottom_main)

                    # 横線 (左)
                    rect_h_left_main = QtCore.QRectF(
                        self.center_x - self.crosshair_gap - self.crosshair_hline_length,
                        self.center_y - half_thickness,
                        self.crosshair_hline_length,
                        self.crosshair_thickness
                    )
                    painter.drawRect(rect_h_left_main)

                    # 横線 (右)
                    rect_h_right_main = QtCore.QRectF(
                        self.center_x + self.crosshair_gap,
                        self.center_y - half_thickness,
                        self.crosshair_hline_length,
                        self.crosshair_thickness
                    )
                    painter.drawRect(rect_h_right_main)

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

            if self.dot_shape == "円":
                painter.drawEllipse(QtCore.QRect(self.center_x - self.dot_radius, self.center_y - self.dot_radius, self.dot_radius * 2, self.dot_radius * 2))
                if self.dot_radius > 1:
                    inner_r = self.dot_radius - 1
                    inner_color = QtGui.QColor(self.dot_inner_color)
                    inner_color.setAlphaF(dot_alpha)
                    painter.setBrush(QtGui.QBrush(inner_color)); painter.setPen(QtGui.QPen(inner_color))
                    painter.drawEllipse(QtCore.QRect(self.center_x - inner_r, self.center_y - inner_r, inner_r * 2, inner_r * 2))
            elif self.dot_shape == "正方形":
                side_length = self.dot_radius * 2
                painter.drawRect(QtCore.QRect(self.center_x - self.dot_radius, self.center_y - self.dot_radius, side_length, side_length))
                if self.dot_radius > 1:
                    inner_r = self.dot_radius - 1
                    inner_color = QtGui.QColor(self.dot_inner_color)
                    inner_color.setAlphaF(dot_alpha)
                    painter.setBrush(QtGui.QBrush(inner_color)); painter.setPen(QtGui.QPen(inner_color))
                    painter.drawRect(QtCore.QRect(self.center_x - inner_r, self.center_y - inner_r, inner_r * 2, inner_r * 2))
            elif self.dot_shape == "正三角形上向き":
                # 正三角形の計算
                # dot_radius が外側の三角形の半径、dot_radius - 1 が内側の三角形の半径と考える
                
                # 外側の三角形 (輪郭用) の計算
                outer_side_length = self.dot_radius * 2.0
                outer_height = outer_side_length * (math.sqrt(3) / 2)
                
                # 外側の三角形の頂点 (上の頂点が self.center_y に来るように)
                outer_points = [
                    QtCore.QPointF(self.center_x, self.center_y), # 上の頂点
                    QtCore.QPointF(self.center_x - outer_side_length / 2, self.center_y + outer_height), # 左下の頂点
                    QtCore.QPointF(self.center_x + outer_side_length / 2, self.center_y + outer_height)  # 右下の頂点
                ]

                # 輪郭の描画 (dot_radius > 1 の場合のみ)
                if self.dot_radius > 1:
                    outline_color = QtGui.QColor(self.dot_outer_color)
                    outline_color.setAlphaF(dot_alpha)
                    outline_pen_width = 1 
                    
                    painter.setPen(QtGui.QPen(outline_color, outline_pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                    painter.setBrush(QtCore.Qt.NoBrush) 
                    painter.drawPolygon(QtGui.QPolygonF(outer_points))

                # 内側の三角形 (本体) の計算
                inner_side_length = (self.dot_radius - 1) * 2.0 if self.dot_radius > 1 else self.dot_radius * 2.0
                inner_height = inner_side_length * (math.sqrt(3) / 2)

                # 内側の三角形の頂点 (上の頂点が self.center_y に来るように)
                inner_points = [
                    QtCore.QPointF(self.center_x, self.center_y), # 上の頂点
                    QtCore.QPointF(self.center_x - inner_side_length / 2, self.center_y + inner_height), # 左下の頂点
                    QtCore.QPointF(self.center_x + inner_side_length / 2, self.center_y + inner_height), # 右下の頂点
                ]

                # 本体の描画
                fill_color = QtGui.QColor(self.dot_inner_color) if self.dot_radius > 1 else QtGui.QColor(self.dot_outer_color)
                fill_color.setAlphaF(dot_alpha)
                painter.setBrush(QtGui.QBrush(fill_color))
                painter.setPen(QtCore.Qt.NoPen) 
                painter.drawPolygon(QtGui.QPolygonF(inner_points))

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
