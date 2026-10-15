"""RAG application using Mistral AI, Pinecone, and Streamlit."""

import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from pinecone import Pinecone
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from streamlit.errors import StreamlitSecretNotFoundError
from typing import List

load_dotenv()

PINECONE_HOST      = "https://pineconeagents-anpvcrc.svc.aped-4627-b74a.pinecone.io"
PINECONE_NAMESPACE = "RAG"


def get_config_value(key: str) -> str | None:
    value = os.getenv(key)
    if value:
        return value
    try:
        return st.secrets.get(key)
    except StreamlitSecretNotFoundError:
        return None


PROMPT_TEMPLATE = (
    "Use the following context to answer the question.\n"
    "If you don't know the answer from the context, say \"I don't have enough information to answer that.\"\n"
    "\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:"
)

PAGE_STYLE = """
<style>
html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }

[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0f1117 0%, #1a1f2e 100%);
    border-right: 1px solid #2d3748;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] p { color: #e2e8f0 !important; }

[data-testid="stAppViewContainer"] > .main { background: #0f1117; }

.hero-box {
    background: linear-gradient(135deg, #1e3a5f 0%, #0d2137 60%, #1a1040 100%);
    border: 1px solid #2d4a6e; border-radius: 16px;
    padding: 2rem 2.5rem; margin-bottom: 1.5rem;
}
.hero-box h1 {
    font-size: 2.4rem; font-weight: 800;
    background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 0.4rem 0;
}
.hero-box p { color: #94a3b8; font-size: 1rem; margin: 0; }

.status-ready {
    background: linear-gradient(90deg, #064e3b, #065f46);
    border: 1px solid #10b981; border-radius: 12px;
    padding: 1rem 1.5rem; margin-bottom: 1.2rem;
    display: flex; align-items: center; gap: 0.75rem;
}
.status-ready .icon { font-size: 1.6rem; }
.status-ready .text { color: #d1fae5; }
.status-ready .text strong { color: #6ee7b7; font-size: 1.05rem; }
.status-ready .text span   { font-size: 0.85rem; color: #a7f3d0; }

.status-idle {
    background: linear-gradient(90deg, #1e1b4b, #312e81);
    border: 1px solid #6366f1; border-radius: 12px;
    padding: 1rem 1.5rem; margin-bottom: 1.2rem;
    display: flex; align-items: center; gap: 0.75rem;
}
.status-idle .icon { font-size: 1.6rem; }
.status-idle .text { color: #c7d2fe; }
.status-idle .text strong { color: #a5b4fc; font-size: 1.05rem; }
.status-idle .text span   { font-size: 0.85rem; color: #818cf8; }

[data-testid="stSidebar"] .stButton > button {
    width: 100%; background: linear-gradient(90deg, #3b82f6, #6366f1);
    color: white; border: none; border-radius: 10px;
    padding: 0.6rem 1rem; font-weight: 600; font-size: 0.95rem;
    cursor: pointer; transition: opacity 0.2s;
}
[data-testid="stSidebar"] .stButton > button:hover { opacity: 0.85; }

[data-testid="stChatMessage"] {
    background: #1a1f2e; border: 1px solid #2d3748;
    border-radius: 12px; margin-bottom: 0.6rem;
}
[data-testid="stChatInput"]  { background: #1a1f2e; border: 1px solid #3b82f6; border-radius: 12px; }
[data-testid="stExpander"]   { background: #161b27; border: 1px solid #2d3748; border-radius: 10px; }

.sidebar-divider { border: none; border-top: 1px solid #2d3748; margin: 1rem 0; }

.doc-card {
    background: #1a2235; border: 1px solid #2d4a6e;
    border-radius: 10px; padding: 0.75rem 1rem; margin-top: 0.5rem;
}
.doc-card p { color: #94a3b8; font-size: 0.82rem; margin: 0.15rem 0; }
.doc-card strong { color: #60a5fa; }

.tip-box { background: #1e1b4b; border-left: 3px solid #818cf8; border-radius: 6px; padding: 0.6rem 0.9rem; margin-top: 0.8rem; }
.tip-box p { color: #c7d2fe; font-size: 0.8rem; margin: 0; }
</style>
"""


# ── Pinecone custom retriever ─────────────────────────────────────────────────
class PineconeRetriever(BaseRetriever):
    index: object
    pc: object
    namespace: str
    k: int = 4

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun  # noqa: ARG002
    ) -> List[Document]:
        query_vec = embed_texts(self.pc, [query], input_type="query")[0]
        results = self.index.query(
            vector=query_vec,
            top_k=self.k,
            namespace=self.namespace,
            include_metadata=True,
        )
        docs = []
        for match in results.get("matches", []):
            meta = match.get("metadata", {})
            text = meta.pop("text", "")
            docs.append(Document(page_content=text, metadata=meta))
        return docs


# ── Helpers ───────────────────────────────────────────────────────────────────
def embed_texts(pc: Pinecone, texts: List[str], input_type: str = "passage") -> List[List[float]]:
    result = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=texts,
        parameters={"input_type": input_type, "truncate": "END"},
    )
    return [r.values for r in result]


def get_llm():
    return ChatMistralAI(
        model="mistral-large-latest",
        api_key=get_config_value("MISTRAL_API_KEY"),
        temperature=0.2,
    )


def load_and_split(file_path: str, url: str):
    loader = PyPDFLoader(file_path) if file_path else WebBaseLoader(url)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    return splitter.split_documents(docs)


def build_vectorstore(chunks):
    pc    = Pinecone(api_key=get_config_value("PINECONE_API_KEY"))
    index = pc.Index(host=PINECONE_HOST)

    # Clear existing RAG namespace before indexing new document
    try:
        index.delete(delete_all=True, namespace=PINECONE_NAMESPACE)
    except Exception:
        pass  # namespace auto-created on first upsert

    # Embed with llama-text-embed-v2 via Pinecone inference and upsert
    texts  = [c.page_content for c in chunks]
    batch_size = 50  # keep batches small for inference API
    for i in range(0, len(texts), batch_size):
        batch_texts  = texts[i:i+batch_size]
        batch_chunks = chunks[i:i+batch_size]
        vectors      = embed_texts(pc, batch_texts, input_type="passage")
        to_upsert    = [
            (str(uuid.uuid4()), vec, {"text": text, **chunk.metadata})
            for text, vec, chunk in zip(batch_texts, vectors, batch_chunks)
        ]
        index.upsert(vectors=to_upsert, namespace=PINECONE_NAMESPACE)

    return PineconeRetriever(index=index, pc=pc, namespace=PINECONE_NAMESPACE, k=4)


def build_qa_chain(retriever):
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"],
    )
    return RetrievalQA.from_chain_type(
        llm=get_llm(),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )


# ── Streamlit UI ──────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="DocChat AI", page_icon="📄", layout="wide")
    st.markdown(PAGE_STYLE, unsafe_allow_html=True)

    if not get_config_value("MISTRAL_API_KEY"):
        st.error(
            "MISTRAL_API_KEY not found. Add it to your local .env file or "
            "Streamlit Cloud app settings under Secrets."
        )
        st.stop()
    if not get_config_value("PINECONE_API_KEY"):
        st.error(
            "PINECONE_API_KEY not found. Add it to your local .env file or "
            "Streamlit Cloud app settings under Secrets."
        )
        st.stop()

    for k, v in {"retriever": None, "messages": [], "doc_name": None, "doc_chunks": 0}.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Sidebar ───────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 📄 DocChat AI")
        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)
        st.markdown("### Load a Document")

        uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"], label_visibility="collapsed")
        st.caption("Supports any PDF — reports, books, research papers")
        st.markdown("<div style='margin:0.5rem 0;color:#64748b;font-size:0.8rem;text-align:center'>— or —</div>", unsafe_allow_html=True)
        url_input = st.text_input("Paste a webpage URL", placeholder="https://example.com/article")

        col1, col2 = st.columns(2)
        with col1: process_btn = st.button("Process", use_container_width=True)
        with col2: clear_btn   = st.button("Clear Chat", use_container_width=True)

        if process_btn:
            with st.spinner("Chunking → Embedding → Indexing to Pinecone…"):
                try:
                    chunks = source_name = None
                    if uploaded_file:
                        tmp_path = f"/tmp/{uploaded_file.name}"
                        with open(tmp_path, "wb") as f:
                            f.write(uploaded_file.read())
                        source_name = uploaded_file.name
                        chunks = load_and_split(file_path=tmp_path, url="")
                    elif url_input:
                        source_name = url_input
                        chunks = load_and_split(file_path="", url=url_input)
                    else:
                        st.warning("Please upload a PDF or enter a URL first.")

                    if chunks:
                        st.session_state.retriever  = build_vectorstore(chunks)
                        st.session_state.messages   = []
                        st.session_state.doc_name   = source_name
                        st.session_state.doc_chunks = len(chunks)
                        st.rerun()
                    elif chunks is not None:
                        st.warning("No content found in the document.")
                except Exception as e:
                    st.error(f"{type(e).__name__}: {e}")

        if clear_btn:
            st.session_state.messages = []
            st.rerun()

        if st.session_state.retriever is not None:
            st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)
            st.markdown("### Loaded Document")
            st.markdown(f"""
            <div class='doc-card'>
                <p>📎 <strong>{st.session_state.doc_name or 'Document'}</strong></p>
                <p>🧩 <strong>{st.session_state.doc_chunks}</strong> chunks indexed</p>
                <p>🗄️ Vector DB: <strong>Pinecone</strong> · namespace <strong>RAG</strong></p>
                <p>🧠 Embeddings: <strong>llama-text-embed-v2</strong> (Pinecone inference)</p>
                <p>🤖 LLM: <strong>Mistral Large</strong></p>
                <p>🔍 Retrieval: top <strong>4</strong> chunks</p>
            </div>""", unsafe_allow_html=True)
            st.markdown("""
            <div class='tip-box'>
                <p>💡 <strong>Tips:</strong> Ask specific questions, request summaries, or ask for key takeaways.</p>
            </div>""", unsafe_allow_html=True)

    # ── Main area ─────────────────────────────────────────────
    st.markdown("""
    <div class='hero-box'>
        <h1>DocChat AI</h1>
        <p>Upload a PDF or paste a URL — then ask anything about it. Powered by Mistral AI + Pinecone RAG.</p>
    </div>""", unsafe_allow_html=True)

    if st.session_state.retriever is not None:
        st.markdown(f"""
        <div class='status-ready'>
            <div class='icon'>✅</div>
            <div class='text'>
                <strong>Document loaded successfully!</strong><br>
                <span>Chatting with: <strong style='color:#6ee7b7'>"{st.session_state.doc_name}"</strong>
                &nbsp;·&nbsp; {st.session_state.doc_chunks} chunks
                &nbsp;·&nbsp; Pinecone namespace: <strong>RAG</strong></span>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='status-idle'>
            <div class='icon'>💬</div>
            <div class='text'>
                <strong>No document loaded yet</strong><br>
                <span>Upload a PDF or paste a URL in the sidebar, then click Process to begin.</span>
            </div>
        </div>""", unsafe_allow_html=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    placeholder = (
        "Ask anything about your document..."
        if st.session_state.retriever
        else "Load a document first to start chatting..."
    )
    question = st.chat_input(placeholder)

    if question:
        if st.session_state.retriever is None:
            st.warning("Please load a document first using the sidebar.")
        else:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    try:
                        qa_chain = build_qa_chain(st.session_state.retriever)
                        result   = qa_chain.invoke({"query": question})
                        answer   = result.get("result", "")
                        sources  = result.get("source_documents", [])

                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})

                        if sources:
                            with st.expander("View Sources"):
                                for i, doc in enumerate(sources, 1):
                                    page = doc.metadata.get("page", "?")
                                    st.markdown(f"**Chunk {i}** (page {page})")
                                    st.caption(doc.page_content[:300] + "...")
                                    if i < len(sources):
                                        st.divider()
                    except Exception as e:
                        st.error(f"Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
