"""Give It A Summary — Streamlit UI."""

import base64
from pathlib import Path

import requests
import streamlit as st

API_URL = "http://backend:8000/api/v1"

st.set_page_config(
    page_title="Give It A Summary",
    page_icon="📄",
    layout="centered",
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_file" not in st.session_state:
    st.session_state.pending_file = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

st.markdown(
    """
    <style>
    /* Give the attachment bar a card-like look */
    .attach-bar {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 6px 12px;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.85rem;
        color: #444;
    }
    /* Shrink the default file uploader drop zone */
    [data-testid="stFileUploader"] section {
        padding: 0.4rem 0.6rem;
        min-height: unset;
    }
    [data-testid="stFileUploader"] section > div {
        gap: 0.3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("⚙️ Options")

    email = st.text_input(
        "Email (optional)",
        placeholder="you@example.com",
        help=(
            "Attach your email here or mention it in your message "
            "(e.g. 'send to me@example.com'). Leave blank to skip."
        ),
    )

    st.divider()
    st.subheader("Service Status")
    if st.button("Check", use_container_width=True):
        try:
            r = requests.get(f"{API_URL}/health", timeout=10)
            if r.ok:
                data = r.json()
                st.success("Backend is Healthy")
                for m in data.get("Available Ollama Models", []):
                    if "error" not in m:
                        st.info(f"{m['name']} ({m['size_gb']} GB)")
                    else:
                        st.warning(f"Ollama: {m['error']}")
            else:
                st.error(f"Backend returned {r.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("Backend unreachable")
        except requests.exceptions.Timeout:
            st.error("Health check timed out")

st.title("📄 Give It A Summary")
st.caption("Attach a document and tell me how to summarize it.")
st.markdown("---")

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "Hello! Attach a document below and tell me what you need — for example:\n\n"
            "> *Summarize this paper in bullet points, max 300 words*\n\n"
            "> *Give me a detailed overview of the methodology section*\n\n"
            "Supported formats: PDF, Word (.docx), plain text, Excel, CSV."
        )
else:
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("docx_b64"):
                st.download_button(
                    label="⬇️ Download Word Document",
                    data=base64.b64decode(msg["docx_b64"]),
                    file_name=msg.get("docx_filename", "summary.docx"),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key=f"dl_{idx}",
                )
            if msg.get("email_info"):
                st.info(msg["email_info"])

uploaded_file = st.file_uploader(
    "📎 Attach a document",
    type=["pdf", "docx", "txt", "xlsx", "xls", "csv"],
    label_visibility="collapsed",
    key=f"uploader_{st.session_state.uploader_key}",
    help="PDF, Word, plain text, Excel or CSV",
)

if uploaded_file is not None:
    st.session_state.pending_file = uploaded_file

if st.session_state.pending_file:
    pf = st.session_state.pending_file
    size_kb = len(pf.getvalue()) / 1024
    st.markdown(
        f'<div class="attach-bar">📄 <strong>{pf.name}</strong> &nbsp;·&nbsp; {size_kb:.1f} KB</div>',
        unsafe_allow_html=True,
    )

prompt = st.chat_input(
    "Ask anything — e.g. 'Summarize in bullets under 400 words'",
    disabled=st.session_state.pending_file is None,
)

if st.session_state.pending_file is None:
    st.caption("⬆️ Attach a document first, then type your instruction.")

if prompt and st.session_state.pending_file:
    pf = st.session_state.pending_file
    instruction = prompt.strip()

    st.session_state.messages.append(
        {"role": "user", "content": f"📎 **{pf.name}** — {instruction}"}
    )

    with st.spinner("Reading document and generating summary…"):
        try:
            response = requests.post(
                f"{API_URL}/summarize",
                files={
                    "file": (
                        pf.name,
                        pf.getvalue(),
                        pf.type or "application/octet-stream",
                    )
                },
                data={
                    "user_instruction": instruction,
                    "email": email.strip() if email else "",
                },
                timeout=600,
            )

            if response.ok:
                data = response.json()
                if data["success"]:
                    assistant_msg: dict = {
                        "role": "assistant",
                        "content": data.get("summary", ""),
                    }

                    if data.get("summary_docx_b64"):
                        stem = Path(pf.name).stem
                        assistant_msg["docx_b64"] = data["summary_docx_b64"]
                        assistant_msg["docx_filename"] = f"{stem}_summary.docx"

                    detected = data.get("detected_email") or email.strip()
                    if data.get("email_sent"):
                        source = (
                            " (from your message)"
                            if data.get("detected_email") and not email.strip()
                            else ""
                        )
                        assistant_msg["email_info"] = (
                            f"📧 Word document emailed to **{detected}**{source}"
                        )
                    elif detected and not data.get("email_sent"):
                        assistant_msg["email_info"] = (
                            f"Email to **{detected}** could not be sent. "
                            "SMTP may not be configured on the server."
                        )

                    st.session_state.messages.append(assistant_msg)
                else:
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f" {data.get('message', 'An unknown error occurred.')}",
                        }
                    )
            else:
                detail = ""
                try:
                    detail = response.json().get("detail", response.text)[:300]
                except Exception:  # noqa: BLE001
                    detail = response.text[:300]
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f" Server error ({response.status_code}): {detail}",
                    }
                )

        except requests.exceptions.ConnectionError:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": " Cannot connect to the backend. Is the API service running?",
                }
            )
        except requests.exceptions.Timeout:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        " Request timed out. The document may be very large "
                        "or the Ollama model is still loading."
                    ),
                }
            )
        except Exception as e:  # noqa: BLE001
            st.session_state.messages.append(
                {"role": "assistant", "content": f" Unexpected error: {e}"}
            )

    st.session_state.pending_file = None
    st.session_state.uploader_key += 1
    st.rerun()
