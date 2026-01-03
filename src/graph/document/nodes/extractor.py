# src/graph/document/nodes/extractor.py
import fitz  # PyMuPDF
import base64
import json
import os

from .extractor_impl.ai_extractor_pdf import analyze_page_with_gpt as analizar_pagina
from .extractor_impl.embeddings import generar_embedding
from .extractor_impl.redis_utils import guardar_en_redis
import redis
from src.config import REDIS_URL

class DocumentExtractorNode:

    redis_client = redis.Redis.from_url(REDIS_URL)

    @staticmethod
    def execute(state: dict) -> dict:
        try:

            return DocumentExtractorNode._run(state)
        except Exception as e:
            state["status"] = "failed"
            state["error_node"] = "document_start"
            state["error"] = str(e)
            print(f"❌ Error en DocumentStartNode: {e}")
            return state
        
    @staticmethod
    def _run(state: dict) -> dict:

        print("📦 State recibido DocumentExtractorNode:")
        for k, v in state.items():
            print(f"   - {k}: {v}")

        document_filename = state.get("document_filename") 
        document_path = state.get("document_path")          # directorio trabajo
        document_id = state.get("document_id")              # directorio trabajo
        document_folder = state.get("document_folder")      # directorio trabajo   
        #os.makedirs(document_folder, exist_ok=True)         

        resultados = DocumentExtractorNode.extraer_data(document_id,document_path)

        try:
            print(f"[guardar_archivos] → Guardando JSON en {document_id}_resultado_paginas.json")
            DocumentExtractorNode.guardar_resultados(resultados, document_folder, nombre_base=document_id)

            # Guardar también un JSON por cada página (requerido por run_embedding_batch)
            for pagina in resultados:
                num_pagina = pagina.get("pagina", "desconocida")
                archivo_pagina = os.path.join(document_folder, f"{document_id}_pag_{num_pagina}.json")
                with open(archivo_pagina, "w", encoding="utf-8") as f:
                    json.dump(pagina, f, ensure_ascii=False, indent=2)
                print(f"[📄] Archivo de página guardado: {archivo_pagina}")

        except Exception as e:
            print(f"[❌ ERROR] Error durante guardado de resultados: {e}")

        print(f"[embedding] 🧠 Iniciando embedding para {len(resultados)} páginas")

        texto_documento = ""
        for pagina in resultados:
            num_pagina = pagina["pagina"]
            print(f"[embedding] → Procesando página {num_pagina}")
            contenido_pagina = ""
            key_base = f"doc_raw_page:{document_id}:p{num_pagina}"

            elementos = pagina.get("elementos", [])
            print(f"[embedding]   • Elementos detectados: {len(elementos)}")

            if not elementos:
                print(f"⚠️ Página {num_pagina} no contiene elementos, se omite")
                continue

            for idx, elem in enumerate(elementos):
                texto = str(elem.get("contenido", "")).strip()
                print(f"[embedding]     • Elem {idx+1}: '{texto[:50]}'... (len={len(texto)})")

                if not texto:
                    continue

                try:
                    emb = generar_embedding(texto)
                    key_elem = f"{key_base}_e{idx+1}"
                    DocumentExtractorNode.redis_client.hset(key_elem, mapping={
                        "pagina": str(num_pagina),
                        "elemento": str(idx+1),
                        "texto": texto,
                        "embedding": json.dumps(emb)
                    })
                    contenido_pagina += texto + "\n"
                except Exception as e:
                    print(f"[❌ error] Fallo embedding en p{num_pagina}_e{idx+1}: {e}")
                    DocumentExtractorNode.registrar_error_reproceso(document_id, num_pagina, idx+1)

            if contenido_pagina.strip():
                try:
                    emb_pagina = generar_embedding(contenido_pagina)
                    DocumentExtractorNode.redis_client.hset(key_base, mapping={
                        "pagina": str(num_pagina),
                        "texto": contenido_pagina.strip(),
                        "embedding": json.dumps(emb_pagina)
                    })
                    texto_documento += contenido_pagina + "\n"
                    print(f"[embedding] ✅ Página {num_pagina} embebida")
                except Exception as e:
                    print(f"[❌ error] Fallo embedding página {num_pagina}: {e}")
                    DocumentExtractorNode.registrar_error_reproceso(document_id, num_pagina)

        if False:
            if texto_documento.strip():
                try:
                    emb_doc = generar_embedding(texto_documento)
                    DocumentExtractorNode.redis_client.hset(f"doc_raw:{nombre_sin_extension}", mapping={
                        "nombre_original": nombre_archivo,
                        "document_id": nombre_sin_extension,
                        "texto": texto_documento.strip(),
                        "embedding": json.dumps(emb_doc),
                        "pages_count": len(resultados),
                        "filename": nombre_archivo,
                        "timestamp": datetime.now().isoformat()
                    })
                    print("[embedding] ✅ Embedding de documento completo generado")
                except Exception as e:
                    print(f"[❌ error] Fallo embedding documento completo: {e}")
                    registrar_error_reproceso(nombre_sin_extension, -1)

            print("[embedding] ➕ Ejecutando refuerzo batch embedding con run_embedding_batch()")
            run_embedding_batch(nombre_sin_extension)

            return len(resultados)

    @staticmethod
    def registrar_error_reproceso(document_id, pagina, elemento=None):
        carpeta = os.path.join("archivos_texto", document_id)
        os.makedirs(carpeta, exist_ok=True)

        archivo_log = os.path.join(carpeta, "log_errores.txt")
        with open(archivo_log, "a", encoding="utf-8") as f:
            if elemento:
                f.write(f"{document_id}:p{pagina}_e{elemento}\n")
            elif pagina == -1:
                f.write(f"{document_id}:DOCUMENTO\n")
            else:
                f.write(f"{document_id}:p{pagina}\n")

    @staticmethod
    def guardar_resultados(resultados, document_folder, nombre_base="documento"):
        json_path = os.path.join(document_folder, f"{nombre_base}_resultado_paginas.json")
        txt_path = os.path.join(document_folder, f"{nombre_base}.txt")
        token_path = os.path.join(document_folder, f"{nombre_base}_tokens.txt")

        with open(json_path, "w", encoding="utf-8") as f_json, \
            open(txt_path, "w", encoding="utf-8") as f_txt, \
            open(token_path, "w", encoding="utf-8") as f_tok:

            total_tokens = 0
            for pagina in resultados:
                num_pagina = pagina["pagina"]
                elementos = pagina.get("elementos", [])

                f_txt.write(f"=== PÁGINA {num_pagina} ===\n")
                for elem in elementos:
                    t = elem.get("tipo")
                    if t == "titulo":
                        f_txt.write(f"\n# {elem.get('contenido', '').strip()}\n")
                    elif t == "texto":
                        f_txt.write(elem.get("contenido", "").strip() + "\n")
                    elif t == "checkbox":
                        f_txt.write("☑️ " + elem.get("contenido", "").strip() + "\n")
                    elif t == "tabla":
                        contenido = elem.get("contenido", [])
                        if isinstance(contenido, list):
                            for row in contenido:
                                if isinstance(row, list):
                                    f_txt.write("|".join(str(c) for c in row) + "\n")
                                else:
                                    f_txt.write(str(row) + "\n")
                        else:
                            f_txt.write(str(contenido) + "\n")

                    tokens = elem.get("tokens", 0)
                    total_tokens += tokens

                f_txt.write("\n\n")

            f_tok.write(f"Total tokens: {total_tokens}\n")

        print(f"[guardar_archivos] → Guardando JSON en {os.path.basename(json_path)}")
        print(f"[guardar_archivos] → Guardando texto plano en {os.path.basename(txt_path)}")
        print(f"[guardar_archivos] → Guardando tokens en {os.path.basename(token_path)}")
        print("[guardar_archivos] ✅ Archivos guardados correctamente")



    @staticmethod
    def extraer_data(document_id,document_path):

        resultados = []
        with fitz.open(document_path) as doc:
            total_paginas = doc.page_count

            indices = list(range(total_paginas))
            print(f"[process_pages] → PDF tiene {total_paginas} páginas. Leyendo indices: {indices}")

            for i in indices:
                print(f"=== process_pages → Procesando {i + 1}/{total_paginas} (página real {i + 1}) ===")

                try:
                    print(f"[Extractor] ({i + 1}) → Iniciando análisis de página {i + 1} de '{document_path}'")
                    elementos, raw, tokens_in, tokens_out = analizar_pagina(document_path, i)

                    resultado = {
                        "pagina": i + 1,
                        "elementos": elementos,
                        "tokens_in": tokens_in,
                        "tokens_out": tokens_out,
                        "raw": raw
                    }
                    resultados.append(resultado)

                    for idx, elem in enumerate(elementos):
                        texto = str(elem.get("contenido", "")).strip()
                        if texto:
                            emb = generar_embedding(texto)
                            if emb:
                                clave = f"doc_raw_page:{document_id}:p{i+1}_e{idx+1}"
                                guardar_en_redis(clave, {
                                    "embedding": json.dumps(emb),
                                    "texto": texto,
                                    "pagina": i + 1,
                                    "tipo": elem.get("tipo", "")
                                })

                    texto_pagina = "\n".join(
                        str(e.get("contenido", "")) for e in elementos if isinstance(e.get("contenido", ""), str)
                    )
                    if texto_pagina.strip():
                        emb_pagina = generar_embedding(texto_pagina.strip())
                        if emb_pagina:
                            clave = f"doc_raw_page:{document_id}:p{i+1}_full"
                            guardar_en_redis(clave, {
                                "embedding": json.dumps(emb_pagina),
                                "texto": texto_pagina.strip(),
                                "pagina": i + 1,
                                "tipo": "pagina"
                            })
                except Exception as e:
                    print(f"[❌ ERROR] No se pudo procesar página {i + 1}: {e}")

        print("[process_pages] ✅ Finalizado.")
        return resultados
                    

    @staticmethod
    def test():
        test_state = {

            "document_path": "D:/sodimac/storage/LIC-001/1-Bases_5300-44-L125__19.pdf",
            "document_folder": "D:/sodimac/storage/LIC-001/1_bases_5300_44_l125__19",
            "document_filename": "1-Bases_5300-44-L125__19.pdf",
            "document_id":"1_bases_5300_44_l125__19"
        }

        result = DocumentExtractorNode.execute(test_state)

if __name__ == "__main__":

    DocumentExtractorNode.test()        