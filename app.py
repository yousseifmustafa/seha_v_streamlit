import streamlit as st
import requests
import json
import os

# إعدادات الصفحة
st.set_page_config(
    page_title="SehaTech AI",
    page_icon="🩺",
    layout="centered"
)



# عنوان التطبيق
st.title("🩺 SehaTech AI Doctor")
st.caption("مساعدك الطبي الذكي (نص + صور)")

# رابط الـ API
API_URL = "https://8000-dep-01kam28bek66ky6z077hhkyms9-d.cloudspaces.litng.ai/chat"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "summary" not in st.session_state:
    st.session_state.summary = "لا يوجد تاريخ مرضي مسجل."

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

with st.popover("➕ إرفاق صورة", use_container_width=False):
    uploaded_image = st.file_uploader("اختر صورة (أشعة/تحاليل)", type=["jpg", "png", "jpeg"], key="img_upload")
    if uploaded_image:
        st.image(uploaded_image, caption="تم اختيار الصورة", width=150)
        st.success("الصورة جاهزة للإرسال مع رسالتك القادمة.")

prompt = st.chat_input("اكتب شكوتك هنا...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_image:
            st.image(uploaded_image, caption="صورة مرفقة", width=200)

    files = {}
    if uploaded_image:
        uploaded_image.seek(0)
        files["image"] = (uploaded_image.name, uploaded_image, uploaded_image.type)

    data_payload = {
        "thread_id":"123",
        "query": prompt,
        "summary": st.session_state.summary
    }
    secret = os.getenv("secret")
    # 2. تجهيز الهيدر (الخلاصة هنا)
    headers = {
        "Authorization":secret}

    # 3. استقبال الرد (Streaming)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        status_container = st.status("جاري تحليل البيانات...", expanded=True)
        
        try:
            # 3. تمرير headers=headers
            with requests.post(API_URL, headers=headers, data=data_payload, files=files if files else None, stream=True) as response:
                
                # التعامل مع حالة الـ Unauthorized (401)
                if response.status_code == 401:
                    status_container.update(label="⛔ غير مصرح", state="error")
                    st.error("فشل المصادقة: تأكد من صحة الـ Token.")
                
                elif response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            try:
                                json_data = json.loads(decoded_line)
                                type_ = json_data.get("type")
                                
                                if type_ == "status":
                                    content = json_data.get("content", "")
                                    status_container.write(f"⚙️ {content}")
                                    status_container.update(label=content)

                                elif type_ == "token":
                                    content = json_data.get("content", "")
                                    full_response += content
                                    response_placeholder.markdown(full_response + "▌")

                                elif type_ == "final":
                                    new_summary = json_data.get("summary")
                                    if new_summary:
                                        st.session_state.summary = new_summary
                                    
                                    # التحقق من حالة الـ Action Required (لو موجودة في الرد النهائي)
                                    if json_data.get("type") == "action_required":
                                         st.warning("النظام يحتاج موافقة!")

                            except json.JSONDecodeError:
                                pass
                    
                    status_container.update(label="✅ تمت المعالجة", state="complete", expanded=False)
                    response_placeholder.markdown(full_response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                else:
                    status_container.update(label="❌ خطأ في السيرفر", state="error")
                    st.error(f"Error: {response.status_code} - {response.text}")
        
        except Exception as e:
            status_container.update(label="❌ فشل الاتصال", state="error")
            st.error(f"Connection Error: {e}")
