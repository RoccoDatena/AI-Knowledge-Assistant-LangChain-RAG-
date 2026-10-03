"""Portfolio-oriented Streamlit user interface."""

import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from frontend.api_client import ApiClient, ApiClientError

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def render_sources(sources: list[dict[str, Any]]) -> None:
    """Render backend-generated citations."""

    if not sources:
        return
    with st.expander("Fonti utilizzate"):
        for source in sources:
            st.markdown(
                f"- **{source['filename']}**, pagina {source['page_number']} "
                f"(rilevanza: {source['score']:.2f})"
            )


def render_grounding_status(grounded: bool) -> None:
    """Show whether the latest answer was supported by retrieved evidence."""

    if grounded:
        st.badge(
            "Risposta grounded",
            icon=":material/check_circle:",
            color="green",
        )
    else:
        st.badge(
            "Informazione non trovata",
            icon=":material/info:",
            color="orange",
        )


def render_document_panel(client: ApiClient) -> None:
    """Render document management controls."""

    st.sidebar.subheader("Knowledge base")
    uploaded_file = st.sidebar.file_uploader("Carica un PDF", type=["pdf"])
    if uploaded_file is not None and st.sidebar.button("Salva documento"):
        content = uploaded_file.getvalue()
        if len(content) > MAX_UPLOAD_BYTES:
            st.sidebar.error("Il PDF supera il limite di 10 MB.")
        else:
            try:
                with st.sidebar.spinner("Salvataggio PDF..."):
                    result = client.upload_document(uploaded_file.name, content)
                st.sidebar.success(f"Caricato: {result['filename']}")
            except ApiClientError as exc:
                st.sidebar.error(f"Upload non riuscito [{exc.code}]: {exc}")
            except Exception as exc:
                st.sidebar.error(f"Upload non riuscito: {exc}")

    if st.sidebar.button("Indicizza documenti"):
        try:
            with st.sidebar.spinner("Indicizzazione in corso..."):
                result = client.index_documents()
            st.sidebar.success(f"Chunk indicizzati: {result['chunks_indexed']}")
        except ApiClientError as exc:
            st.sidebar.error(f"Indicizzazione non riuscita [{exc.code}]: {exc}")
        except Exception as exc:
            st.sidebar.error(f"Indicizzazione non riuscita: {exc}")

    try:
        documents = client.list_documents()
        st.sidebar.caption(f"Documenti: {len(documents)}")
        for document in documents:
            columns = st.sidebar.columns([4, 1])
            columns[0].write(document["filename"])
            if columns[1].button("×", key=f"delete-{document['document_id']}"):
                try:
                    with st.sidebar.spinner("Eliminazione..."):
                        client.delete_document(document["document_id"])
                    st.rerun()
                except ApiClientError as exc:
                    st.sidebar.error(f"Eliminazione non riuscita [{exc.code}]: {exc}")
    except ApiClientError as exc:
        st.sidebar.warning(f"Backend non disponibile [{exc.code}]: {exc}")
    except Exception as exc:
        st.sidebar.warning(f"Backend non disponibile: {exc}")


def render_conversation_controls(client: ApiClient) -> None:
    """Render controls for starting a fresh conversation session."""

    st.sidebar.subheader("Conversazione")
    if st.sidebar.button("Nuova conversazione"):
        try:
            conversation = client.create_conversation()
            st.session_state.conversation_id = conversation["conversation_id"]
            st.rerun()
        except ApiClientError as exc:
            st.sidebar.error(f"Impossibile creare la conversazione [{exc.code}]")
        except Exception as exc:
            st.sidebar.error(f"Impossibile creare la conversazione: {exc}")


def render_search_panel(client: ApiClient) -> None:
    """Render an optional semantic search panel with metadata filters."""

    st.sidebar.divider()
    st.sidebar.subheader("Ricerca semantica")
    query = st.sidebar.text_input("Query di ricerca", key="search-query")
    try:
        documents = client.list_documents()
        document_options = {"Tutti i documenti": None}
        document_options.update(
            {document["filename"]: document["document_id"] for document in documents}
        )
        selected_filename = st.sidebar.selectbox(
            "Documento",
            options=list(document_options),
            key="search-document",
        )
        page_number = st.sidebar.number_input(
            "Pagina (0 = tutte)", min_value=0, value=0, step=1, key="search-page"
        )
        if st.sidebar.button("Cerca chunk", disabled=not query.strip()):
            results = client.search_documents(
                query=query,
                document_id=document_options[selected_filename],
                page_number=page_number or None,
            )
            if not results:
                st.sidebar.info("Nessun chunk rilevante trovato.")
            for result in results:
                st.sidebar.caption(
                    f"{result['chunk_id']} · pagina {result['page_number']} · "
                    f"score {result['score']:.2f}"
                )
                st.sidebar.write(result["content"])
    except ApiClientError as exc:
        st.sidebar.warning(f"Ricerca non disponibile [{exc.code}]: {exc}")
    except Exception as exc:
        st.sidebar.warning(f"Ricerca non disponibile: {exc}")


def main() -> None:
    """Render the application."""

    st.set_page_config(
        page_title="AI Knowledge Assistant", page_icon="📚", layout="wide"
    )
    st.markdown(
        """
        <style>
        .block-container { max-width: 1100px; padding-top: 2rem; }
        [data-testid="stSidebar"] { border-right: 1px solid #e5e7eb; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("AI Knowledge Assistant")
    st.caption("Chat grounded sui tuoi documenti, con fonti verificabili.")

    client = ApiClient(API_BASE_URL)
    if "conversation_id" not in st.session_state:
        try:
            with st.spinner("Connessione al backend..."):
                conversation = client.create_conversation()
            st.session_state.conversation_id = conversation["conversation_id"]
        except ApiClientError as exc:
            st.error(f"Backend non disponibile [{exc.code}]: {exc}")
            return
        except Exception as exc:
            st.error(f"Backend non disponibile: {exc}")
            return

    render_conversation_controls(client)
    render_document_panel(client)
    render_search_panel(client)
    try:
        history = client.get_history(st.session_state.conversation_id)
        for message in history["messages"]:
            is_assistant = message["role"] == "assistant"
            with st.chat_message("assistant" if is_assistant else "user"):
                st.markdown(message["content"])
                if is_assistant and message.get("grounded") is not None:
                    render_grounding_status(message["grounded"])
                    render_sources(message.get("sources", []))
    except ApiClientError as exc:
        st.error(f"Impossibile caricare la conversazione [{exc.code}]: {exc}")
    except Exception as exc:
        st.error(f"Impossibile caricare la conversazione: {exc}")

    if question := st.chat_input("Fai una domanda sui documenti..."):
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Analizzo i documenti..."):
                try:
                    result = client.send_message(
                        st.session_state.conversation_id, question
                    )
                    st.markdown(result["assistant_message"]["content"])
                    render_grounding_status(result.get("grounded", False))
                    render_sources(result.get("sources", []))
                except ApiClientError as exc:
                    st.error(f"Risposta non disponibile [{exc.code}]: {exc}")
                except Exception as exc:
                    st.error(f"Risposta non disponibile: {exc}")


if __name__ == "__main__":
    main()
