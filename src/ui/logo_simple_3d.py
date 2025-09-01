"""
Simplified 3D Logo Animation
Uses PyQt6's built-in OpenGL for maximum compatibility.
"""

import math
import time
from typing import Tuple, Optional
from PyQt6.QtCore import QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QVariantAnimation
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QTransform, QFont
from PyQt6.QtCore import Qt, QRect, QPoint

from ..utils.logging import get_logger


class SimpleHelyxiumLogo3D(QWidget):
    """
    Simplified 3D animated Helyxium logo using QPainter.
    
    Features:
    - Rotating wireframe globe
    - Animated helixes with depth illusion
    - Dynamic colors based on theme
    - Smooth animations with easing
    - No external OpenGL dependencies
    """
    
    animation_finished = pyqtSignal()
    
    def __init__(self, parent=None, animation_speed: float = 1.0):
        super().__init__(parent)
        
        self.logger = get_logger(__name__)
        self.animation_speed = animation_speed
        
        # Animation state
        self.globe_rotation = 0.0
        self.helix_rotation = 0.0
        self.animation_time = 0.0
        self.is_animating = True
        
        # Colors (theme-aware)
        self.primary_color = QColor(51, 102, 204, 200)  # Blue with alpha
        self.secondary_color = QColor(204, 51, 102, 200)  # Red with alpha
        self.background_color = QColor(13, 13, 13, 255)  # Dark
        self.text_color = QColor(255, 255, 255, 255)
        
        # Animation properties
        self.rotation_animation = QVariantAnimation()
        self.rotation_animation.setDuration(10000)  # 10 seconds for full rotation
        self.rotation_animation.setStartValue(0.0)
        self.rotation_animation.setEndValue(360.0)
        self.rotation_animation.setLoopCount(-1)  # Infinite loop
        self.rotation_animation.valueChanged.connect(self._update_rotation)
        
        # Breathing effect animation
        self.breathing_animation = QVariantAnimation()
        self.breathing_animation.setDuration(3000)  # 3 seconds
        self.breathing_animation.setStartValue(0.8)
        self.breathing_animation.setEndValue(1.2)
        self.breathing_animation.setLoopCount(-1)
        self.breathing_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.breathing_animation.valueChanged.connect(self.update)
        
        # Setup widget
        self.setMinimumSize(400, 400)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        self.logger.info("Simple 3D logo widget initialized")
    
    def paintEvent(self, event):
        """Paint the 3D logo using QPainter."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        # Clear background
        painter.fillRect(self.rect(), self.background_color)
        
        # Get center and radius
        center = QPoint(self.width() // 2, self.height() // 2)
        base_radius = min(self.width(), self.height()) // 4
        
        # Get breathing effect scale
        breathing_scale = self.breathing_animation.currentValue() if self.breathing_animation.currentValue() else 1.0
        radius = int(base_radius * breathing_scale)
        
        # Draw the wireframe globe
        self._draw_globe(painter, center, radius)
        
        # Draw the helixes
        self._draw_helix(painter, center, radius, self.primary_color, self.helix_rotation)
        self._draw_helix(painter, center, radius * 0.75, self.secondary_color, -self.helix_rotation * 1.3)
        
        # Draw center glow effect
        self._draw_center_glow(painter, center, radius // 3)
    
    def _draw_globe(self, painter: QPainter, center: QPoint, radius: int):
        """Draw wireframe globe."""
        painter.setPen(QPen(self.primary_color, 2, Qt.PenStyle.SolidLine))
        
        # Draw main circle
        painter.drawEllipse(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        
        # Draw latitude lines
        for i in range(1, 4):
            ellipse_height = int(radius * 2 * math.sin(math.pi * i / 4))
            y_offset = int(radius * math.cos(math.pi * i / 4))
            
            painter.drawEllipse(
                center.x() - radius, 
                center.y() - ellipse_height // 2 + y_offset, 
                radius * 2, 
                ellipse_height
            )
            
            painter.drawEllipse(
                center.x() - radius, 
                center.y() - ellipse_height // 2 - y_offset, 
                radius * 2, 
                ellipse_height
            )
        
        # Draw longitude lines (with rotation)
        for i in range(6):
            angle = (self.globe_rotation + i * 30) * math.pi / 180
            
            # Create rotated ellipse for longitude
            transform = QTransform()
            transform.translate(center.x(), center.y())
            transform.rotate(angle * 180 / math.pi)
            transform.translate(-center.x(), -center.y())
            
            painter.setTransform(transform)
            
            # Draw vertical ellipse
            ellipse_width = int(radius * 0.3)
            painter.drawEllipse(
                center.x() - ellipse_width // 2,
                center.y() - radius,
                ellipse_width,
                radius * 2
            )
            
            painter.resetTransform()
    
    def _draw_helix(self, painter: QPainter, center: QPoint, radius: int, color: QColor, rotation: float):
        """Draw animated helix spiral."""
        painter.setPen(QPen(color, 3, Qt.PenStyle.SolidLine))
        
        # Number of turns and points per turn
        turns = 3
        points_per_turn = 50
        total_points = turns * points_per_turn
        height = radius * 2
        
        points = []
        
        for i in range(total_points):
            t = i / points_per_turn
            angle = 2 * math.pi * t + rotation * math.pi / 180
            
            # Helix coordinates
            x = radius * 0.7 * math.cos(angle)
            y = (height * t / turns) - height / 2
            z = radius * 0.7 * math.sin(angle)
            
            # Simple 3D projection (perspective)
            perspective_scale = 1.0 + z / (radius * 4)
            screen_x = center.x() + int(x * perspective_scale)
            screen_y = center.y() + int(y)
            
            points.append(QPoint(screen_x, screen_y))
        
        # Draw the helix as connected line segments
        for i in range(1, len(points)):
            # Vary alpha based on z-depth for 3D effect
            t = i / len(points)
            angle = 2 * math.pi * (i / points_per_turn) * turns + rotation * math.pi / 180
            z_factor = (math.sin(angle) + 1) / 2  # 0 to 1
            
            alpha = int(100 + 155 * z_factor)  # 100 to 255
            depth_color = QColor(color.red(), color.green(), color.blue(), alpha)
            painter.setPen(QPen(depth_color, 3, Qt.PenStyle.SolidLine))
            
            painter.drawLine(points[i-1], points[i])
    
    def _draw_center_glow(self, painter: QPainter, center: QPoint, radius: int):
        """Draw glowing center effect."""
        # Create radial gradient
        gradient_radius = radius
        
        for i in range(10):
            alpha = int(30 * (10 - i) / 10)
            glow_color = QColor(51, 102, 204, alpha)
            painter.setPen(QPen(glow_color, 1, Qt.PenStyle.SolidLine))
            
            glow_radius = int(gradient_radius * (i + 1) / 10)
            painter.drawEllipse(
                center.x() - glow_radius,
                center.y() - glow_radius,
                glow_radius * 2,
                glow_radius * 2
            )
    
    def _update_rotation(self, value):
        """Update rotation values from animation."""
        self.globe_rotation = value * 0.5  # Slower globe rotation
        self.helix_rotation = value * 1.2  # Faster helix rotation
        self.update()  # Trigger repaint
    
    def start_animation(self):
        """Start the logo animation."""
        self.is_animating = True
        self.rotation_animation.start()
        self.breathing_animation.start()
        self.logger.info("Started simple 3D logo animation")
    
    def stop_animation(self):
        """Stop the logo animation."""
        self.is_animating = False
        self.rotation_animation.stop()
        self.breathing_animation.stop()
        self.animation_finished.emit()
        self.logger.info("Stopped simple 3D logo animation")
    
    def set_theme_colors(self, is_dark_theme: bool):
        """Update colors based on theme."""
        if is_dark_theme:
            self.background_color = QColor(13, 13, 13, 255)
            self.primary_color = QColor(76, 128, 230, 200)  # Brighter blue for dark theme
            self.secondary_color = QColor(230, 76, 128, 200)  # Brighter red for dark theme
            self.text_color = QColor(255, 255, 255, 255)
        else:
            self.background_color = QColor(242, 242, 242, 255)
            self.primary_color = QColor(51, 102, 204, 200)  # Standard blue for light theme
            self.secondary_color = QColor(204, 51, 102, 200)  # Standard red for light theme
            self.text_color = QColor(51, 51, 51, 255)
        
        self.update()  # Trigger repaint with new colors
    
    def set_animation_speed(self, speed: float):
        """Set animation speed multiplier."""
        self.animation_speed = max(0.1, min(5.0, speed))
        
        # Update animation durations
        if self.rotation_animation.state() == QVariantAnimation.State.Running:
            self.rotation_animation.setDuration(int(10000 / self.animation_speed))
        if self.breathing_animation.state() == QVariantAnimation.State.Running:
            self.breathing_animation.setDuration(int(3000 / self.animation_speed))


class LogoWithText(QWidget):
    """Logo widget with text below."""
    
    animation_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 3D Logo
        self.logo_3d = SimpleHelyxiumLogo3D(self)
        self.logo_3d.animation_finished.connect(self.animation_finished.emit)
        layout.addWidget(self.logo_3d, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Logo text
        self.logo_text = QLabel("HELYXIUM")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        self.logo_text.setFont(font)
        self.logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_text.setStyleSheet("""
            QLabel {
                color: #0078d4;
                background: transparent;
                margin: 10px;
            }
        """)
        layout.addWidget(self.logo_text, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def start_animation(self):
        """Start logo animation."""
        self.logo_3d.start_animation()
    
    def stop_animation(self):
        """Stop logo animation."""
        self.logo_3d.stop_animation()
    
    def set_theme_colors(self, is_dark_theme: bool):
        """Update theme colors."""
        self.logo_3d.set_theme_colors(is_dark_theme)
        
        if is_dark_theme:
            self.logo_text.setStyleSheet("""
                QLabel {
                    color: #4C80E6;
                    background: transparent;
                    margin: 10px;
                }
            """)
        else:
            self.logo_text.setStyleSheet("""
                QLabel {
                    color: #0078d4;
                    background: transparent;
                    margin: 10px;
                }
            """)
    
    def set_animation_speed(self, speed: float):
        """Set animation speed."""
        self.logo_3d.set_animation_speed(speed)


def create_simple_logo_widget(parent=None) -> QWidget:
    """Factory function to create the simple 3D logo widget."""
    return LogoWithText(parent)