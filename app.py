from PIL import Image
import io
import logging
import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')
os.environ['GOOGLE_API_KEY'] = api_key
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 1,
    "max_output_tokens": 99998,
}

st.set_page_config(page_title="Talk2Image 🖼️")

with st.sidebar:
    st.title("Configuration")
    api_key_input = st.sidebar.text_input("Enter your Gemini API Key (if available)", type="password", placeholder="If you have!")
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.8, 0.1)
    model_selection = st.sidebar.selectbox("Select Model", ("gemini-1.5", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-1.5-flash"))
    uploaded_image = st.file_uploader("Upload your image here:", accept_multiple_files=False, type=["png", "jpg"])
    if uploaded_image:
        image_bytes = uploaded_image.read()

    st.markdown("App built by Subhayu Dutta")

def generate_response(messages, model="gemini-pro-vision"):
    model = genai.GenerativeModel(model)
    return model.generate_content(messages, generation_config=generation_config)

if "messages" not in st.session_state:
    st.session_state["messages"] = []
messages = st.session_state["messages"]

st.title('Talk2Image 🖼️')
st.write('Talk with your image and ask questions using Gemini!')


if messages:
    for item in messages:
        role, parts = item.values()
        if role == "user":
            st.chat_message("user", avatar="user.png").markdown(parts[0])
        elif role == "model":
            st.chat_message("assistant", avatar="bot.png").markdown(parts[0])

user_input = st.chat_input("Say something")

if user_input:
    st.chat_message("user", avatar="user.png").markdown(user_input)
    response_area = st.chat_message("assistant", avatar="bot.png").markdown("...")

    if "image_bytes" in globals():
        vision_message = [user_input, Image.open(io.BytesIO(image_bytes))]
        try:
            response = generate_response(vision_message, model="gemini-pro-vision")
        except google_exceptions.InvalidArgument as e:
            if "API key not valid" in str(e):
                st.error("Invalid API key. Please provide a valid API key.")
            else:
                st.error("An error occurred. Please try again.")
        except Exception as e:
            logging.error(e)
            st.error("An error occurred. Please refresh the page and try again.")
    else:
        vision_message = [{"role": "user", "parts": [user_input]}]
        st.warning("No image uploaded. Generating result using the default gemini-pro model.")
        try:
            response = generate_response(vision_message, model="gemini-pro-vision")
        except google_exceptions.InvalidArgument as e:
            if "API key not valid" in str(e):
                st.error("Invalid API key. Please provide a valid API key.")
            else:
                st.error("An error occurred. Please try again.")
        except Exception as e:
            logging.error(e)
            st.error("An error occurred. Please refresh the page and try again.")

    if response:
        response_text = ""
        for chunk in response:
            if chunk.candidates:
                response_text += chunk.text
            if not response_text:
                response_text = "inappropriate words"
                st.error("Your input violates the rules. Please try again.")
        response_area.markdown(response_text)
