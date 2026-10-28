import json
import re
import requests
import streamlit as st

from database import (
    save_story,
    get_all_stories,
    get_story,
    delete_story,
    clear_history,
)


# -----------------------------
# Configuration
# -----------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

TERMS = [
    "Semiconductor",
    "Silicon",
    "Transistor",
    "Diode",
    "Integrated Circuit",
    "Microprocessor",
    "Photolithography",
    "Doping",
    "PN Junction",
    "Wafer",
    "MOSFET",
    "Clean Room",
]

GENRES = [
    "Adventure",
    "Science Fiction",
    "Mystery",
    "Fantasy",
    "Comedy",
    "Educational",
]


# -----------------------------
# Page configuration
# Must be the first Streamlit command.
# -----------------------------
st.set_page_config(
    page_title="Silicon Stories",
    page_icon="🔬",
    layout="wide",
)


# -----------------------------
# Professional UI styling
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f3f7fc 0%, #ffffff 48%);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #142d4e;
        letter-spacing: -0.4px;
    }

    p, label, .stMarkdown {
        line-height: 1.65;
    }

    section[data-testid="stSidebar"] {
        background: #10243e;
    }

    section[data-testid="stSidebar"] * {
        color: #f1f5fb;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #172b45;
    }

    section[data-testid="stSidebar"] input {
        color: #172b45;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 600;
        border: 1px solid #d5dfeb;
        transition: all 0.2s ease;
    }

    .stButton > button[kind="primary"] {
        background: #1769aa;
        color:white;
        border: none;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: #1769aa;
        transform: translateY(-1px);
    }

    [data-baseweb="select"],
    [data-baseweb="input"] {
        border-radius: 9px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px;
        border-color: #dce5f0;
        box-shadow: 0 3px 12px rgba(25, 55, 90, 0.04);
    }

    button[data-baseweb="tab"] {
        font-weight: 600;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #1769aa;
    }

    hr {
        border-color: #dce5f0;
    }

    .app-footer {
        text-align: center;
        color: #64748b;
        font-size: 0.85rem;
        padding: 22px 0;
    }

    @media (max-width: 700px) {
        .block-container {
            padding: 1rem 1rem 2rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Helper functions
# -----------------------------
def extract_title(story):
    """Use the first non-empty line as the story title."""
    for line in story.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:200]
    return "Untitled Silicon Story"


def count_words(text):
    """Count words in a story."""
    return len(re.findall(r"\b[\w'-]+\b", text))


# -----------------------------
# Ollama helper
# -----------------------------
def ask_ollama(prompt):
    """Send a prompt to the local Ollama model."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    except requests.exceptions.ConnectionError:
        st.error(
            "Cannot connect to Ollama. If it is not already running, "
            "open a terminal and run: ollama serve"
        )
    except requests.exceptions.Timeout:
        st.error("The model took too long to respond. Try a shorter story.")
    except requests.exceptions.RequestException as error:
        st.error(f"Ollama request failed: {error}")
    except (ValueError, AttributeError):
        st.error("Ollama returned an invalid response.")

    return None


# -----------------------------
# Story generation
# -----------------------------
def generate_story(terms, word_count, genre, age_group):
    prompt = f"""
You are an engaging semiconductor science educator and storyteller.

Write an original {genre} story for {age_group} learners.

Required semiconductor concepts:
{", ".join(terms)}

Requirements:
1. Target approximately {word_count} words.
2. Use all three selected terms naturally.
3. Explain each technical term correctly in context.
4. Keep the language appropriate for the learners.
5. Give the story a suitable title.
6. Make the story entertaining and educational.
7. Avoid claiming that fictional events are real science.
8. Output only the title and story.

Target word count: {word_count}.
"""
    return ask_ollama(prompt)


# -----------------------------
# Glossary generation
# -----------------------------
def generate_glossary(terms):
    prompt = f"""
Explain these semiconductor terms for young learners:
{", ".join(terms)}

For each term, provide:
- Term name
- A simple definition in 1-2 sentences
- One everyday analogy

Use accurate science. Return clear, readable text with one section
for each term.
"""
    return ask_ollama(prompt)


# -----------------------------
# Quiz generation
# -----------------------------
def generate_quiz(story):
    prompt = f"""
Create exactly five multiple-choice questions based on this story.

For each question, provide four options labelled A, B, C, and D,
and identify the correct answer.

Return ONLY valid JSON in this format:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": {{
        "A": "Option one",
        "B": "Option two",
        "C": "Option three",
        "D": "Option four"
      }},
      "answer": "A",
      "explanation": "Why this answer is correct"
    }}
  ]
}}

Make questions educational and scientifically accurate.
The answer must be one of A, B, C, or D.

STORY:
{story}
"""
    raw = ask_ollama(prompt)
    if not raw:
        return None

    # Extract JSON if the model adds code fences or extra text.
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None

    try:
        data = json.loads(raw[start:end + 1])
        questions = data.get("questions", [])

        if not isinstance(questions, list) or len(questions) != 5:
            return None

        for question in questions:
            if not isinstance(question, dict):
                return None
            options = question.get("options")
            if (
                not isinstance(options, dict)
                or question.get("answer") not in ["A", "B", "C", "D"]
                or not all(key in options for key in ["A", "B", "C", "D"])
            ):
                return None

        return questions

    except (json.JSONDecodeError, AttributeError, TypeError):
        return None


# -----------------------------
# Header and hero section
# -----------------------------
st.markdown(
    """
    # 🔬 Silicon Stories

    ### Discover the world of semiconductors through storytelling.

    Turn complex semiconductor concepts into engaging stories,
    simple explanations, and interactive quizzes using local AI.
    """
)

st.markdown(
    """
    <div style="
        background: linear-gradient(120deg, #10243e, #1769aa);
        padding: 22px 25px;
        border-radius: 16px;
        color: white;
        margin: 12px 0 25px 0;
    ">
        <div style="font-size: 13px; opacity: 0.85;">
            YOUR PERSONAL SEMICONDUCTOR LEARNING STUDIO
        </div>
        <div style="font-size: 23px; font-weight: 700; margin-top: 7px;">
            Learn science. Explore stories. Test your knowledge.
        </div>
        <div style="font-size: 14px; margin-top: 8px;">
            Powered by Ollama and Llama 3.2
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

metric1, metric2, metric3 = st.columns(3)
with metric1:
    st.metric("AI Engine", "Llama 3.2")
with metric2:
    st.metric("Story Mode", "Creative Learning")
with metric3:
    st.metric("Generation", "Local AI")


# -----------------------------
# Sidebar story settings
# -----------------------------
with st.sidebar:
    st.markdown("## 🔬 Silicon Stories")
    st.caption("YOUR LEARNING WORKSPACE")
    st.divider()
    st.markdown("### ⚙️ Story Configuration")

    selected_terms = st.multiselect(
        "Choose exactly three semiconductor terms",
        options=TERMS,
        max_selections=3,
        help="Choose three concepts to include in your story.",
    )

    genre = st.selectbox("Choose a genre", GENRES)

    word_count = st.slider(
        "Target story length (words)",
        min_value=100,
        max_value=1000,
        value=300,
        step=50,
    )

    age_group = st.selectbox(
        "Target audience",
        [
            "school students",
            "middle-school students",
            "high-school students",
            "beginner engineering students",
        ],
    )

    generate_button = st.button(
        "✨ Generate My Story",
        type="primary",
        use_container_width=True,
    )


# -----------------------------
# Generate and save a new story
# -----------------------------
if generate_button:
    if len(selected_terms) != 3:
        st.warning("Please select exactly three semiconductor terms.")
    else:
        with st.spinner("Your AI story is being created..."):
            generated_story = generate_story(
                selected_terms, word_count, genre, age_group
            )

        if generated_story:
            try:
                story_id = save_story(
                    title=extract_title(generated_story),
                    content=generated_story,
                    terms=selected_terms,
                    genre=genre,
                    target_words=word_count,
                )

                st.session_state["story"] = generated_story
                st.session_state["terms"] = selected_terms
                st.session_state["genre"] = genre
                st.session_state["target_words"] = word_count
                st.session_state["current_story_id"] = story_id

                # Clear results belonging to the previous story.
                for key in ("glossary", "quiz", "quiz_answers", "quiz_score"):
                    st.session_state.pop(key, None)

                st.success("Story generated and saved to your history!")
            except Exception as error:
                st.error(f"The story was generated, but could not be saved: {error}")
                # Keep the generated story available in the current session.
                st.session_state["story"] = generated_story
                st.session_state["terms"] = selected_terms
                st.session_state["genre"] = genre
                st.session_state["target_words"] = word_count


# -----------------------------
# Current story, glossary and quiz
# -----------------------------
if st.session_state.get("story"):
    story = st.session_state["story"]
    terms = st.session_state.get("terms", [])

    st.divider()
    st.markdown("## 📖 Your Learning Story")
    st.caption(
        f"Genre: {st.session_state.get('genre', 'Unknown')} · "
        f"Target: {st.session_state.get('target_words', 0)} words · "
        f"Actual: {count_words(story)} words"
    )

    with st.container(border=True):
        st.markdown(story)
        st.download_button(
            "⬇️ Download Story",
            data=story,
            file_name="silicon_story.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_current_story",
        )

    tab_glossary, tab_quiz = st.tabs(
        ["📚 Semiconductor Glossary", "🧠 Story Quiz"]
    )

    with tab_glossary:
        st.write(
            "Learn the scientific concepts used in your generated story."
        )

        if st.button("Generate Glossary", key="make_glossary"):
            with st.spinner("Creating simple explanations..."):
                result = generate_glossary(terms)

            if result:
                st.session_state["glossary"] = result

        if st.session_state.get("glossary"):
            st.markdown(st.session_state["glossary"])

    with tab_quiz:
        st.write(
            "Test what you learned by answering five questions "
            "about your story."
        )

        if st.button("Generate Quiz", key="make_quiz"):
            with st.spinner("Creating quiz questions..."):
                questions = generate_quiz(story)

            if questions:
                st.session_state["quiz"] = questions
                st.session_state.pop("quiz_answers", None)
                st.session_state.pop("quiz_score", None)
            else:
                st.error(
                    "The model did not return a valid five-question quiz. "
                    "Please try again."
                )

        questions = st.session_state.get("quiz")
        if questions:
            with st.form("quiz_form"):
                answers = {}

                for i, question in enumerate(questions):
                    st.markdown(
                        f"**{i + 1}. {question['question']}**"
                    )

                    options = question["options"]
                    labels = [
                        f"{letter}. {options[letter]}"
                        for letter in ["A", "B", "C", "D"]
                    ]

                    answers[i] = st.radio(
                        "Select your answer",
                        labels,
                        index=None,
                        key=f"question_{i}",
                        label_visibility="collapsed",
                    )

                submitted = st.form_submit_button("Check My Answers")

            if submitted:
                score = 0
                for i, question in enumerate(questions):
                    chosen = answers[i]
                    correct = question["answer"]
                    if chosen and chosen.startswith(correct + "."):
                        score += 1

                st.session_state["quiz_answers"] = answers
                st.session_state["quiz_score"] = score

            if "quiz_score" in st.session_state:
                st.metric(
                    "Your Score",
                    f"{st.session_state['quiz_score']} / 5",
                )

                for i, question in enumerate(questions):
                    chosen = st.session_state["quiz_answers"].get(i)
                    correct = question["answer"]
                    options = question["options"]

                    if chosen and chosen.startswith(correct + "."):
                        st.success(f"Question {i + 1}: Correct!")
                    else:
                        st.info(
                            f"Question {i + 1}: Correct answer — "
                            f"{correct}. {options[correct]}"
                        )

                    st.caption(question.get("explanation", ""))
else:
    st.info(
        "Choose three terms, a genre, and a word count in the sidebar "
        "to create your first story."
    )


# -----------------------------
# Persistent story history
# -----------------------------
st.divider()
st.markdown("## 📚 Your Story Library")
st.caption("Revisit, download, or manage stories saved on this device.")

saved_stories = get_all_stories()

if not saved_stories:
    st.info("No saved stories yet. Generate your first story!")
else:
    st.write(f"Total saved stories: {len(saved_stories)}")

    choices = {
        f"#{item['id']} — {item['title']} ({item['created_at'][:10]})":
        item["id"]
        for item in saved_stories
    }

    selected_label = st.selectbox(
        "Choose a story to revisit",
        options=list(choices.keys()),
        key="history_selection",
    )

    selected_id = choices[selected_label]
    previous_story = get_story(selected_id)

    if previous_story:
        st.subheader(previous_story["title"])
        st.caption(
            f"Genre: {previous_story['genre']} | "
            f"Terms: {previous_story['terms']} | "
            f"Target: {previous_story['target_words']} words"
        )

        st.markdown(previous_story["content"])

        st.download_button(
            "⬇️ Download Previous Story",
            data=previous_story["content"],
            file_name=f"silicon_story_{selected_id}.txt",
            mime="text/plain",
            key=f"download_{selected_id}",
        )

        if st.button(
            "🗑️ Delete This Story",
            key=f"delete_{selected_id}",
        ):
            delete_story(selected_id)
            st.rerun()

    if st.button("Clear All Story History", key="clear_history"):
        st.session_state["confirm_clear_history"] = True

    if st.session_state.get("confirm_clear_history", False):
        st.warning("This permanently deletes all saved stories.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Confirm Delete All", type="primary"):
                clear_history()
                st.session_state.pop("confirm_clear_history", None)
                st.rerun()

        with col2:
            if st.button("Cancel", key="cancel_clear_history"):
                st.session_state.pop("confirm_clear_history", None)
                st.rerun()


# -----------------------------
# Footer
# -----------------------------
st.markdown(
    """
    <div class="app-footer">
        Silicon Stories · AI-Powered Semiconductor Learning
        <br>
        Built with Streamlit, Python, SQLite and Ollama
    </div>
    """,
    unsafe_allow_html=True,
)
