import streamlit as st
import sys

st.title("Test Streamlit App")
st.write("If you can see this, Streamlit is working correctly!")

# Display some basic UI elements
st.header("Basic UI Elements")
st.subheader("Button")
if st.button("Click me"):
    st.success("Button clicked!")

st.subheader("Text Input")
name = st.text_input("Enter your name")
if name:
    st.write(f"Hello, {name}!")

st.subheader("Slider")
value = st.slider("Select a value", 0, 100, 50)
st.write(f"Selected value: {value}")

# Display system info
st.header("System Info")
st.json({
    "streamlit_version": st.__version__,
    "python_version": sys.version,
    "platform": sys.platform
}) 