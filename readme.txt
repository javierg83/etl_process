Objetivo:
---------
etl_process: debe de procesar los subdirectorios dentro de "repository" y todos su archivos.
una vez terminado de procesar los archivos de una licitacion, deberia de eliminar la carpeta de la licitacion en repository

sistema de carpetas para aplicaciones:

app_licitacion/frontend		: app para usuario, crea una licitacion y sube archivos.
app_licitacion/backend		: gestiona y crea un subdirectorio de una licitacion dentro del repositorio. usan ID base de datos
app_licitacion/etl_process	: langgraph - procesa la transformacion de los archivos
app_licitacion/repository	: repositorio archivos en subdirectorio donde el nombre es el ID  (LIC-1, LIC-2)
app_licitacion/storage		: repositorio de licitaciones procesadas. subdirectorios ya procesados y sacados de repositoriy



etl_process:
-------------


[GRAFO PRINCIPAL]
nodo inicio -> nodo calculo costos -> nodo procesar archivos -> nodo eliminar subdirectorio

nodo inicio					: revisa el directorio raiz (repository) -> deberia de elegir una licitacion (subdirectorio, ejemplo LIC-1).
							  deberia de copiar los archivos a storage.							  					  
							  
nodo calculo costos			: luego debe ejecutar una funcion de costo (ya creada) y actualizar datos en base datos.

nodo procesar archivos		: por cada archivo ->  ejecucion de un subgrafo (posible trabajo en paralelo a futuro)

nodo eliminar subdirectorio	: si no ha existido errores, borra el subdirectorio de la licitacion en repository y actualiza estado en base de datos




[SUBGRAFO ]
nodo inicio -> nodo revision -> nodo extractor  

nodo inicio		: deberia de normalizar nombre y crear directorio del nombre del archivo.
nodo revision	: deberia de evaluar tipo de archivo (por defecto haremos 1 solo camino por ahora)
nodo extractor	: - convierte cada pagina en imagen (base64) y llama al modelo.
				  - genera json con la informacion  de la pagina y sus elementos.
				  - genera embeddings de cada elemento encontrado
				  - guarda:
						json: un archivo por cada pagina con el resumen de todos sus elementos.
						redis: un documento full de la pagina
						redis: un documento por cada pagina
						redis: un documento por cada elemento de la pagina






consideraciones tecnicas.
-------------------------

ejecucion del sistema "py -m src.main"
arbol directorio propuesto (sugerir nombres o mejoras):
	src (main.py y config.py)
	src.graph.etl
	src.graph.etl.node
	src.graph.document
	src.graph.document.node
	
Cada nodo del grafo tendra un archivo con un metodo estatico llamado execute.
Este metodo execute recibira todos los parametros necesarios para ejecutarse de manera independiente.
Habrá otro método llamado test para probar con datos dummy (opcional).


plantilla de trabajo propuesta con ejemplo (junto con dejar la documentacion del nodo)

considerar que execute atrapa errores de ejecucion y puede devolver diferentes tipos de status para mover el nodo a otro en particular.
funcion _run(state: dict) -> dict:   recibe y devuelve el estate para seguir. aqui va la logica de negocios.

class MyNode:
    """
    StartNode

    RESPONSABILIDAD DEL NODO
    ----------------
    - Detecta licitaciones disponibles en el directorio repository
    - Selecciona una licitación (primer subdirectorio encontrado)
    - Copia los archivos a storage (si no existen previamente)
    - Registra y sincroniza archivos en base de datos SQLite

    BEHAVIOR / INVARIANTS
    --------------------
    - Si repository está vacío:
        state["status"] = "empty"
        → el grafo NO continúa
    - Si ocurre cualquier error:
        state["status"] = "failed"
		→ puede indicar ir a otro nodo
     - Si todo es correcto:
        state["status"] = "ok"
		→ continua el flujo regular

    STATE OUTPUT
    ------------
    - licitation_id
    - storage_case_path
    - status
    - error (opcional)
    """

    @staticmethod
    def execute(state: dict) -> dict:

        try:
            return MyNode._run(state) # funcion del negocio
        except Exception as e:
            state["status"] = "failed"
            state["error_node"] = "start"
            state["error"] = str(e)
            print(f"❌ Error en MyNode: {e}")
            return state

    @staticmethod
    def _run(state: dict) -> dict:
	
		#funciones estilo seudolenguaje para guiar

		#imprime todas las variables de state
        print("📦 State recibido:")
        for k, v in state.items():
            print(f"   - {k}: {v}")

        #para utilizar una variable:
        licitation_id = state.get("licitation_id")