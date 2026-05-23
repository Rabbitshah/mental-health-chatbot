import os

path = r"c:\Users\maana\Desktop\mental-health-chatbot\frontend\src\components\Chatbot.jsx"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('const token = localStorage.getItem("token");', 'const isLoggedIn = localStorage.getItem("isLoggedIn") === "true";')
content = content.replace('if (!token) {', 'if (!isLoggedIn) {')

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("Done")
