
import re

import requests
import streamlit as st

# ---------------- CONFIGURATION ----------------

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

st.set_page_config(
    page_title="Silicon Stories",
    page_icon="🔬",
    layout="centered",
)

# ---------------- SEMICONDUCTOR VOCABULARY ----------------

TERMS = {
    "Semiconductor": (
        "A material whose electrical conductivity is "
        "between that of a conductor and an insulator."
    ),
    "Transistor": (
        "A tiny electronic component that controls "
        "or switches electrical signals."
    ),
    "Integrated Circuit (IC)": (
        "A collection of electronic components built on a small chip."
    ),
    "Silicon Wafer": (
        "A thin slice of silicon used to manufacture chips."
    ),
    "Doping": (
        "Adding small amounts of impurities to change "
        "silicon's electrical properties."
    ),
    "Photolithography": (
        "A process that transfers tiny patterns onto a semiconductor wafer."
    ),
    "Diode": (
        "A component that mainly allows current to flow in one direction."
    ),
    "Microprocessor": (
        "A chip that executes instructions and performs computations."
    ),
    "Logic Gate": (
        "A circuit that performs a logical operation."
    ),
    "MOSFET": (
        "A transistor widely used for switching and amplifying signals."
    ),
    "Fabrication": (
        "The process of manufacturing semiconductor devices."
    ),
    "Integrated Circuit Design": (
        "Planning the electronic components and connections inside a chip."
    ),
}

GENRES = [
    "Adventure",
    "Science Fiction",
    "Fantasy",
    "Mystery",
    "Comedy",
    "School Story",
]


# ---------------- HELPER FUNCTIONS ----------------

def count_words(text):
    """Count words while ignoring Markdown formatting."""
    return len(re.findall(r"\b[\w'-]+\b", text))


def generate_story(terms, word_count, genre):
    """Generate a semiconductor story using a local Ollama model."""

    definitions = "\n".join(
        f"- {term}: {TERMS[term]}"
        for term in terms
    )

    prompt = f"""
You are Silicon Stories, a creative semiconductor educator
who makes technical concepts exciting and understandable
for young learners.

Write an original educational story with these requirements:

Genre: {genre}
Target STORY length: approximately {word_count} words.
Required semiconductor terms: {", ".join(terms)}

Instructions:
1. Use all three selected terms naturally in the story.
2. Explain their scientific meanings accurately and simply.
3. Include a clear beginning, an interesting challenge,
   and a satisfying ending.
4. Use engaging characters, imagination, and vivid descriptions.
5. Keep the language suitable for young learners.
6. Avoid unnecessary technical jargon and scientific errors.
7. Keep the main story close to the requested word count.
8. After the story, add a section titled "What We Learned".
9. In that section, explain each of the three terms using
   the definitions supplied below.
10. Do not claim that a real experiment or event occurred
    unless it is part of the fictional story.

Reference definitions:
{definitions}

Return the story in Markdown.
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=(10, 300),
        )
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure Ollama is installed "
            "and running on this computer."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            "Ollama took too long to respond. Try again or use a "
            "smaller model."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"Could not contact Ollama: {exc}"
        ) from exc

    if response.status_code == 404:
        raise RuntimeError(
            f"Model '{MODEL}' was not found. Run "
            f"'ollama pull {MODEL}' in your terminal."
        )

    if not response.ok:
        raise RuntimeError(
            f"Ollama returned HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Ollama returned an invalid response."
        ) from exc

    story = result.get("response", "").strip()

    if not story:
        raise RuntimeError(
            "Ollama returned an empty story. Please try again."
        )

    return story


# ---------------- USER INTERFACE ----------------

st.title("🔬 Silicon Stories")
st.subheader("Where Semiconductor Science Meets Imagination")

st.write(
    "Choose three semiconductor terms, pick your favorite genre, "
    "and create an educational adventure powered by local AI."
)

with st.form("story_form"):
    selected_terms = st.multiselect(
        "Choose exactly 3 semiconductor terms",
        options=list(TERMS.keys()),
        max_selections=3,
        help="Select three different terms.",
    )

    genre = st.selectbox(
        "Choose a story genre",
        options=GENRES,
    )

    word_count = st.slider(
        "Desired story word count",
        min_value=100,
        max_value=1000,
        value=300,
        step=50,
    )

    submitted = st.form_submit_button(
        "✨ Generate My Story",
        use_container_width=True,
    )


if submitted:
    if len(selected_terms) != 3:
        st.error("Please select exactly three terms.")
    else:
        try:
            with st.spinner(
                f"Generating your story with {MODEL}..."
            ):
                story = generate_story(
                    selected_terms,
                    word_count,
                    genre,
                )

            st.success("Your story has been generated locally!")

            st.markdown("---")
            st.markdown(story)

            st.caption(
                f"Generated text word count: {count_words(story)}. "
                f"Requested story length: about {word_count} words. "
                "The learning section may add extra words."
            )

            st.download_button(
                label="⬇️ Download Story",
                data=story,
                file_name="silicon_story.md",
                mime="text/markdown",
                use_container_width=True,
            )

        except RuntimeError as error:
            st.error(str(error))
        except Exception as error:
            st.error("An unexpected error occurred.")
            st.caption(f"Technical details: {error}")


st.markdown("---")
st.caption(
    "Silicon Stories | Learn semiconductor science through stories"
)
