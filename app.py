
import os
import re

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Load private configuration from .env
load_dotenv()

st.set_page_config(
    page_title="Silicon Stories",
    page_icon="🔬",
    layout="centered"
)

# Semiconductor vocabulary
TERMS = {
    "Semiconductor": "A material whose electrical conductivity "
                     "is between that of a conductor and an insulator.",
    "Transistor": "A tiny electronic component that controls "
                  "or switches electrical signals.",
    "Integrated Circuit (IC)": "A collection of electronic "
                               "components built on a small chip.",
    "Silicon Wafer": "A thin slice of silicon used to manufacture chips.",
    "Doping": "Adding small amounts of impurities to change "
              "silicon's electrical properties.",
    "Photolithography": "A process that transfers tiny patterns "
                        "onto a semiconductor wafer.",
    "Diode": "A component that mainly allows current to flow "
             "in one direction.",
    "Microprocessor": "A chip that executes instructions and "
                      "performs computations.",
    "Logic Gate": "A circuit that performs a logical operation.",
    "MOSFET": "A transistor widely used for switching and "
              "amplifying electronic signals.",
    "Fabrication": "The process of manufacturing semiconductor devices.",
    "Integrated Circuit Design": "Planning the electronic components "
                                  "and connections inside a chip."
}

GENRES = [
    "Adventure",
    "Science Fiction",
    "Fantasy",
    "Mystery",
    "Comedy",
    "School Story"
]


def count_words(text):
    """Count words while ignoring Markdown formatting."""
    return len(re.findall(r"\b[\w'-]+\b", text))


def create_demo_story(terms, word_count, genre):
    """Offline demonstration; this is not an LLM-generated story."""
    definitions = [f"{term}: {TERMS[term]}" for term in terms]

    return (
        f"## The {genre} of the Silicon Kingdom\n\n"
        f"In a world of tiny circuits, a young inventor named Mira "
        f"began a remarkable journey. Her mission was to discover how "
        f"modern electronic devices worked and help her community.\n\n"
        f"During her adventure, Mira learned about "
        f"{terms[0]}, which helped her understand the science of "
        f"electronic materials. Next, she explored {terms[1]} "
        f"and discovered how important it was to controlling "
        f"electrical signals. Finally, she investigated {terms[2]} "
        f"and connected her new knowledge to the challenge ahead.\n\n"
        f"With curiosity, teamwork, and careful experiments, Mira "
        f"solved the mystery of the Silicon Kingdom. She realized "
        f"that tiny semiconductor technologies could make a huge "
        f"difference in people's lives.\n\n"
        f"### What we learned\n\n"
        + "\n".join(f"- **{item}** — {TERMS[item]}" for item in terms)
        + "\n\n*Demo story: connect an API key to generate a "
          "new story using AI.*"
    )


def generate_story(terms, word_count, genre):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-5.5")

    if not api_key or api_key == "your_api_key_here":
        return create_demo_story(terms, word_count, genre), True

    client = OpenAI(api_key=api_key)

    definitions = "\n".join(
        f"- {term}: {TERMS[term]}" for term in terms
    )

    prompt = f"""
Create an engaging educational story for young learners.

Genre: {genre}
Target story length: approximately {word_count} words.
Required technical terms: {", ".join(terms)}

Use all three selected terms naturally and accurately.
Explain each term in simple, age-appropriate language.
Use a clear beginning, an interesting challenge, and a satisfying ending.
Use creative characters and vivid descriptions.
Keep the science correct and avoid misleading explanations.
Do not introduce unnecessary advanced technical jargon.

Reference definitions:
{definitions}

After the story, add a short section titled "What We Learned"
explaining the three selected terms in simple language.

Keep the STORY itself close to the requested word count.
The vocabulary section may be additional.
"""

    response = client.responses.create(
        model=model,
        instructions=(
            "You are Silicon Stories, a creative semiconductor "
            "educator who makes technical concepts understandable "
            "and exciting for children."
        ),
        input=prompt
    )

    return response.output_text, False


# ---------------- USER INTERFACE ----------------

st.title("🔬 Silicon Stories")
st.subheader("Where Semiconductor Science Meets Imagination")

st.write(
    "Choose three semiconductor terms, pick your favorite genre, "
    "and create a learning adventure powered by Generative AI!"
)

with st.form("story_form"):
    selected_terms = st.multiselect(
        "Choose exactly 3 semiconductor terms",
        options=list(TERMS.keys()),
        max_selections=3,
        help="Select three different terms."
    )

    genre = st.selectbox(
        "Choose a story genre",
        options=GENRES
    )

    word_count = st.slider(
        "Desired story word count",
        min_value=100,
        max_value=1000,
        value=300,
        step=50
    )

    submitted = st.form_submit_button(
        "✨ Generate My Story",
        use_container_width=True
    )

if submitted:
    if len(selected_terms) != 3:
        st.error("Please select exactly three terms.")
    else:
        try:
            with st.spinner("Creating your silicon adventure..."):
                story, is_demo = generate_story(
                    selected_terms, word_count, genre
                )

            if is_demo:
                st.info(
                    "Demo mode: add your API key to .env "
                    "to generate original AI stories."
                )

            st.markdown("---")
            st.markdown(story)

            st.caption(
                f"Generated text word count: {count_words(story)}. "
                f"Requested story length: about {word_count} words; "
                "the vocabulary section may add extra words."
            )

            st.download_button(
                label="⬇️ Download Story",
                data=story,
                file_name="silicon_story.md",
                mime="text/markdown",
                use_container_width=True
            )

        except Exception as error:
            st.error(
                "The story could not be generated. Check your API "
                "key, model access, internet connection, and API "
                "usage limits, then try again."
            )
            st.caption(f"Technical details: {error}")

st.markdown("---")
st.caption(
    "Silicon Stories | Learn semiconductor science through stories"
)
