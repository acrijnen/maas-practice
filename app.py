"""
MAAS Practice - Streamlit Prototype
Patient Responses Adapted to Clinical Technique in Calibrated Encounters
"""

import streamlit as st
import anthropic
import json
import os
from pathlib import Path
from datetime import datetime

# Configuration
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 500

# Page config
st.set_page_config(
    page_title="MAAS Practice",
    page_icon="🩺",
    layout="centered"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "patient" not in st.session_state:
    st.session_state.patient = None
if "consultation" not in st.session_state:
    st.session_state.consultation = None
if "session_active" not in st.session_state:
    st.session_state.session_active = False
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "paused" not in st.session_state:
    st.session_state.paused = False
if "last_exchange" not in st.session_state:
    st.session_state.last_exchange = None
if "user_feedback_given" not in st.session_state:
    st.session_state.user_feedback_given = False

# Configuration - Feedback email
FEEDBACK_EMAIL = "acrijnen@gmail.com"
FEEDBACK_URL = f"mailto:{FEEDBACK_EMAIL}?subject=MAAS%20Practice%20Feedback&body=Patient%20practiced%3A%20%0A%0AWhat%20worked%3A%20%0A%0AWhat%20could%20be%20better%3A%20%0A"


def log_user_feedback(patient_id, consultation_id, feedback_text):
    """Save user feedback to a local log file."""
    log_path = Path(__file__).parent / "data" / "feedback_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"{timestamp} | {patient_id} | Consultation {consultation_id} | {feedback_text}\n"
    try:
        with open(log_path, "a") as f:
            f.write(entry)
    except Exception:
        pass  # Don't break the app if logging fails


def load_patients():
    """Load all available patients from data/patients folder."""
    patients_dir = Path(__file__).parent / "data" / "patients"
    patients = {}
    if patients_dir.exists():
        for patient_file in patients_dir.glob("*.json"):
            with open(patient_file, "r") as f:
                patient_data = json.load(f)
                patients[patient_data["patient_id"]] = patient_data
    return patients


def load_prompt(prompt_name):
    """Load a prompt from data/prompts folder."""
    prompt_path = Path(__file__).parent / "data" / "prompts" / f"{prompt_name}.txt"
    if prompt_path.exists():
        with open(prompt_path, "r") as f:
            return f.read()
    return ""


def load_introduction():
    """Load the introduction text."""
    intro_path = Path(__file__).parent.parent / "APP-INTRODUCTION.md"
    if intro_path.exists():
        with open(intro_path, "r") as f:
            content = f.read()
            # Remove the header and trailing separator for display
            lines = content.split('\n')
            # Skip first line (# header) and last lines (--- and Ready?)
            return '\n'.join(lines[2:-3])
    return ""


def build_system_prompt(patient, consultation):
    """Build the complete system prompt for patient simulation."""
    base_prompt = load_prompt("patient-simulation")

    # Build follow-up context if applicable
    follow_up_context = ""
    if consultation.get("for_follow_up"):
        fu = consultation["for_follow_up"]
        follow_up_context = f"""
## Follow-Up Context

**Previous consultation:** {fu.get('previous_consultation_summary', 'N/A')}

**What was recommended:**
{json.dumps(fu.get('what_was_recommended', []), indent=2)}

**What patient remembers:**
{json.dumps(fu.get('what_patient_remembers', []), indent=2)}

**What patient forgot:**
{json.dumps(fu.get('what_patient_forgot', []), indent=2)}

**Interval since last visit:** {fu.get('interval', {}).get('duration', 'N/A')}
**Symptom evolution:** {fu.get('interval', {}).get('symptom_evolution', 'N/A')}
**Compliance:** {fu.get('interval', {}).get('compliance', {}).get('details', 'N/A')}
**Patient experience during interval:** {fu.get('interval', {}).get('patient_experience', 'N/A')}
"""
        if fu.get('results'):
            follow_up_context += f"""
**Test results to discuss:**
{json.dumps(fu['results'].get('tests', {}), indent=2)}

**How to explain results:** {fu['results'].get('how_to_explain', 'N/A')}
"""

    # Build ICE section
    ice = consultation.get('ideas_concerns_expectations', {})

    system_prompt = f"""{base_prompt}

## Patient Identity (Constant)

**Name:** {patient['patient']['name']}
**Age:** {patient['patient']['age']} years old
**Gender:** {patient['patient']['gender']}
**Occupation:** {patient['patient']['occupation']}
**Education:** {patient['patient']['education_level']}

**Personality:**
- Style: {patient['patient']['personality']['baseline_style']}
- Trust building: {patient['patient']['personality']['trust_building']}
- Core traits: {patient['patient']['personality']['core_traits']}

## Background

**Living situation:** {patient['background']['living_situation']}
**Family:** {patient['background']['family']}
**Support system:** {patient['background']['support_system']}
**Work context:** {patient['background']['work_context']}

## Medical History at This Point

**Past medical:** {json.dumps(patient['baseline_medical_history'].get('past_medical', []))}
**Current medications:** {json.dumps(consultation['history_at_this_point'].get('current_medications', []))}
**Allergies:** {json.dumps(patient['baseline_medical_history'].get('allergies', []))}
**Family history:** {json.dumps(patient['baseline_medical_history'].get('family_history', []))}
**Smoking:** {patient['baseline_medical_history']['social_history'].get('smoking', 'N/A')}
**Alcohol:** {patient['baseline_medical_history']['social_history'].get('alcohol', 'N/A')}

## This Consultation

**Setting:** {consultation['scenario']['time_context']}
**Appearance:** {consultation['scenario']['appearance']}
**Emotional state:** {consultation['scenario']['emotional_state']}
**Trust level:** {consultation['scenario']['trust_level']}

## Presenting Problem

**Stated reason:** {consultation['presenting_problem']['stated_reason']}
**Real reason:** {consultation['presenting_problem']['real_reason']}
**Hidden agenda:** {consultation['presenting_problem'].get('hidden_agenda', 'None')}

## Ideas, Concerns, Expectations

**Ideas (what patient thinks):** {ice.get('ideas', 'N/A')}
**Concerns (what patient fears):** {ice.get('concerns', 'N/A')}
**Expectations (what patient wants):** {ice.get('expectations', 'N/A')}

## Clinical Information

**Chief Complaint:** {consultation['complaint']['chief_complaint']}

**Heuristic 1 - Nature:**
{json.dumps(consultation['complaint']['heuristic_1_nature'], indent=2)}

**Heuristic 2 - Time:**
{json.dumps(consultation['complaint']['heuristic_2_time'], indent=2)}

**Heuristic 3 - Modifiers:**
{json.dumps(consultation['complaint']['heuristic_3_modifiers'], indent=2)}

**Heuristic 4 - Accompanying:**
{json.dumps(consultation['complaint']['heuristic_4_accompanying'], indent=2)}
{follow_up_context}

## Red Flags

**Present:** {json.dumps(consultation['red_flags'].get('present', []))}
**Absent:** {json.dumps(consultation['red_flags'].get('absent', []))}
**Notes:** {consultation['red_flags'].get('notes', '')}

## Information Reveal Rules

**Freely shared (volunteer without prompting):**
{json.dumps(consultation['simulation_guidance']['information_reveal']['freely_shared'], indent=2)}

**If asked directly:**
{json.dumps(consultation['simulation_guidance']['information_reveal']['if_asked_directly'], indent=2)}

**If asked sensitively (requires trust):**
{json.dumps(consultation['simulation_guidance']['information_reveal']['if_asked_sensitively'], indent=2)}

**Will not share (protect until significant rapport):**
{json.dumps(consultation['simulation_guidance']['information_reveal']['will_not_share'], indent=2)}

**Emotional moments (topics that trigger emotion):**
{json.dumps(consultation['simulation_guidance'].get('emotional_moments', []), indent=2)}

## Guardrails
{json.dumps(consultation['simulation_guidance']['guardrails'], indent=2)}

---

You are now {patient['patient']['name']}. Respond only as this patient. Wait for the student to speak first.
"""
    return system_prompt


def get_api_key():
    """Get API key from Streamlit secrets or environment."""
    try:
        # Try section format first: [anthropic] api_key
        return st.secrets["anthropic"]["api_key"]
    except:
        try:
            # Try flat format: ANTHROPIC_API_KEY
            return st.secrets["ANTHROPIC_API_KEY"]
        except:
            return os.environ.get("ANTHROPIC_API_KEY")


def get_patient_response(messages, system_prompt):
    """Get response from Claude API."""
    api_key = get_api_key()
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not set. Please set the environment variable."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"


def generate_feedback(patient, consultation, messages, feedback_type="full"):
    """Generate MAAS-mapped feedback on the consultation."""
    api_key = get_api_key()
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not set."

    feedback_prompt = load_prompt("feedback-generation")

    # Build transcript
    transcript = "\n".join([
        f"{'Student' if m['role'] == 'user' else patient['patient']['name']}: {m['content']}"
        for m in messages
    ])

    if feedback_type == "interim":
        instruction = "Provide brief interim feedback on how the consultation is going so far. Focus on 2-3 specific observations about technique."
    elif feedback_type == "advice":
        instruction = "The student is stuck. Provide a helpful hint about what they might try next, without giving away the answer."
    else:
        instruction = "Provide complete MAAS-mapped feedback on this consultation."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500 if feedback_type == "full" else 500,
            system=feedback_prompt if feedback_prompt else "You are a medical education expert providing feedback on consultation skills.",
            messages=[{
                "role": "user",
                "content": f"""
## Case: {consultation['title']}

## Learning Objectives
{json.dumps(consultation.get('learning_objectives', []), indent=2)}

## MAAS Focus
{json.dumps(consultation.get('maas_focus', {}), indent=2)}

## Transcript
{transcript}

{instruction}
"""
            }]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error generating feedback: {str(e)}"


def generate_summary(patient, consultation, messages):
    """Generate a learning summary for the consultation."""
    api_key = get_api_key()
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not set."

    transcript = "\n".join([
        f"{'Student' if m['role'] == 'user' else patient['patient']['name']}: {m['content']}"
        for m in messages
    ])

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            system="You are a medical education expert. Provide a concise learning summary.",
            messages=[{
                "role": "user",
                "content": f"""
## Case: {consultation['title']}

## Learning Objectives
{json.dumps(consultation.get('learning_objectives', []), indent=2)}

## Transcript
{transcript}

Provide a brief summary of:
1. What information the student gathered
2. Key things they discovered (or missed)
3. One specific thing they did well
4. One specific thing to work on next time

Keep it encouraging and practical.
"""
            }]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error generating summary: {str(e)}"


def download_transcript(patient, consultation, messages, feedback=None):
    """Generate downloadable transcript."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = f"""MAAS Practice - Consultation Transcript
========================================
Patient: {patient['patient']['name']}
Consultation: {consultation['title']}
Date: {timestamp}

TRANSCRIPT
----------
"""
    for m in messages:
        role = "Student" if m["role"] == "user" else patient["patient"]["name"]
        content += f"\n{role}: {m['content']}\n"

    if feedback:
        content += f"""

FEEDBACK
--------
{feedback}
"""

    content += """

---
Generated by MAAS Practice
Patient Responses Adapted to Clinical Technique in Calibrated Encounters
"""
    return content


def handle_command(command, patient, consultation, messages):
    """Handle special commands from the user."""
    cmd = command.lower().strip()

    if cmd == "pause":
        st.session_state.paused = True
        return "paused", "Take your time. Type anything when you're ready to continue."

    elif cmd == "feedback":
        feedback = generate_feedback(patient, consultation, messages, "interim")
        return "feedback", feedback

    elif cmd == "advice":
        advice = generate_feedback(patient, consultation, messages, "advice")
        return "advice", advice

    elif cmd == "summary":
        summary = generate_summary(patient, consultation, messages)
        return "summary", summary

    elif cmd == "again":
        if st.session_state.last_exchange:
            # Remove the last exchange
            if len(st.session_state.messages) >= 2:
                st.session_state.messages = st.session_state.messages[:-2]
            return "again", "Let's try that again. What would you like to say?"
        return "again", "Nothing to redo yet. Keep going."

    return None, None


# Main app
def main():
    st.title("MAAS Practice")
    st.caption("Patient Responses Adapted to Clinical Technique in Calibrated Encounters")

    # Load available patients
    patients = load_patients()

    if not patients:
        st.error("No patients found. Please add patient files to data/patients/")
        return

    # Sidebar for patient/consultation selection and controls
    with st.sidebar:
        st.header("Session Controls")

        if not st.session_state.session_active:
            # Patient selection
            patient_options = {p["patient"]["name"]: p["patient_id"] for p in patients.values()}
            selected_name = st.selectbox(
                "Select a patient:",
                options=list(patient_options.keys())
            )
            selected_id = patient_options[selected_name]
            selected_patient = patients[selected_id]

            # Consultation selection for this patient
            consultations = selected_patient.get("consultations", [])
            if consultations:
                consultation_options = {
                    f"{c['consultation_id']}. {c['title']}": i
                    for i, c in enumerate(consultations)
                }
                selected_consultation_title = st.selectbox(
                    "Select a consultation:",
                    options=list(consultation_options.keys())
                )
                selected_consultation_idx = consultation_options[selected_consultation_title]
                selected_consultation = consultations[selected_consultation_idx]

                # Show consultation info
                st.markdown(f"**Difficulty:** {selected_consultation.get('difficulty', 'N/A')}")
                st.markdown(f"**Duration:** ~{selected_consultation.get('estimated_duration_minutes', '?')} min")
                st.markdown(f"**Type:** {selected_consultation.get('type', 'N/A')}")

                if selected_consultation.get('learning_objectives'):
                    st.markdown("**Learning objectives:**")
                    for obj in selected_consultation['learning_objectives']:
                        st.markdown(f"- {obj}")

                if st.button("Start Interview", type="primary"):
                    st.session_state.patient = selected_patient
                    st.session_state.consultation = selected_consultation
                    st.session_state.messages = []
                    st.session_state.session_active = True
                    st.session_state.feedback_shown = False
                    st.session_state.paused = False
                    st.session_state.last_exchange = None
                    st.session_state.user_feedback_given = False
                    st.session_state.user_feedback_text = None
                    st.rerun()

        else:
            # Active session controls
            st.markdown(f"**Patient:** {st.session_state.patient['patient']['name']}")
            st.markdown(f"**Consultation:** {st.session_state.consultation['title']}")
            st.markdown(f"**Messages:** {len(st.session_state.messages)}")

            st.divider()
            st.markdown("**Commands:**")
            st.markdown("- `pause` - take time to think")
            st.markdown("- `feedback` - how am I doing?")
            st.markdown("- `advice` - I'm stuck")
            st.markdown("- `summary` - what did I learn?")
            st.markdown("- `again` - try that again")

            st.divider()

            if st.button("End Interview"):
                st.session_state.session_active = False
                st.rerun()

            if st.button("Restart"):
                st.session_state.messages = []
                st.session_state.feedback_shown = False
                st.session_state.paused = False
                st.session_state.last_exchange = None
                st.rerun()

            if st.button("Different Patient"):
                st.session_state.patient = None
                st.session_state.consultation = None
                st.session_state.messages = []
                st.session_state.session_active = False
                st.session_state.feedback_shown = False
                st.session_state.paused = False
                st.session_state.user_feedback_given = False
                st.rerun()

        # Feedback link - always visible at bottom of sidebar
        st.divider()
        st.markdown("**Help us improve**")
        st.markdown(f"[Share feedback]({FEEDBACK_URL})")

    # Main content area
    if st.session_state.session_active and st.session_state.patient:
        patient = st.session_state.patient
        consultation = st.session_state.consultation

        # Show patient info
        with st.expander("Patient Information", expanded=False):
            st.markdown(f"""
**Name:** {patient['patient']['name']}
**Age:** {patient['patient']['age']}
**Occupation:** {patient['patient']['occupation']}
**Appearance:** {consultation['scenario']['appearance']}
            """)

        st.divider()

        # Chat interface
        for message in st.session_state.messages:
            role = "user" if message["role"] == "user" else "assistant"
            with st.chat_message(role):
                st.write(message["content"])

        # Show system messages (feedback, advice, etc.)
        if "system_message" in st.session_state and st.session_state.system_message:
            st.info(st.session_state.system_message)
            st.session_state.system_message = None

        # Chat input
        if prompt := st.chat_input("Type what you would say to the patient..."):
            # Check for commands
            cmd_type, cmd_response = handle_command(prompt, patient, consultation, st.session_state.messages)

            if cmd_type:
                if cmd_type == "again":
                    st.session_state.system_message = cmd_response
                    st.rerun()
                else:
                    st.info(cmd_response)
                    if cmd_type == "paused":
                        st.session_state.paused = False
            else:
                # Regular message - add to conversation
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.write(prompt)

                # Get patient response
                system_prompt = build_system_prompt(patient, consultation)
                with st.chat_message("assistant"):
                    with st.spinner(f"{patient['patient']['name']} is thinking..."):
                        response = get_patient_response(
                            st.session_state.messages,
                            system_prompt
                        )
                    st.write(response)

                # Store response and last exchange
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.last_exchange = (prompt, response)

    elif st.session_state.patient and not st.session_state.session_active:
        # Session ended - show feedback
        patient = st.session_state.patient
        consultation = st.session_state.consultation

        st.header("Interview Complete")
        st.markdown(f"**Patient:** {patient['patient']['name']}")
        st.markdown(f"**Consultation:** {consultation['title']}")
        st.markdown(f"**Total exchanges:** {len(st.session_state.messages) // 2}")

        # Quick feedback question before showing MAAS feedback
        if not st.session_state.user_feedback_given:
            st.divider()
            st.markdown("**Before we show your feedback — one quick question:**")
            user_improvement = st.text_input(
                "What's one thing that would make this practice better?",
                placeholder="Any thought is helpful — about the patient, the app, anything...",
                key="improvement_input"
            )
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Submit", type="primary"):
                    if user_improvement:
                        # Log feedback to file
                        log_user_feedback(
                            patient['patient_id'],
                            consultation['consultation_id'],
                            user_improvement
                        )
                        st.session_state.user_feedback_text = user_improvement
                    st.session_state.user_feedback_given = True
                    st.rerun()
            with col2:
                if st.button("Skip"):
                    st.session_state.user_feedback_given = True
                    st.rerun()
            st.stop()

        # Show thank you if they gave feedback
        if hasattr(st.session_state, 'user_feedback_text') and st.session_state.user_feedback_text:
            st.success("Thanks for your feedback!")

        # Generate and show feedback
        if not st.session_state.feedback_shown:
            with st.spinner("Generating feedback..."):
                feedback = generate_feedback(patient, consultation, st.session_state.messages, "full")
                st.session_state.feedback = feedback
                st.session_state.feedback_shown = True

        st.subheader("Feedback")
        st.markdown(st.session_state.feedback)

        st.divider()

        # Transcript download
        st.subheader("Download Transcript")
        transcript = download_transcript(
            patient,
            consultation,
            st.session_state.messages,
            st.session_state.feedback if st.session_state.feedback_shown else None
        )
        st.download_button(
            label="Download Transcript",
            data=transcript,
            file_name=f"maas-practice-{patient['patient_id']}-{consultation['consultation_id']}-{datetime.now().strftime('%Y%m%d-%H%M')}.txt",
            mime="text/plain"
        )

        # Show transcript
        with st.expander("View Transcript"):
            for m in st.session_state.messages:
                role = "Student" if m["role"] == "user" else patient["patient"]["name"]
                st.markdown(f"**{role}:** {m['content']}")

        # Options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Try Again"):
                st.session_state.messages = []
                st.session_state.session_active = True
                st.session_state.feedback_shown = False
                st.session_state.user_feedback_given = False
                st.session_state.user_feedback_text = None
                st.rerun()
        with col2:
            if st.button("Different Patient"):
                st.session_state.patient = None
                st.session_state.consultation = None
                st.session_state.messages = []
                st.session_state.session_active = False
                st.session_state.feedback_shown = False
                st.session_state.user_feedback_given = False
                st.session_state.user_feedback_text = None
                st.rerun()

    else:
        # Welcome screen with introduction
        intro = load_introduction()
        if intro:
            st.markdown(intro)
        else:
            st.markdown("""
## How to Use MAAS Practice

This is practice for real consultations. Type what you would say to the patient. Take your time — the slower pace of writing helps you think before you speak.

Don't worry about being perfect. Real consultations aren't perfect either. What matters is that you're practicing the skill of finding the right words.

**Commands you can use:**
- **pause** — when you need time to think
- **feedback** — when you want to know how you're doing
- **advice** — when you're stuck and want a hint
- **summary** — to see what you've learned
- **again** — to try that last part differently

**One important thing:** We take your diagnosis and treatment seriously. What you do in one consultation carries forward to the next.
            """)

        st.markdown("---")
        st.markdown("**Select a patient from the sidebar to begin**")


if __name__ == "__main__":
    main()
