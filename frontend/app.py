"""Give It A Summary — Streamlit UI."""

import base64
from pathlib import Path

import requests
import streamlit as st

API_URL = "http://api:8000/api/v1"

st.set_page_config(
    page_title="Give It A Summary",
    page_icon="📄",
    layout="centered",
)


with st.sidebar:
    st.title("⚙️ Options")

    style = st.selectbox(
        "Summary Style",
        ["concise", "detailed", "bullets"],
        help=(
            "**concise** — brief overview (1–2 paragraphs)\n\n"
            "**detailed** — comprehensive coverage (3–5 paragraphs)\n\n"
            "**bullets** — key points as a bulleted list"
        ),
    )

    word_count = st.slider(
        "Max Words",
        min_value=100,
        max_value=1000,
        value=250,
        step=50,
        help="Target maximum word count for the summary.",
    )

    email = st.text_input(
        "Email (optional)",
        placeholder="you@example.com",
        help="Receive the Word document in your inbox. Leave blank to skip.",
    )

    st.divider()
    st.subheader("🔧 Service Status")
    if st.button("Check", use_container_width=True):
        try:
            r = requests.get(f"{API_URL}/health", timeout=5)
            if r.ok:
                data = r.json()
                st.success("Backend: ✅ Healthy")
                for m in data.get("Available Ollama Models", []):
                    if "error" not in m:
                        st.info(f"🤖 {m['name']} ({m['size_gb']} GB)")
                    else:
                        st.warning(f"⚠️ Ollama: {m['error']}")
            else:
                st.error(f"Backend returned {r.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Backend unreachable")
        except requests.exceptions.Timeout:
            st.error("❌ Health check timed out")


st.title("📄 Give It A Summary")
st.caption(
    "AI-powered academic paper summarization. Upload a document, get a clear summary instantly."
)
st.markdown("---")

uploaded_file = st.file_uploader(
    "Drop your document here",
    type=["pdf", "docx", "txt", "xlsx", "xls", "csv"],
    help="Supported: PDF, Word (.docx), Plain text, Excel (.xlsx/.xls), CSV",
)

if uploaded_file:
    size_kb = len(uploaded_file.getvalue()) / 1024
    st.info(f"📎 **{uploaded_file.name}** — {size_kb:.1f} KB")

    if st.button("🚀 Summarize", type="primary", use_container_width=True):
        with st.spinner(
            "Extracting text and generating summary… this may take a minute."
        ):
            try:
                response = requests.post(
                    f"{API_URL}/summarize",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream",
                        )
                    },
                    data={
                        "style": style,
                        "word_count": str(word_count),
                        "email": email.strip() if email else "",
                    },
                    timeout=300,
                )

                if response.ok:
                    data = response.json()
                    if data["success"]:
                        st.success("✅ Summary ready!")
                        st.markdown("---")
                        st.subheader("📝 Summary")

                        summary_text = data.get("summary", "")
                        if style == "bullets":
                            st.markdown(summary_text)
                        else:
                            st.write(summary_text)

                        st.markdown("---")

                        if data.get("summary_docx_b64"):
                            docx_bytes = base64.b64decode(data["summary_docx_b64"])
                            stem = Path(uploaded_file.name).stem
                            st.download_button(
                                label="⬇️ Download Word Document",
                                data=docx_bytes,
                                file_name=f"{stem}_summary.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True,
                            )

                        if data.get("email_sent"):
                            st.info(f"📧 Word document emailed to **{email.strip()}**")
                        elif email and email.strip() and not data.get("email_sent"):
                            st.warning(
                                "⚠️ Email could not be sent. "
                                "SMTP may not be configured on the server."
                            )
                    else:
                        st.error(
                            f"❌ {data.get('message', 'An unknown error occurred.')}"
                        )
                else:
                    st.error(
                        f"❌ Server error ({response.status_code}): "
                        f"{response.json().get('detail', response.text)[:300]}"
                    )

            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ Cannot connect to the backend. Is the API service running?"
                )
            except requests.exceptions.Timeout:
                st.error(
                    "❌ Request timed out. The document may be very large, "
                    "or the Ollama model is still loading."
                )
            except Exception as e:  # noqa: BLE001
                st.error(f"❌ Unexpected error: {e}")

else:
    st.markdown(
        """
        #### How it works
        1. **Upload** a PDF, Word doc, plain text file, spreadsheet, or CSV above.
        2. **Configure** summary style and length in the sidebar.
        3. Click **Summarize** — the AI will extract and condense the content.
        4. **Download** a professionally formatted Word document, or have it emailed to you.
        """
    )
