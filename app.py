
from database import (
    save_story,
    get_all_stories,
    get_story,
    delete_story,
    clear_history,
)
import json
import re
import requests
import streamlit as st

def extract_title(story):
    for line in story.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:200]
    return "Untitled Silicon Story"

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
            "Cannot connect to Ollama. "
            "Open a terminal and run: ollama serve"
        )
    except requests.exceptions.Timeout:
        st.error("The model took too long to respond. Try a shorter story.")
    except requests.exceptions.RequestException as error:
        st.error(f"Ollama request failed: {error}")
    except (ValueError, AttributeError):
        st.error("Ollama returned an invalid response.")

    return None


# -----------------------------
# Word count helper
# -----------------------------
def count_words(text):
    return len(re.findall(r"\b[\w'-]+\b", text))


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
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group())
        questions = data.get("questions", [])

        if len(questions) != 5:
            return None

        for q in questions:
            if (
                not isinstance(q.get("options"), dict)
                or q.get("answer") not in ["A", "B", "C", "D"]
                or not all(
                    key in q["options"] for key in ["A", "B", "C", "D"]
                )
            ):
                return None

        return questions

    except (json.JSONDecodeError, AttributeError, TypeError):
        return None


# -----------------------------
# Streamlit interface
# -----------------------------
st.set_page_config(
    page_title="Silicon Stories",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 Silicon Stories")
st.subheader("A Creative Learning Engine for the Semiconductor Industry")
st.write(
    "Turn semiconductor concepts into stories, simple explanations, "
    "and interactive quizzes — powered by a local AI model."
)

with st.sidebar:
    st.header("Story Settings")

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
        "Generate Silicon Story",
        type="primary",
        use_container_width=True,
    )

if generate_button:
    if len(selected_terms) != 3:
        st.warning("Please select exactly three semiconductor terms.")
    else:
        with st.spinner("Your AI story is being created..."):
            story = generate_story(
                selected_terms, word_count, genre, age_group
            )

        if story:
            st.session_state["story"] = story
            st.session_state["terms"] = selected_terms
            st.session_state["genre"] = genre
            st.session_state["target_words"] = word_count
            
             # Prevent duplicate saves when Streamlit reruns the page.
            if st.session_state.get("last_saved_story") != story:
                story_id = save_story(
                title=extract_title(story),
                content=story,
                terms=selected_terms,
                genre=genre,
                target_words=word_count,
            )
            st.session_state["last_saved_story"] = story
            st.session_state["current_story_id"] = story_id
            st.success("Story saved to your history!")
            st.session_state.pop("glossary", None)
            st.session_state.pop("quiz", None)
            st.session_state.pop("quiz_answers", None)

# Display saved story
if st.session_state.get("story"):
    story = st.session_state["story"]
    terms = st.session_state["terms"]

    st.divider()
    st.header("📖 Your Silicon Story")
    st.caption(
        f"Genre: {st.session_state['genre']} · "
        f"Target: {st.session_state['target_words']} words · "
        f"Actual: {count_words(story)} words"
    )

    st.markdown(story)

    st.download_button(
        "⬇️ Download Story",
        data=story,
        file_name="silicon_story.txt",
        mime="text/plain",
    )

    st.divider()
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
                st.metric("Your Score", f"{st.session_state['quiz_score']} / 5")

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

st.divider()
st.caption("Powered by Streamlit and Ollama · Local AI generation")

st.divider()
st.header("📚 Story History")

saved_stories = get_all_stories()

if not saved_stories:
    st.info("No saved stories yet. Generate your first story!")
else:
    st.write(f"Total saved stories: {len(saved_stories)}")

    # Select a previous story.
    choices = {
        f"#{item['id']} — {item['title']} "
        f"({item['created_at'][:10]})": item["id"]
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

    if st.button("Clear All Story History"):
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
            if st.button("Cancel"):
                st.session_state.pop("confirm_clear_history", None)
                st.rerun()
