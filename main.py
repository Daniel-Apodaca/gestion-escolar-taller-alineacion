import sqlite3
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

import crud
from db import conectar, crear_tablas, obtener_ruta_db
from models import Alumno, Curso, Inscripcion


class Aplicacion:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ids = {"alumno": None, "curso": None, "inscripcion": None}
        self.registros_alumnos = {}
        self.registros_cursos = {}
        self.registros_inscripciones = {}
        self.opciones_alumnos = {}
        self.opciones_cursos = {}

        ventana.title("Control escolar — Alumnos y cursos")
        ventana.geometry("1000x700")
        ventana.minsize(900, 640)
        ventana.configure(bg="#EEF2F6")

        self.configurar_estilos()

        encabezado = tk.Frame(
            ventana, bg="#17324D", padx=20, pady=15
        )
        encabezado.pack(fill="x")

        tk.Label(
            encabezado,
            text="Control escolar",
            bg="#17324D",
            fg="white",
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            encabezado,
            text="Administración de alumnos, cursos e inscripciones",
            bg="#17324D",
            fg="#D7E3EF",
            font=("Segoe UI", 10),
        ).pack(anchor="w")

        contenido = ttk.Frame(ventana, padding=15)
        contenido.pack(fill="both", expand=True)

        pestañas = ttk.Notebook(contenido)
        pestañas.pack(fill="both", expand=True)

        self.panel_alumnos = ttk.Frame(pestañas, padding=15)
        self.panel_cursos = ttk.Frame(pestañas, padding=15)
        self.panel_inscripciones = ttk.Frame(pestañas, padding=15)

        pestañas.add(self.panel_alumnos, text="  Alumnos  ")
        pestañas.add(self.panel_cursos, text="  Cursos  ")
        pestañas.add(self.panel_inscripciones, text="  Inscripciones  ")

        self.crear_alumnos()
        self.crear_cursos()
        self.crear_inscripciones()

        pie = ttk.Frame(contenido)
        pie.pack(fill="x", pady=(10, 0))

        ttk.Label(
            pie,
            text="Selecciona un registro en la tabla para editarlo.",
        ).pack(side="left")

        ttk.Button(
            pie,
            text="Respaldar base de datos",
            command=self.respaldar,
        ).pack(side="right")

        self.refrescar()

    def configurar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(".", font=("Segoe UI", 10))
        estilo.configure("TFrame", background="#EEF2F6")
        estilo.configure(
            "TLabel", background="#EEF2F6", foreground="#24364B"
        )
        estilo.configure(
            "TLabelframe", background="#EEF2F6"
        )
        estilo.configure(
            "TLabelframe.Label",
            background="#EEF2F6",
            foreground="#17324D",
            font=("Segoe UI", 11, "bold"),
        )
        estilo.configure(
            "TCheckbutton", background="#EEF2F6"
        )
        estilo.configure("TButton", padding=(10, 7))
        estilo.configure(
            "Principal.TButton",
            background="#17324D",
            foreground="white",
        )
        estilo.map(
            "Principal.TButton",
            background=[("active", "#285277")],
        )
        estilo.configure("TEntry", padding=5)
        estilo.configure("TNotebook", background="#EEF2F6")
        estilo.configure("TNotebook.Tab", padding=(12, 8))
        estilo.map(
            "TNotebook.Tab",
            background=[("selected", "#17324D")],
            foreground=[("selected", "white")],
        )
        estilo.configure(
            "Treeview", rowheight=30, fieldbackground="white"
        )
        estilo.configure(
            "Treeview.Heading",
            background="#DCE5EF",
            foreground="#17324D",
            font=("Segoe UI", 10, "bold"),
        )
        estilo.map(
            "Treeview",
            background=[("selected", "#17324D")],
            foreground=[("selected", "white")],
        )

    def campo(self, padre, etiqueta, variable, fila):
        ttk.Label(padre, text=etiqueta).grid(
            row=fila, column=0, sticky="w", padx=(0, 12), pady=4
        )
        entrada = ttk.Entry(padre, textvariable=variable)
        entrada.grid(row=fila, column=1, sticky="ew", pady=4)
        return entrada

    def formulario(self, panel, titulo):
        marco = ttk.LabelFrame(panel, text=titulo, padding=12)
        marco.pack(fill="x")
        marco.columnconfigure(1, weight=1)
        return marco

    def botones(self, panel, agregar, actualizar, eliminar, limpiar):
        marco = ttk.Frame(panel)
        marco.pack(fill="x", pady=10)

        for texto, funcion in [
            ("Agregar", agregar),
            ("Actualizar", actualizar),
            ("Eliminar", eliminar),
            ("Limpiar formulario", limpiar),
        ]:
            ttk.Button(
                marco,
                text=texto,
                command=funcion,
                style=(
                    "Principal.TButton"
                    if texto == "Agregar"
                    else "TButton"
                ),
            ).pack(side="left", padx=(0, 8))

    def crear_tabla(self, panel, columnas):
        marco = ttk.Frame(panel)
        marco.pack(fill="both", expand=True)
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(0, weight=1)

        tabla = ttk.Treeview(
            marco,
            columns=[columna[0] for columna in columnas],
            show="headings",
            selectmode="browse",
        )

        for clave, titulo, ancho in columnas:
            tabla.heading(clave, text=titulo)
            tabla.column(clave, width=ancho, minwidth=80)

        vertical = ttk.Scrollbar(
            marco, orient="vertical", command=tabla.yview
        )
        horizontal = ttk.Scrollbar(
            marco, orient="horizontal", command=tabla.xview
        )
        tabla.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )
        tabla.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")

        tabla.tag_configure("par", background="white")
        tabla.tag_configure("impar", background="#F2F6FA")
        return tabla

    def llenar_tabla(self, tabla, filas):
        for elemento in tabla.get_children():
            tabla.delete(elemento)

        for numero, (identificador, valores) in enumerate(filas):
            tabla.insert(
                "",
                "end",
                iid=str(identificador),
                values=valores,
                tags=("par" if numero % 2 == 0 else "impar",),
            )

    def crear_alumnos(self):
        self.matricula = tk.StringVar()
        self.nombre = tk.StringVar()
        self.campus = tk.StringVar()
        self.activo = tk.BooleanVar(value=True)
        self.busqueda = tk.StringVar()

        marco = self.formulario(self.panel_alumnos, "Datos del alumno")
        self.campo(marco, "Matrícula:", self.matricula, 0)
        self.campo(marco, "Nombre completo:", self.nombre, 1)
        self.campo(marco, "Campus:", self.campus, 2)
        ttk.Checkbutton(
            marco, text="Alumno activo", variable=self.activo
        ).grid(row=3, column=1, sticky="w", pady=4)

        self.botones(
            self.panel_alumnos,
            lambda: self.guardar_alumno(False),
            lambda: self.guardar_alumno(True),
            lambda: self.eliminar("alumno"),
            lambda: self.limpiar("alumno"),
        )

        buscador = ttk.Frame(self.panel_alumnos)
        buscador.pack(fill="x", pady=(0, 10))

        ttk.Label(buscador, text="Buscar alumno:").pack(side="left")
        entrada = ttk.Entry(buscador, textvariable=self.busqueda)
        entrada.pack(side="left", fill="x", expand=True, padx=8)
        entrada.bind("<Return>", lambda evento: self.refrescar())

        ttk.Button(
            buscador, text="Buscar", command=self.refrescar
        ).pack(side="left")
        ttk.Button(
            buscador, text="Mostrar todos", command=self.mostrar_alumnos
        ).pack(side="left", padx=(8, 0))

        self.tabla_alumnos = self.crear_tabla(
            self.panel_alumnos,
            [
                ("matricula", "Matrícula", 140),
                ("nombre", "Nombre completo", 330),
                ("campus", "Campus", 220),
                ("estado", "Estado", 110),
            ],
        )
        self.tabla_alumnos.bind(
            "<<TreeviewSelect>>", self.seleccionar_alumno
        )

    def crear_cursos(self):
        self.nombre_curso = tk.StringVar()
        self.creditos = tk.StringVar()

        marco = self.formulario(self.panel_cursos, "Datos del curso")
        self.campo(marco, "Nombre del curso:", self.nombre_curso, 0)
        self.campo(marco, "Créditos:", self.creditos, 1)

        self.botones(
            self.panel_cursos,
            lambda: self.guardar_curso(False),
            lambda: self.guardar_curso(True),
            lambda: self.eliminar("curso"),
            lambda: self.limpiar("curso"),
        )

        self.tabla_cursos = self.crear_tabla(
            self.panel_cursos,
            [
                ("nombre", "Curso", 600),
                ("creditos", "Créditos", 150),
            ],
        )
        self.tabla_cursos.bind(
            "<<TreeviewSelect>>", self.seleccionar_curso
        )

    def crear_inscripciones(self):
        self.alumno_elegido = tk.StringVar()
        self.curso_elegido = tk.StringVar()
        self.fecha = tk.StringVar(value=date.today().isoformat())
        self.filtro_alumno = tk.StringVar(value="Todos")

        marco = self.formulario(
            self.panel_inscripciones, "Datos de la inscripción"
        )

        ttk.Label(marco, text="Alumno:").grid(
            row=0, column=0, sticky="w", padx=(0, 12), pady=4
        )
        self.selector_alumno = ttk.Combobox(
            marco,
            textvariable=self.alumno_elegido,
            state="readonly",
        )
        self.selector_alumno.grid(
            row=0, column=1, sticky="ew", pady=4
        )

        ttk.Label(marco, text="Curso:").grid(
            row=1, column=0, sticky="w", padx=(0, 12), pady=4
        )
        self.selector_curso = ttk.Combobox(
            marco,
            textvariable=self.curso_elegido,
            state="readonly",
        )
        self.selector_curso.grid(
            row=1, column=1, sticky="ew", pady=4
        )
        self.campo(marco, "Fecha (AAAA-MM-DD):", self.fecha, 2)

        self.botones(
            self.panel_inscripciones,
            lambda: self.guardar_inscripcion(False),
            lambda: self.guardar_inscripcion(True),
            lambda: self.eliminar("inscripcion"),
            lambda: self.limpiar("inscripcion"),
        )

        filtros = ttk.Frame(self.panel_inscripciones)
        filtros.pack(fill="x", pady=(0, 10))
        ttk.Label(filtros, text="Inscripciones de:").pack(side="left")

        self.selector_filtro = ttk.Combobox(
            filtros,
            textvariable=self.filtro_alumno,
            state="readonly",
        )
        self.selector_filtro.pack(
            side="left", fill="x", expand=True, padx=8
        )
        self.selector_filtro.bind(
            "<<ComboboxSelected>>",
            lambda evento: self.refrescar(),
        )

        ttk.Button(
            filtros,
            text="Resumen por curso",
            command=self.mostrar_resumen,
        ).pack(side="right")

        self.tabla_inscripciones = self.crear_tabla(
            self.panel_inscripciones,
            [
                ("matricula", "Matrícula", 110),
                ("alumno", "Alumno", 250),
                ("curso", "Curso", 250),
                ("fecha", "Fecha de inscripción", 150),
            ],
        )
        self.tabla_inscripciones.bind(
            "<<TreeviewSelect>>", self.seleccionar_inscripcion
        )

    def refrescar(self):
        try:
            todos = crud.consultar_alumnos()
            alumnos = (
                crud.consultar_alumnos(self.busqueda.get())
                if self.busqueda.get().strip()
                else todos
            )
            cursos = crud.consultar_cursos()

            self.opciones_alumnos = {
                f'{a["matricula"]} — {a["nombre"]}': a["id"]
                for a in todos
            }
            self.opciones_cursos = {
                c["nombre"]: c["id"] for c in cursos
            }

            self.selector_alumno["values"] = list(self.opciones_alumnos)
            self.selector_curso["values"] = list(self.opciones_cursos)
            self.selector_filtro["values"] = [
                "Todos", *self.opciones_alumnos
            ]

            if self.filtro_alumno.get() not in [
                "Todos", *self.opciones_alumnos
            ]:
                self.filtro_alumno.set("Todos")

            alumno_id = self.opciones_alumnos.get(
                self.filtro_alumno.get()
            )
            inscripciones = crud.consultar_inscripciones(alumno_id)

        except sqlite3.Error as error:
            self.error(error)
            return

        for tipo in self.ids:
            self.limpiar(tipo)

        self.registros_alumnos = {str(a["id"]): a for a in alumnos}
        self.registros_cursos = {str(c["id"]): c for c in cursos}
        self.registros_inscripciones = {
            str(i["id"]): i for i in inscripciones
        }

        self.llenar_tabla(
            self.tabla_alumnos,
            [
                (
                    a["id"],
                    (
                        a["matricula"], a["nombre"], a["campus"],
                        "Activo" if a["activo"] else "Inactivo",
                    ),
                )
                for a in alumnos
            ],
        )
        self.llenar_tabla(
            self.tabla_cursos,
            [(c["id"], (c["nombre"], c["creditos"])) for c in cursos],
        )
        self.llenar_tabla(
            self.tabla_inscripciones,
            [
                (
                    i["id"],
                    (
                        i["matricula"], i["alumno"], i["curso"],
                        i["fecha_inscripcion"],
                    ),
                )
                for i in inscripciones
            ],
        )

    def seleccionar_alumno(self, evento=None):
        seleccion = self.tabla_alumnos.selection()
        if not seleccion:
            return
        alumno = self.registros_alumnos.get(seleccion[0])
        if alumno is None:
            return

        self.ids["alumno"] = alumno["id"]
        self.matricula.set(alumno["matricula"])
        self.nombre.set(alumno["nombre"])
        self.campus.set(alumno["campus"])
        self.activo.set(bool(alumno["activo"]))

    def seleccionar_curso(self, evento=None):
        seleccion = self.tabla_cursos.selection()
        if not seleccion:
            return
        curso = self.registros_cursos.get(seleccion[0])
        if curso is None:
            return

        self.ids["curso"] = curso["id"]
        self.nombre_curso.set(curso["nombre"])
        self.creditos.set(str(curso["creditos"]))

    def seleccionar_inscripcion(self, evento=None):
        seleccion = self.tabla_inscripciones.selection()
        if not seleccion:
            return
        inscripcion = self.registros_inscripciones.get(seleccion[0])
        if inscripcion is None:
            return

        self.ids["inscripcion"] = inscripcion["id"]

        for etiqueta, identificador in self.opciones_alumnos.items():
            if identificador == inscripcion["alumno_id"]:
                self.alumno_elegido.set(etiqueta)
                break

        for etiqueta, identificador in self.opciones_cursos.items():
            if identificador == inscripcion["curso_id"]:
                self.curso_elegido.set(etiqueta)
                break

        self.fecha.set(inscripcion["fecha_inscripcion"])

    def limpiar(self, tipo):
        self.ids[tipo] = None

        if tipo == "alumno":
            self.matricula.set("")
            self.nombre.set("")
            self.campus.set("")
            self.activo.set(True)
            tabla = self.tabla_alumnos
        elif tipo == "curso":
            self.nombre_curso.set("")
            self.creditos.set("")
            tabla = self.tabla_cursos
        else:
            self.alumno_elegido.set("")
            self.curso_elegido.set("")
            self.fecha.set(date.today().isoformat())
            tabla = self.tabla_inscripciones

        seleccion = tabla.selection()
        if seleccion:
            tabla.selection_remove(*seleccion)

    def requiere_seleccion(self, tipo):
        if self.ids[tipo] is None:
            messagebox.showwarning(
                "Selecciona un registro",
                "Primero selecciona una fila en la tabla.",
                parent=self.ventana,
            )
            return False
        return True

    def guardar_alumno(self, actualizar):
        if actualizar and not self.requiere_seleccion("alumno"):
            return

        matricula = self.matricula.get().strip().upper()
        nombre = self.nombre.get().strip()
        campus = self.campus.get().strip()

        if not all((matricula, nombre, campus)):
            self.aviso("Completa matrícula, nombre y campus.")
            return

        if len(matricula) > 30 or len(nombre) > 120 or len(campus) > 80:
            self.aviso(
                "Máximo: matrícula 30, nombre 120 y campus 80 caracteres."
            )
            return

        alumno = Alumno(
            matricula, nombre, campus, self.activo.get(),
            self.ids["alumno"] if actualizar else None,
        )

        funcion = (
            crud.actualizar_alumno if actualizar else crud.agregar_alumno
        )
        self.operacion(
            lambda: funcion(alumno),
            "Los datos del alumno se guardaron.",
            "Ya existe un alumno con esa matrícula.",
        )

    def guardar_curso(self, actualizar):
        if actualizar and not self.requiere_seleccion("curso"):
            return

        nombre = self.nombre_curso.get().strip()

        if not nombre or len(nombre) > 120:
            self.aviso("Escribe un nombre de curso de hasta 120 caracteres.")
            return

        try:
            creditos = int(self.creditos.get())
            if not 1 <= creditos <= 100:
                raise ValueError
        except ValueError:
            self.aviso("Los créditos deben ser un entero entre 1 y 100.")
            return

        curso = Curso(
            nombre, creditos,
            self.ids["curso"] if actualizar else None,
        )
        funcion = (
            crud.actualizar_curso if actualizar else crud.agregar_curso
        )
        self.operacion(
            lambda: funcion(curso),
            "Los datos del curso se guardaron.",
            "Ya existe un curso con ese nombre.",
        )

    def guardar_inscripcion(self, actualizar):
        if actualizar and not self.requiere_seleccion("inscripcion"):
            return

        alumno_id = self.opciones_alumnos.get(self.alumno_elegido.get())
        curso_id = self.opciones_cursos.get(self.curso_elegido.get())

        if alumno_id is None or curso_id is None:
            self.aviso("Selecciona un alumno y un curso.")
            return

        fecha = self.fecha.get().strip()
        try:
            fecha_validada = date.fromisoformat(fecha)
            if fecha_validada.isoformat() != fecha:
                raise ValueError
        except ValueError:
            self.aviso("Usa una fecha válida con formato AAAA-MM-DD.")
            return

        inscripcion = Inscripcion(
            alumno_id, curso_id, fecha,
            self.ids["inscripcion"] if actualizar else None,
        )
        funcion = (
            crud.actualizar_inscripcion
            if actualizar
            else crud.agregar_inscripcion
        )
        self.operacion(
            lambda: funcion(inscripcion),
            "La inscripción se guardó.",
            "El alumno ya está inscrito en ese curso, "
            "o el alumno/curso ya no existe.",
        )

    def eliminar(self, tipo):
        if not self.requiere_seleccion(tipo):
            return

        if not messagebox.askyesno(
            "Confirmar eliminación",
            "¿Eliminar el registro seleccionado?\n"
            "Esta acción no se puede deshacer.",
            parent=self.ventana,
        ):
            return

        funciones = {
            "alumno": crud.eliminar_alumno,
            "curso": crud.eliminar_curso,
            "inscripcion": crud.eliminar_inscripcion,
        }
        identificador = self.ids[tipo]

        self.operacion(
            lambda: funciones[tipo](identificador),
            "El registro se eliminó.",
            "No puedes eliminar un alumno o curso con inscripciones. "
            "Cancela primero sus inscripciones. Para conservar el "
            "historial de un alumno, puedes marcarlo como inactivo.",
        )

    def operacion(self, funcion, mensaje, mensaje_integridad):
        try:
            resultado = funcion()
        except sqlite3.IntegrityError:
            self.aviso(mensaje_integridad)
            return
        except sqlite3.Error as error:
            self.error(error)
            return

        self.refrescar()

        if resultado == 0:
            self.aviso("El registro ya no existe. La tabla se actualizó.")
            return

        messagebox.showinfo(
            "Operación completada", mensaje, parent=self.ventana
        )

    def mostrar_alumnos(self):
        self.busqueda.set("")
        self.refrescar()

    def mostrar_resumen(self):
        try:
            filas = crud.resumen_por_curso()
        except sqlite3.Error as error:
            self.error(error)
            return

        resumen = tk.Toplevel(self.ventana)
        resumen.title("Resumen de inscripciones por curso")
        resumen.geometry("520x350")
        resumen.transient(self.ventana)

        marco = ttk.Frame(resumen, padding=15)
        marco.pack(fill="both", expand=True)

        ttk.Label(
            marco,
            text="Número de alumnos inscritos en cada curso",
        ).pack(anchor="w", pady=(0, 10))

        tabla = self.crear_tabla(
            marco,
            [("curso", "Curso", 330), ("total", "Inscritos", 110)],
        )
        self.llenar_tabla(
            tabla,
            [
                (numero, (fila["nombre"], fila["total"]))
                for numero, fila in enumerate(filas)
            ],
        )

    def respaldar(self):
        destino = filedialog.asksaveasfilename(
            parent=self.ventana,
            title="Guardar respaldo",
            defaultextension=".db",
            initialfile=f"respaldo_escuela_{date.today().isoformat()}.db",
            filetypes=[("Base de datos SQLite", "*.db")],
        )
        if not destino:
            return

        from pathlib import Path

        if Path(destino).resolve() == obtener_ruta_db().resolve():
            self.aviso("El respaldo debe tener una ruta distinta a escuela.db.")
            return

        origen = None
        copia = None

        try:
            origen = conectar()
            copia = sqlite3.connect(destino)
            origen.backup(copia)
        except (sqlite3.Error, OSError) as error:
            self.error(error)
            return
        finally:
            if copia is not None:
                copia.close()
            if origen is not None:
                origen.close()

        messagebox.showinfo(
            "Respaldo creado",
            "La copia de seguridad se guardó correctamente.",
            parent=self.ventana,
        )

    def aviso(self, mensaje):
        messagebox.showwarning(
            "Revisa los datos", mensaje, parent=self.ventana
        )

    def error(self, error):
        messagebox.showerror(
            "Error",
            f"No se pudo completar la operación:\n{error}",
            parent=self.ventana,
        )


def main():
    ventana = tk.Tk()
    ventana.withdraw()

    try:
        crear_tablas()
        Aplicacion(ventana)
    except sqlite3.Error as error:
        messagebox.showerror(
            "Error al iniciar",
            f"No se pudo preparar la aplicación:\n{error}",
            parent=ventana,
        )
        ventana.destroy()
        return

    ventana.deiconify()
    ventana.mainloop()


if __name__ == "__main__":
    main()