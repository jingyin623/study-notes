"""
二维码生成器，支持将文本消息转换为高性能的 PNG 二维码内存字节流
"""
import io
import qrcode

def generate_qr_image_stream(text_message: str) -> io.BytesIO:
    """
    将文本消息转换为高性能的 PNG 二维码内存字节流
    """
    # 1. 严格初始化配置参数
    qr = qrcode.QRCode(
        version=None,               # None 表示自适应文本长度调整矩阵大小
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% 高纠错级别，抗污损能力最强
        box_size=10,                # 每个黑白方块占 10 个像素宽度
        border=4,                   # 标准 4 格安全静区白边
    )
    
    # 2. 注入数据并强制使用 utf-8 规避乱码
    qr.add_data(text_message.encode('utf-8'))
    qr.make(fit=True)
    
    # 3. 渲染为图像并将其导出至内存
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_stream = io.BytesIO()
    img.save(img_stream, format="PNG") # 👈 核心：在内存中直接转化为 PNG 二进制编码
    img_stream.seek(0)                 # 重置指针，方便上层业务直接读取、上传或分发
    
    return img_stream

# 示例调用：
if __name__ == "__main__":
    msg = "LPA:1$cel.prod.ondemandconnectivity.com$20D0B8DAEDA4B26AB84847F9E8A7A2F28B6C01FB8B41B61725E7E015405CE2D2"
    with open("output_qr.png", "wb") as f:
        f.write(generate_qr_image_stream(msg).read())