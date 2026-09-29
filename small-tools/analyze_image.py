import ollama

# 确保你已经 ollama pull llava
response = ollama.chat(
    model='gemma-4-E4B-it-UD-Q6_K_XL:latest',
    messages=[{
        'role': 'user',
        'content': '描述一下这张图片',
        'images': ['./dan-me.jpg']  # 这里换成你实际的图片路径
    }]
)

print(response['message']['content'])