from flask import Flask
import threading

app = Flask(__name__)

interrupt_flag = False

@app.route("/interrupt", methods=["POST"])
def interrupt():
    global interrupt_flag
    interrupt_flag = True
    print("🛑 收到中断请求")
    return "OK"

def should_interrupt():
    global interrupt_flag
    if interrupt_flag:
        interrupt_flag = False
        return True
    return False

if __name__ == "__main__":
    app.run(port=9000)
