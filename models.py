from dataclasses import dataclass


@dataclass
class Alumno:
    matricula: str
    nombre: str
    campus: str
    activo: bool = True
    id: int | None = None


@dataclass
class Curso:
    nombre: str
    creditos: int
    id: int | None = None


@dataclass
class Inscripcion:
    alumno_id: int
    curso_id: int
    fecha_inscripcion: str
    id: int | None = None