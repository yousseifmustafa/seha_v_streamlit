import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
secret = os.getenv("secret")
API_URL = "https://8001-dep-01k97cftrq0d0tz2y37e2km2ge-d.cloudspaces.litng.ai"
AUTH_HEADERS = {
    "Authorization": secret
}


def diagnose_api_call(user_query, conversation_summary):
    """ Client function to call the /diagnose TEXT endpoint. """
    url = f"{API_URL}/diagnose"
    data = {
        "user_query": user_query,
        "conversation_summary": conversation_summary
    }
    try:
        response = requests.post(url, json=data,headers=AUTH_HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise e

def ocr_api_call(user_query, image_bytes):
    """ Client function to call the /analyze IMAGE endpoint. """
    url = f"{API_URL}/analyze"
    
    files = {'image': ('image.jpg', image_bytes, 'image/jpeg')}
    data = {'user_query': user_query}
    
    try:
        response = requests.post(url, files=files, data=data,headers=AUTH_HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise e



def main_app():
    
    st.set_page_config(
        page_title="SehaTech 🏥", page_icon="🏥", layout="wide", initial_sidebar_state="collapsed"
    )

    if "current_mode" not in st.session_state:
        st.session_state.current_mode = "MAIN_MENU"
        st.session_state.chat_history = []
        st.session_state.conversation_summary = None 

    st.title("🏥 SehaTech Bot")
    
    if st.session_state.current_mode == "MAIN_MENU":
        
        col_main_mid = st.columns([1, 2, 1])
        with col_main_mid[1]:
            st.markdown("<p style='text-align: center; font-size: 1.25rem;'>Your intelligent medical assistant. Please select a service to begin.</p>", unsafe_allow_html=True)
            st.divider()

            col1, col2 = st.columns(2)
            
            with col1:
                with st.container(border=True):
                    st.markdown("### 🩺 Symptom Analysis")
                    st.markdown("Describe your symptoms to get a **preliminary RAG analysis**.")
                    if st.button("Start Now", key="diag_start", use_container_width=True, type="primary"):
                        st.session_state.current_mode = "DIAGNOSE_MODE"
                        st.session_state.chat_history = [
                            {"role": "assistant", "content": """Welcome to the **Symptom Analysis Service**."""}
                        ]
                        st.rerun()

            with col2:
                with st.container(border=True):
                    st.markdown("### 📄 Image Analysis")
                    st.markdown("Read prescriptions, lab results, medicine boxes and More using the **Qwen-VL model**.")
                    if st.button("Start Now", key="OCR", use_container_width=True, type="primary"):
                        st.session_state.current_mode = "OCR_MODE" 
                        st.rerun() 
            
            st.divider()
            st.markdown("""<p style='text-align: center; color: grey;'>SehaTech v1.0 - Disclaimer: This tool uses AI, which can make mistakes or generate inaccurate information.</p>""", unsafe_allow_html=True)


    elif st.session_state.current_mode == "DIAGNOSE_MODE":

        with st.sidebar:
            st.markdown("### 🧭 Current Mode")
            st.markdown("Symptom Analysis")
            st.divider()
            if st.button("⬅️ Back to Main Menu", use_container_width=True):
                st.session_state.current_mode = "MAIN_MENU"
                st.rerun()

        st.title("🩺 Symptom Analysis Assistant")
        
        for message in st.session_state.chat_history:
             with st.chat_message(message["role"]):
                 st.markdown(message["content"])

        if user_input := st.chat_input("Describe your symptoms here..."):
            
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.status("Bot: Thinking...", expanded=True) as status:
                    st.write("Analyzing symptoms...")
                    
                    try:
                        response_data = diagnose_api_call(
                            user_input, 
                            st.session_state.conversation_summary 
                        )
                        answer = response_data['answer']
                        new_summary = response_data['new_summary']
                        
                        status.update(label="Analysis Complete!", state="complete", expanded=False)
                        st.markdown(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                        st.session_state.conversation_summary = new_summary # تحديث الملخص

                    except Exception as e:
                        status.update(label="Error", state="error", expanded=True)
                        st.error(f"Error processing diagnosis via API: {e}")
                        st.session_state.chat_history.append({"role": "assistant", "content": f"API Error: {e}"})
            
            st.rerun()
    elif st.session_state.current_mode == "OCR_MODE":
        
        with st.sidebar:
            st.markdown("### 🧭 Current Mode")
            st.markdown("Image Analysis")
            st.divider()
            if st.button("⬅️ Back to Main Menu", use_container_width=True):
                st.session_state.current_mode = "MAIN_MENU"
                st.rerun()

        st.title("📄 Analyze Medical Images")
        st.markdown("Upload a prescription or lab result and ask a specific question.")

        uploaded_file = st.file_uploader("Upload an image here:", type=["jpg", "png", "jpeg"])
        user_question = st.text_input("Ask a question about the image:", placeholder="e.g., What is this medication and what is its dosage?")

        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image", width=300)

        if st.button("Analyze Image", key="imageRec", use_container_width=True, type="primary"):
            if uploaded_file is not None and user_question:
                image_bytes = uploaded_file.getvalue()
                
                with st.spinner("Analyzing image... 🧠"):
                    try:
                        response_data = ocr_api_call(user_question, image_bytes)
                        response_text = response_data['answer']
                        
                        st.success("Analysis Complete!")
                        st.markdown(response_text)
                        
                    except Exception as e:
                        st.error(f"Error processing image via API: {e}")
            else:
                st.warning("Please upload an image and ask a question first.")


if __name__ == "__main__":

    main_app()
