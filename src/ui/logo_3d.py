"""
3D OpenGL Animated Helyxium Logo
Professional-grade 3D logo with rotating globe, helixes, and dynamic lighting.
"""

import math
import time
import numpy as np
from typing import Tuple, Optional
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtOpenGL import QOpenGLVersionProfile

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL import GL
    import moderngl as mgl
    import pyrr
    OPENGL_AVAILABLE = True
except ImportError as e:
    print(f"OpenGL import failed: {e}")
    OPENGL_AVAILABLE = False

from ..utils.logging import get_logger


class HelyxiumLogo3D(QOpenGLWidget):
    """
    3D animated Helyxium logo with OpenGL rendering.
    
    Features:
    - Rotating 3D globe with wireframe
    - Counter-rotating red and blue helixes  
    - Dynamic lighting effects
    - Particle system for connection points
    - VR-ready rendering
    """
    
    animation_finished = pyqtSignal()
    
    def __init__(self, parent=None, animation_speed: float = 1.0):
        super().__init__(parent)
        
        self.logger = get_logger(__name__)
        
        if not OPENGL_AVAILABLE:
            self.logger.error("OpenGL dependencies not available")
            return
        
        # Animation settings
        self.animation_speed = animation_speed
        self.animation_time = 0.0
        self.is_animating = True
        
        # Rotation angles
        self.globe_rotation = 0.0
        self.helix_rotation = 0.0
        
        # Colors (theme-aware)
        self.primary_color = [0.2, 0.4, 0.8, 1.0]  # Blue
        self.secondary_color = [0.8, 0.2, 0.4, 1.0]  # Red
        self.background_color = [0.05, 0.05, 0.05, 1.0]  # Dark
        
        # OpenGL context
        self.ctx: Optional[mgl.Context] = None
        self.program: Optional[mgl.Program] = None
        self.vao_globe: Optional[mgl.VertexArray] = None
        self.vao_helix_blue: Optional[mgl.VertexArray] = None
        self.vao_helix_red: Optional[mgl.VertexArray] = None
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
        
        # Set OpenGL format
        fmt = self.format()
        fmt.setVersion(3, 3)
        fmt.setProfile(QOpenGLVersionProfile.CoreProfile)
        fmt.setSamples(4)  # Anti-aliasing
        self.setFormat(fmt)
        
        self.logger.info("3D logo widget initialized")
    
    def initializeGL(self):
        """Initialize OpenGL context and resources."""
        if not OPENGL_AVAILABLE:
            return
            
        try:
            # Initialize ModernGL context
            self.ctx = mgl.create_context()
            
            # Enable depth testing and blending
            self.ctx.enable(mgl.DEPTH_TEST)
            self.ctx.enable(mgl.BLEND)
            self.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
            
            # Create shader program
            self._create_shaders()
            
            # Create 3D geometry
            self._create_globe_geometry()
            self._create_helix_geometry()
            
            self.logger.info("OpenGL context initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenGL: {e}")
    
    def _create_shaders(self):
        """Create vertex and fragment shaders."""
        vertex_shader = """
        #version 330 core
        
        layout (location = 0) in vec3 position;
        layout (location = 1) in vec3 normal;
        layout (location = 2) in vec4 color;
        
        uniform mat4 mvp_matrix;
        uniform mat4 model_matrix;
        uniform mat4 normal_matrix;
        uniform vec3 light_pos;
        uniform float time;
        
        out vec4 vertex_color;
        out vec3 fragment_pos;
        out vec3 fragment_normal;
        out float vertex_time;
        
        void main() {
            gl_Position = mvp_matrix * vec4(position, 1.0);
            fragment_pos = vec3(model_matrix * vec4(position, 1.0));
            fragment_normal = mat3(normal_matrix) * normal;
            vertex_color = color;
            vertex_time = time;
        }
        """
        
        fragment_shader = """
        #version 330 core
        
        in vec4 vertex_color;
        in vec3 fragment_pos;
        in vec3 fragment_normal;
        in float vertex_time;
        
        uniform vec3 light_pos;
        uniform vec3 view_pos;
        uniform bool use_lighting;
        uniform float alpha;
        
        out vec4 frag_color;
        
        void main() {
            vec4 color = vertex_color;
            
            if (use_lighting) {
                // Ambient lighting
                float ambient_strength = 0.3;
                vec3 ambient = ambient_strength * color.rgb;
                
                // Diffuse lighting
                vec3 norm = normalize(fragment_normal);
                vec3 light_dir = normalize(light_pos - fragment_pos);
                float diff = max(dot(norm, light_dir), 0.0);
                vec3 diffuse = diff * color.rgb;
                
                // Specular lighting
                float specular_strength = 0.5;
                vec3 view_dir = normalize(view_pos - fragment_pos);
                vec3 reflect_dir = reflect(-light_dir, norm);
                float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 32);
                vec3 specular = specular_strength * spec * vec3(1.0);
                
                // Animated glow effect
                float glow = 0.5 + 0.3 * sin(vertex_time * 2.0);
                
                color.rgb = (ambient + diffuse + specular) * glow;
            }
            
            // Animated alpha for breathing effect
            float breath = 0.8 + 0.2 * sin(vertex_time * 1.5);
            frag_color = vec4(color.rgb, color.a * alpha * breath);
        }
        """
        
        self.program = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )
    
    def _create_globe_geometry(self):
        """Create 3D globe wireframe geometry."""
        # Create sphere vertices (wireframe)
        vertices = []
        colors = []
        indices = []
        
        radius = 1.0
        rings = 20
        sectors = 20
        
        # Generate vertices
        for i in range(rings + 1):
            lat = math.pi * (-0.5 + i / rings)
            y = radius * math.sin(lat)
            radius_at_lat = radius * math.cos(lat)
            
            for j in range(sectors + 1):
                lon = 2 * math.pi * j / sectors
                x = radius_at_lat * math.cos(lon)
                z = radius_at_lat * math.sin(lon)
                
                # Position
                vertices.extend([x, y, z])
                
                # Normal (same as position for sphere)
                vertices.extend([x, y, z])
                
                # Color (blue with alpha)
                colors.extend(self.primary_color)
        
        # Create wireframe indices
        for i in range(rings):
            for j in range(sectors):
                current = i * (sectors + 1) + j
                next_ring = (i + 1) * (sectors + 1) + j
                
                # Horizontal lines
                if j < sectors:
                    indices.extend([current, current + 1])
                
                # Vertical lines
                if i < rings:
                    indices.extend([current, next_ring])
        
        # Combine vertices and colors
        vertex_data = []
        for i in range(0, len(vertices), 6):  # position + normal
            vertex_data.extend(vertices[i:i+6])  # pos + normal
            color_idx = (i // 6) * 4
            vertex_data.extend(colors[color_idx:color_idx+4])  # color
        
        # Create vertex buffer and array
        vbo = self.ctx.buffer(np.array(vertex_data, dtype=np.float32))
        ibo = self.ctx.buffer(np.array(indices, dtype=np.uint32))
        
        self.vao_globe = self.ctx.vertex_array(
            self.program,
            [(vbo, '3f 3f 4f', 'position', 'normal', 'color')],
            ibo
        )
    
    def _create_helix_geometry(self):
        """Create helix spiral geometries (red and blue)."""
        def create_helix(turns: int, radius: float, height: float, color: list):
            vertices = []
            indices = []
            
            points_per_turn = 50
            total_points = turns * points_per_turn
            
            for i in range(total_points):
                t = i / points_per_turn
                angle = 2 * math.pi * t
                
                # Helix equations
                x = radius * math.cos(angle)
                y = (height * t / turns) - height / 2
                z = radius * math.sin(angle)
                
                # Position
                vertices.extend([x, y, z])
                
                # Normal (pointing outward)
                normal_x = math.cos(angle)
                normal_y = 0.0
                normal_z = math.sin(angle)
                vertices.extend([normal_x, normal_y, normal_z])
                
                # Color
                vertices.extend(color)
                
                # Create line segments
                if i > 0:
                    indices.extend([i - 1, i])
            
            return vertices, indices
        
        # Create blue helix (outer)
        blue_vertices, blue_indices = create_helix(3, 0.8, 2.0, self.primary_color)
        vbo_blue = self.ctx.buffer(np.array(blue_vertices, dtype=np.float32))
        ibo_blue = self.ctx.buffer(np.array(blue_indices, dtype=np.uint32))
        
        self.vao_helix_blue = self.ctx.vertex_array(
            self.program,
            [(vbo_blue, '3f 3f 4f', 'position', 'normal', 'color')],
            ibo_blue
        )
        
        # Create red helix (inner)
        red_vertices, red_indices = create_helix(3, 0.6, 2.0, self.secondary_color)
        vbo_red = self.ctx.buffer(np.array(red_vertices, dtype=np.float32))
        ibo_red = self.ctx.buffer(np.array(red_indices, dtype=np.uint32))
        
        self.vao_helix_red = self.ctx.vertex_array(
            self.program,
            [(vbo_red, '3f 3f 4f', 'position', 'normal', 'color')],
            ibo_red
        )
    
    def paintGL(self):
        """Render the 3D logo."""
        if not OPENGL_AVAILABLE or not self.ctx:
            return
        
        try:
            # Clear buffers
            self.ctx.clear(*self.background_color)
            
            # Set viewport
            width, height = self.size().width(), self.size().height()
            self.ctx.viewport = (0, 0, width, height)
            
            # Calculate matrices
            aspect = width / height if height > 0 else 1.0
            
            # Projection matrix
            proj_matrix = pyrr.matrix44.create_perspective_projection(
                45.0, aspect, 0.1, 100.0
            )
            
            # View matrix (camera position)
            view_matrix = pyrr.matrix44.create_look_at(
                [0, 0, 5],  # Camera position
                [0, 0, 0],  # Look at origin
                [0, 1, 0]   # Up vector
            )
            
            # Model matrices for each component
            globe_model = pyrr.matrix44.create_rotation_y(self.globe_rotation)
            
            helix_blue_model = pyrr.matrix44.create_rotation_y(-self.helix_rotation * 0.7)
            helix_red_model = pyrr.matrix44.create_rotation_y(self.helix_rotation * 0.9)
            
            # Set uniforms
            self.program['light_pos'] = [2.0, 3.0, 4.0]
            self.program['view_pos'] = [0.0, 0.0, 5.0]
            self.program['time'] = self.animation_time
            self.program['use_lighting'] = True
            self.program['alpha'] = 0.9
            
            # Render globe
            mvp = proj_matrix @ view_matrix @ globe_model
            self.program['mvp_matrix'] = mvp.astype(np.float32)
            self.program['model_matrix'] = globe_model.astype(np.float32)
            self.program['normal_matrix'] = globe_model.astype(np.float32)
            
            self.ctx.line_width = 2.0
            self.vao_globe.render(mgl.LINES)
            
            # Render blue helix
            mvp = proj_matrix @ view_matrix @ helix_blue_model
            self.program['mvp_matrix'] = mvp.astype(np.float32)
            self.program['model_matrix'] = helix_blue_model.astype(np.float32)
            self.program['normal_matrix'] = helix_blue_model.astype(np.float32)
            
            self.ctx.line_width = 3.0
            self.vao_helix_blue.render(mgl.LINES)
            
            # Render red helix  
            mvp = proj_matrix @ view_matrix @ helix_red_model
            self.program['mvp_matrix'] = mvp.astype(np.float32)
            self.program['model_matrix'] = helix_red_model.astype(np.float32)
            self.program['normal_matrix'] = helix_red_model.astype(np.float32)
            
            self.ctx.line_width = 3.0
            self.vao_helix_red.render(mgl.LINES)
            
        except Exception as e:
            self.logger.error(f"Render error: {e}")
    
    def resizeGL(self, width: int, height: int):
        """Handle window resize."""
        if self.ctx:
            self.ctx.viewport = (0, 0, width, height)
    
    def update_animation(self):
        """Update animation state."""
        if not self.is_animating:
            return
        
        # Update time
        dt = 0.016 * self.animation_speed  # ~60 FPS
        self.animation_time += dt
        
        # Update rotations
        self.globe_rotation += dt * 0.5  # Slow globe rotation
        self.helix_rotation += dt * 1.2  # Faster helix rotation
        
        # Keep angles in reasonable range
        if self.globe_rotation > 2 * math.pi:
            self.globe_rotation -= 2 * math.pi
        if self.helix_rotation > 2 * math.pi:
            self.helix_rotation -= 2 * math.pi
        
        # Trigger repaint
        self.update()
    
    def set_theme_colors(self, is_dark_theme: bool):
        """Update colors based on theme."""
        if is_dark_theme:
            self.background_color = [0.05, 0.05, 0.05, 1.0]
            self.primary_color = [0.3, 0.5, 0.9, 0.8]
            self.secondary_color = [0.9, 0.3, 0.5, 0.8]
        else:
            self.background_color = [0.95, 0.95, 0.95, 1.0]
            self.primary_color = [0.2, 0.4, 0.8, 0.9]
            self.secondary_color = [0.8, 0.2, 0.4, 0.9]
    
    def start_animation(self):
        """Start the animation."""
        self.is_animating = True
        self.animation_time = 0.0
        self.timer.start(16)
    
    def stop_animation(self):
        """Stop the animation."""
        self.is_animating = False
        self.timer.stop()
        self.animation_finished.emit()
    
    def set_animation_speed(self, speed: float):
        """Set animation speed multiplier."""
        self.animation_speed = max(0.1, min(5.0, speed))


class Logo3DFallback(QWidget):
    """Fallback widget when OpenGL is not available."""
    
    animation_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.logger.warning("Using fallback logo - OpenGL not available")
        
        # Simple timer for fallback
        self.timer = QTimer()
        self.timer.timeout.connect(self.animation_finished.emit)
        self.timer.setSingleShot(True)
    
    def start_animation(self):
        """Start fallback animation."""
        self.timer.start(3000)  # 3 second fallback
    
    def stop_animation(self):
        """Stop fallback animation."""
        self.timer.stop()
        self.animation_finished.emit()
    
    def set_theme_colors(self, is_dark_theme: bool):
        """Theme awareness for fallback."""
        pass
    
    def set_animation_speed(self, speed: float):
        """Speed control for fallback."""
        pass


def create_logo_widget(parent=None) -> QWidget:
    """Factory function to create the best available logo widget."""
    # Try the simple version first (more compatible)
    from .logo_simple_3d import create_simple_logo_widget
    try:
        return create_simple_logo_widget(parent)
    except Exception as e:
        print(f"Simple logo failed: {e}")
        
        # Try full OpenGL version
        if OPENGL_AVAILABLE:
            try:
                return HelyxiumLogo3D(parent)
            except Exception as e:
                print(f"OpenGL logo failed: {e}")
        
        # Final fallback
        return Logo3DFallback(parent)