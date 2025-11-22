import streamlit as st
import requests
import json
import os

# --- 1. إعدادات الصفحة (تاتش العاطفة) ---
st.set_page_config(
    page_title="SehaTech AI | رفيقك الطبي",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS Customization (عشان الشكل يبقى مريح للعين) ---
st.markdown("""
<style>
    .stChatInput {border-radius: 20px;}
    .stChatMessage {border-radius: 15px; padding: 10px;}
    .stMarkdown {font-family: 'Segoe UI', sans-serif;}
    /* لون مميز لرسائل الدكتور */
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #f0f2f6; 
        border-left: 5px solid #2E86C1;
    }
</style>
""", unsafe_allow_html=True)

# عنوان التطبيق
st.title("🩺 SehaTech AI")
st.markdown("#### 💙 *مساعدك الطبي الذكي.. لأن صحتك تهمنا*")

# رابط الـ API
API_URL = "https://8000-dep-01kam28bek66ky6z077hhkyms9-d.cloudspaces.litng.ai/chat"

# --- 3. Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # رسالة ترحيب دافئة
    st.session_state.messages.append({
        "role": "assistant",
        "content": "أهلاً بيك يا بطل 👋\nألف سلامة عليك.. طمني حاسس بإيه النهاردة؟ أنا هنا عشان اسمعك واساعدك."
    })

if "summary" not in st.session_state:
    st.session_state.summary = "لا يوجد تاريخ مرضي مسجل."

# --- 4. عرض الرسائل القديمة ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. إدارة الصورة (التعديل المهم) ---
# بنستخدم key ثابت عشان نقدر نتحكم فيه
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def clear_image():
    # دالة عشان تريسيت الـ uploader
    st.session_state.uploader_key += 1

with st.popover("📸 إرفاق أشعة / روشتة", use_container_width=True):
    st.info("ممكن ترفع صورة أشعة، تحليل، أو علبة دواء.")
    uploaded_image = st.file_uploader(
        "اختر الصورة", 
        type=["jpg", "png", "jpeg"], 
        key=f"img_upload_{st.session_state.uploader_key}" # مفتاح متغير
    )
    if uploaded_image:
        st.image(uploaded_image, caption="تم إرفاق الصورة بنجاح ✅", width=200)

# --- 6. استقبال الرسالة ---
prompt = st.chat_input("اكتب اللي حاسس بيه هنا...")

if prompt:
    # 1. عرض رسالة اليوزر
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_image:
            st.image(uploaded_image, caption="صورة مرفقة 📎", width=200)

    # 2. تجهيز البيانات
    files = {}
    if uploaded_image:
        uploaded_image.seek(0)
        files["image"] = (uploaded_image.name, uploaded_image, uploaded_image.type)

    data_payload = {
        "thread_id": "123", # يفضل تغيره لـ UUID لكل جلسة
        "query": prompt,
        "summary": st.session_state.summary
    }
    
    # يفضل تحط الـ Secret في st.secrets مش os.getenv لو على Streamlit Cloud
    # secret = st.secrets["API_SECRET"] 
    secret = os.getenv("secret", "") # Fallback
    headers = {"Authorization": secret}

    # 3. استقبال الرد (Streaming)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Status مع رسائل لطيفة
        status_container = st.status("🤔 لحظة واحدة، براجع حالتك...", expanded=True)
        
        try:
            with requests.post(API_URL, headers=headers, data=data_payload, files=files if files else None, stream=True) as response:
                
                if response.status_code == 401:
                    status_container.update(label="⛔ مشكلة في التصريح", state="error")
                    st.error("عذراً، مفتاح الاتصال غير صحيح.")
                
                elif response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            try:
                                json_data = json.loads(decoded_line)
                                type_ = json_data.get("type")
                                
                                if type_ == "status":
                                    content = json_data.get("content", "")
                                    # ترجمة الحالة لرسائل ودودة
                                    if "Retrieving" in content: msg = "📚 براجع المراجع الطبية..."
                                    elif "Thinking" in content: msg = "🧠 بفكر في الأعراض..."
                                    elif "Vision" in content: msg = "👁️ بحلل الصورة اللي بعتها..."
                                    else: msg = f"⚙️ {content}"
                                    
                                    status_container.write(msg)
                                    status_container.update(label=msg)

                                elif type_ == "token":
                                    content = json_data.get("content", "")
                                    full_response += content
                                    response_placeholder.markdown(full_response + "▌")

                                elif type_ == "final":
                                    new_summary = json_data.get("summary")
                                    if new_summary:
                                        st.session_state.summary = new_summary
                                    
                                    # مسح الصورة أوتوماتيكياً بعد نجاح الرد
                                    if uploaded_image:
                                        clear_image() 

                            except json.JSONDecodeError:
                                pass
                    
                    status_container.update(label="✅ اتفضل يا بطل، دي نصيحتي ليك", state="complete", expanded=False)
                    response_placeholder.markdown(full_response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                    # لو كان فيه صورة، نعمل Rerun عشان الـ Uploader يختفي
                    if files:
                        st.rerun()
                    
                else:
                    status_container.update(label="❌ حصلت مشكلة", state="error")
                    st.error(f"عذراً، السيرفر مشغول حالياً. (كود الخطأ: {response.status_code})")
        
        except Exception as e:
            status_container.update(label="❌ مشكلة في النت", state="error")
            st.error("تأكد من اتصالك بالإنترنت وحاول تاني.")
