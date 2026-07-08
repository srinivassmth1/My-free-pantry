import streamlit as st
from google import genai
import PIL.Image

# 1. Setup Page Configuration
st.set_page_config(page_title="Free Smart Pantry", page_icon="🥦", layout="centered")
st.title("🥦 Free Smart Pantry & Inventory Agent")

# 2. Free API Key Input (Securely handles your free Gemini Key)
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key = st.text_input("Enter your free Gemini API Key:", value=st.session_state.api_key, type="password")
if api_key:
    st.session_state.api_key = api_key
    client = genai.Client(api_key=api_key)
else:
    st.warning("Please enter your Gemini API key to activate the app.")
    st.stop()

# Initialize global session variables to hold persistent inventory
if "inventory" not in st.session_state:
    st.session_state.inventory = ["Paneer", "Tomatoes", "Cilantro", "Butter"] # Starter baseline

# 3. Photo & Bill Capture Interface
st.subheader("📸 Scan Kitchen / Add Bill")
upload_method = st.radio("Choose upload method:", ["Take a Live Photo", "Upload Receipt / Image File"])

image_file = None
if upload_method == "Take a Live Photo":
    image_file = st.camera_input("Snap a photo of your fridge or shopping bill")
else:
    image_file = st.file_uploader("Upload an image asset...", type=["jpg", "jpeg", "png", "heic"])

# 4. Trigger AI Scanning Agent
if image_file is not None:
    if st.button("🤖 Process Photo & Sync Data"):
        with st.spinner("AI is scanning image pixels..."):
            image = PIL.Image.open(image_file)
            
            vision_prompt = """
            Analyze this image (it could be a photo of a refrigerator, pantry, or a grocery receipt bill). 
            List all unique visible food ingredient items clearly. 
            Return the output as a simple comma-separated list of lowercase items (e.g., milk, eggs, chicken).
            Do not write code, descriptions, or explanations. Just list the items.
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[image, vision_prompt]
            )
            
            # Extract new foods and append to live inventory matrix
            scanned_text = response.text.strip()
            new_items = [item.strip().capitalize() for item in scanned_text.split(",") if item.strip()]
            
            # Merge lists uniquely
            st.session_state.inventory = list(set(st.session_state.inventory + new_items))
            st.success("Data synchronization complete! Inventory updated.")

---

# 5. Core Inventory Dashboard
st.subheader("📋 Current Kitchen Inventory")
st.write("Uncheck items you have fully consumed or are running low on:")

current_items = list(st.session_state.inventory)
available_items = []
empty_items = []

for item in current_items:
    # Generates a dynamic layout checkbox for every single food product in memory
    is_stocked = st.checkbox(f"🍏 {item}", value=True, key=f"inv_{item}")
    if is_stocked:
        available_items.append(item)
    else:
        empty_items.append(item)

---

# 6. Automate Your Missing / Pending Shopping List
st.subheader("🛒 Out of Stock / Pending Purchase List")
if len(empty_items) > 0:
    st.error("The following items are getting empty in your fridge:")
    for empty_item in empty_items:
        st.write(f"❌ **{empty_item}** needs to be bought!")
        
    # AI Shopping Assistant Suggestion Module
    if st.button("💡 Suggest Recipes based only on remaining Stock"):
        with st.spinner("Calculating custom recipes..."):
            recipe_prompt = f"Suggest 2 quick meals using only: {', '.join(available_items)}. Keep it brief."
            recipe_resp = client.models.generate_content(model='gemini-2.5-flash', contents=[recipe_prompt])
            st.info(recipe_resp.text)
else:
    st.success("Your fridge is completely full! Nothing is pending purchase.")
