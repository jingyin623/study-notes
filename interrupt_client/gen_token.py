from livekit import api
import os

# 确保这里的 Key 和 Secret 跟你的 livekit.yaml 以及 agent.py 一致
API_KEY = "devkey"
API_SECRET = "secret"

def generate_token():
    token = api.AccessToken(API_KEY, API_SECRET) \
        .with_identity("user1") \
        .with_name("My User") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room="my-first-room",
        ))
    
    print("\n--- 你的 Room Token 如下，请全选复制 ---")
    print(token.to_jwt())
    print("------------------------------------------\n")

if __name__ == "__main__":
    generate_token()
    print("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiTXkgVXNlciIsInZpZGVvIjp7InJvb21Kb2luIjp0cnVlLCJyb29tIjoibXktZmlyc3Qtcm9vbSIsImNhblB1Ymxpc2giOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWV9LCJzdWIiOiJ1c2VyMSIsImlzcyI6ImRldmtleSIsIm5iZiI6MTc3MDQwMzI2NSwiZXhwIjoxNzcwNDI0ODY1fQ.mRhwXN3aohVgw7uxQ4U-qdU0B1RgV0elkFAwGAsVbHU")
    print("ws://localhost:7880")