# model_module.py
# Loads and renders the 3D hand model from OBJ file

import numpy as np
from OpenGL.GL import *

class OBJLoader:
    def __init__(self, filename):
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.vbo_vertices = None
        self.vbo_normals = None
        self.vertex_count = 0
        self.load_obj(filename)
        self.create_vbo()

    def load_obj(self, filename):
        """Load .obj file"""
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                values = line.split()
                if not values:
                    continue
                if values[0] == 'v':
                    self.vertices.append([float(x) for x in values[1:4]])
                elif values[0] == 'vn':
                    self.normals.append([float(x) for x in values[1:4]])
                elif values[0] == 'f':
                    face = []
                    for v in values[1:]:
                        w = v.split('/')
                        face.append([
                            int(w[0]) if w[0] else 0,
                            int(w[2]) if len(w) > 2 and w[2] else 0
                        ])
                    self.faces.append(face)

    def create_vbo(self):
        """Generate Vertex Buffer Objects"""
        vertex_data, normal_data = [], []
        for face in self.faces:
            for vertex in face:
                vertex_data.extend(self.vertices[vertex[0]-1])
                if vertex[1]:
                    normal_data.extend(self.normals[vertex[1]-1])
                else:
                    normal_data.extend([0, 0, 1])

        self.vertex_count = len(vertex_data) // 3
        vertex_array = np.array(vertex_data, dtype=np.float32)
        normal_array = np.array(normal_data, dtype=np.float32)

        self.vbo_vertices = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glBufferData(GL_ARRAY_BUFFER, vertex_array.nbytes, vertex_array, GL_STATIC_DRAW)

        self.vbo_normals = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
        glBufferData(GL_ARRAY_BUFFER, normal_array.nbytes, normal_array, GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def render(self):
        """Render model"""
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glVertexPointer(3, GL_FLOAT, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
        glNormalPointer(GL_FLOAT, 0, None)
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
