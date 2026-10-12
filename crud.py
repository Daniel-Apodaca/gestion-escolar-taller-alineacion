from db import conectar


def ejecutar(sql, parametros=(), consulta=False):
    conexion = conectar()

    try:
        cursor = conexion.execute(sql, parametros)

        if consulta:
            return cursor.fetchall()

        conexion.commit()
        return cursor.rowcount
    finally:
        conexion.close()


def consultar_alumnos(busqueda=""):
    patron = f"%{busqueda.strip()}%"
    return ejecutar(
        """
        SELECT id, matricula, nombre, campus, activo
        FROM alumnos
        WHERE matricula LIKE ? OR nombre LIKE ? OR campus LIKE ?
        ORDER BY nombre COLLATE NOCASE
        """,
        (patron, patron, patron),
        consulta=True,
    )


def agregar_alumno(alumno):
    return ejecutar(
        """
        INSERT INTO alumnos (matricula, nombre, campus, activo)
        VALUES (?, ?, ?, ?)
        """,
        (
            alumno.matricula,
            alumno.nombre,
            alumno.campus,
            int(alumno.activo),
        ),
    )


def actualizar_alumno(alumno):
    return ejecutar(
        """
        UPDATE alumnos
        SET matricula = ?, nombre = ?, campus = ?, activo = ?
        WHERE id = ?
        """,
        (
            alumno.matricula,
            alumno.nombre,
            alumno.campus,
            int(alumno.activo),
            alumno.id,
        ),
    )


def eliminar_alumno(alumno_id):
    return ejecutar(
        "DELETE FROM alumnos WHERE id = ?",
        (alumno_id,),
    )


def consultar_cursos():
    return ejecutar(
        "SELECT id, nombre, creditos FROM cursos ORDER BY nombre",
        consulta=True,
    )


def agregar_curso(curso):
    return ejecutar(
        "INSERT INTO cursos (nombre, creditos) VALUES (?, ?)",
        (curso.nombre, curso.creditos),
    )


def actualizar_curso(curso):
    return ejecutar(
        "UPDATE cursos SET nombre = ?, creditos = ? WHERE id = ?",
        (curso.nombre, curso.creditos, curso.id),
    )


def eliminar_curso(curso_id):
    return ejecutar(
        "DELETE FROM cursos WHERE id = ?",
        (curso_id,),
    )


def consultar_inscripciones(alumno_id=None):
    sql = """
        SELECT i.id, i.alumno_id, i.curso_id,
               a.matricula, a.nombre AS alumno,
               c.nombre AS curso, i.fecha_inscripcion
        FROM inscripciones i
        JOIN alumnos a ON a.id = i.alumno_id
        JOIN cursos c ON c.id = i.curso_id
    """
    parametros = ()

    if alumno_id is not None:
        sql += " WHERE i.alumno_id = ?"
        parametros = (alumno_id,)

    sql += " ORDER BY a.nombre, c.nombre"
    return ejecutar(sql, parametros, consulta=True)


def agregar_inscripcion(inscripcion):
    return ejecutar(
        """
        INSERT INTO inscripciones
            (alumno_id, curso_id, fecha_inscripcion)
        VALUES (?, ?, ?)
        """,
        (
            inscripcion.alumno_id,
            inscripcion.curso_id,
            inscripcion.fecha_inscripcion,
        ),
    )


def actualizar_inscripcion(inscripcion):
    return ejecutar(
        """
        UPDATE inscripciones
        SET alumno_id = ?, curso_id = ?, fecha_inscripcion = ?
        WHERE id = ?
        """,
        (
            inscripcion.alumno_id,
            inscripcion.curso_id,
            inscripcion.fecha_inscripcion,
            inscripcion.id,
        ),
    )


def eliminar_inscripcion(inscripcion_id):
    return ejecutar(
        "DELETE FROM inscripciones WHERE id = ?",
        (inscripcion_id,),
    )


def resumen_por_curso():
    return ejecutar(
        """
        SELECT c.nombre, COUNT(i.id) AS total
        FROM cursos c
        LEFT JOIN inscripciones i ON i.curso_id = c.id
        GROUP BY c.id, c.nombre
        ORDER BY c.nombre
        """,
        consulta=True,
    )