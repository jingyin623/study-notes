import json
import requests

def generate_english_quiz(word):
    # 1. 确认 IP 和 端口
    url = "http://192.168.100.20:11434/api/chat"
    
    # 2. 这里的 model 必须和你 curl 出来的 name 完全一致
    MODEL_NAME = "llama3.1:8b" 

    prompt = f"""
    Please generate an English example sentence for the word '{word}'.
    Replace the word '{word}' with '_____' to create a fill-in-the-blank quiz.
    Output strictly in JSON format with keys: "quiz", "answer", "translation".
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "format": "json", # 强制要求 JSON
        "stream": False   # 禁用流式输出，一次性获取结果
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # 检查状态码
        
        # 解析 Ollama 的 Chat API 返回结构
        raw_content = response.json()['message']['content']
        result = json.loads(raw_content)
        
        print("\n" + "="*30)
        print(f"题目: {result['quiz']}")
        print(f"翻译提示: {result['translation']}")
        print("="*30)
        
        user_input = input("\n请输入单词补全句子: ").strip()
        
        if user_input.lower() == result['answer'].lower():
            print("\n✅ Correct! (回答正确)")
        else:
            print(f"\n❌ Wrong. The answer is: {result['answer']}")
            
    except Exception as e:
        print(f"\n调用失败，请检查模型名称或网络: {e}")

if __name__ == "__main__":
    target_word = input("请输入你想练习的单词: ").strip()
    if target_word:
        generate_english_quiz(target_word)