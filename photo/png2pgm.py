from PIL import Image
import sys

def convert_to_pgm(input_path, output_path):
    # 打开图像并转换为灰度
    img = Image.open(input_path).convert("L")
    width, height = img.size

    # 获取像素数据
    pixel_bytes = img.tobytes()

    # 写入符合 OpenMV 的 P5 格式 PGM 文件
    with open(output_path, 'wb') as f:
        f.write(f"P5\n{width} {height}\n255\n".encode())
        f.write(pixel_bytes)

    print(f"✅ 转换成功：{output_path}（尺寸：{width}x{height}）")

# 示例用法
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python3 convert.py 输入图像 输出.pgm")
        sys.exit(1)

    convert_to_pgm(sys.argv[1], sys.argv[2])
