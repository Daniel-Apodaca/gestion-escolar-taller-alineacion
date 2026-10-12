import sqlite3
import sys
from pathlib import Path


def obtener_ruta_db():
    if getattr(sys, "frozen", False):
        carpeta = Path(sys.executable).resolve().parent
    else:
        carpeta = Path(__file__).resolve().parent

    return carpeta / "escuela.db"


def conectar():
    conexion = sqlite3.connect(obtener_ruta_db())
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def crear_tablas():
    conexion = conectar()

    try:
        conexion.executescript("""
            CREATE TABLE IF NOT EXISTS alumnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT NOT NULL UNIQUE COLLATE NOCASE,
                nombre TEXT NOT NULL,
                campus TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1
                    CHECK (activo IN (0, 1))
            );

            CREATE TABLE IF NOT EXISTS cursos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
                creditos INTEGER NOT NULL CHECK (creditos > 0)
            );

            CREATE TABLE IF NOT EXISTS inscripciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                curso_id INTEGER NOT NULL,
                fecha_inscripcion TEXT NOT NULL,
                UNIQUE (alumno_id, curso_id),
                FOREIGN KEY (alumno_id)
                    REFERENCES alumnos(id) ON DELETE RESTRICT,
                FOREIGN KEY (curso_id)
                    REFERENCES cursos(id) ON DELETE RESTRICT
            );
        """)
        conexion.commit()
    finally:
        conexion.close()