import OpenGL.GL as ogl
import numpy
import pyrr


class RenderException(Exception):
    pass


class VertexState:
    """
    Maintains a draw state.
    Will track any VertexBuffers created while bound
    """

    def __init__(self) -> None:
        self.vao = ogl.glGenVertexArrays(1)

    def __enter__(self) -> None:
        self.bind()

    def __exit__(self, type, value, traceback) -> None:
        self.unbind()

    def bind(self) -> None:
        ogl.glBindVertexArray(self.vao)

    def unbind(self) -> None:
        ogl.glBindVertexArray(0)

    def draw_array(self, length: int) -> None:
        ogl.glDrawArrays(ogl.GL_TRIANGLES, 0, length)

    def draw_indexed_elements(self, length: int) -> None:
        ogl.glDrawElements(ogl.GL_TRIANGLES, length, ogl.GL_UNSIGNED_INT, None)

    def draw_instanced(self, length, instances):
        ogl.glDrawArraysInstanced(ogl.GL_TRIANGLES, 0, length, instances)


class VertexBuffer:
    """
    Respresents a buffer of data
    Probably should be run within a VertexState with block
    """

    def __init__(self, data: list, program, name: str, instanced=False) -> None:
        self.vbo = ogl.glGenBuffers(1)
        self.data = numpy.array(data, dtype="float32")
        self.name = name
        self.program = program
        self.instanced = instanced
        self._buffer_data()

    def bind(self) -> None:
        ogl.glBindBuffer(ogl.GL_ARRAY_BUFFER, self.vbo)

    def unbind(self) -> None:
        ogl.glBindBuffer(ogl.GL_ARRAY_BUFFER, 0)

    def _buffer_data(self) -> None:
        self.bind()
        ogl.glBufferData(
            ogl.GL_ARRAY_BUFFER, len(self.data) * 4, self.data, ogl.GL_STATIC_DRAW
        )

        self.program.use()
        self.program.set_attribute(self.name)

        # If instanced this attribute is split between verticie instances.
        if self.instanced:
            ogl.glVertexAttribDivisor(self.program.get_attribute(self.name), 1)
        self.unbind()


class IndexBuffer:
    def __init__(self, data: list, program, name: str) -> None:
        self.vbo = ogl.glGenBuffers(1)
        self.data = numpy.array(data, dtype="float32")
        self.name = name
        self.program = program
        self._buffer_data()

    def bind(self) -> None:
        ogl.glBindBuffer(ogl.GL_ELEMENT_ARRAY_BUFFER, self.vbo)

    def unbind(self) -> None:
        ogl.glBindBuffer(ogl.GL_ELEMENT_ARRAY_BUFFER, 0)

    def _buffer_data(self) -> None:
        self.bind()
        ogl.glBufferData(
            ogl.GL_ELEMENT_ARRAY_BUFFER,
            len(self.data) * 4,
            self.data,
            ogl.GL_STATIC_DRAW,
        )

        self.program.use()
        self.program.set_attribute(self.name)
        self.unbind()


TRIANGLE_DATA = (
    -0.5,
    -0.5,
    0,
    0.5,
    -0.5,
    0,
    -0.5,
    0.5,
    0,
    0.5,
    0.5,
    0,
    -0.5,
    0.5,
    0,
    0.5,
    -0.5,
    0,
)


TRIANGLE_DATA_LENGTH = len(TRIANGLE_DATA)


class RectangleGroup:
    def __init__(self, program, sprites=[]):
        self.vao = VertexState()
        self.program = program
        self.scale_matrix = pyrr.Matrix44.from_scale([4, 4, 0])

        self.sprites = sprites

        with self.vao:
            VertexBuffer(TRIANGLE_DATA, program, "vp")
            VertexBuffer((0, 0, 1), program, "c")

    def append(self, sprite):
        self.sprites.append(sprite)

    def draw(self):
        self.program.use()
        self.program.set_uniform("scale", self.scale_matrix)

        rects = self.update_rects()

        with self.vao:
            # TODO Update rather than new buffer each time?
            VertexBuffer(rects, self.program, "os", True)
            self.vao.draw_instanced(TRIANGLE_DATA_LENGTH, int(len(rects) / 3))

    def update_rects(self):
        rectangles = []

        for s in self.sprites:
            rectangles.append(s.rect.x)
            rectangles.append(s.rect.y)
            rectangles.append(0.0)

        return rectangles


class Rectangle:
    def __init__(self, program, x, y, w, h, color=[0.0, 0.0, 0.0]) -> None:
        self.program = program
        self.color = color
        self.vao = VertexState()

        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.scale_matrix = pyrr.Matrix44.from_scale([self.w, self.h, 0])

        with self.vao:
            VertexBuffer(TRIANGLE_DATA, program, "vp")
            VertexBuffer(self.color, program, "c")

    def draw(self) -> None:
        self.program.use()
        mat = pyrr.Matrix44.from_translation([self.x, self.y, 0])

        self.program.set_uniform("translation", mat)
        self.program.set_uniform("scale", self.scale_matrix)

        with self.vao:
            self.vao.draw_array(TRIANGLE_DATA_LENGTH)

    def check_collision(self, rect2) -> None:
        if (
            self.x < rect2.x + rect2.w
            and self.x + self.w > rect2.x
            and self.y < rect2.y + rect2.h
            and self.y + self.h > rect2.y
        ):
            return True
        return False
