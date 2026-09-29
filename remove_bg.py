"""
抠图脚本：从 tubiao 文件夹的 JPG 图片中移除纯色背景，生成透明 PNG。
原理：采样四角背景色，将接近背景色的像素设为透明，并对边缘做羽化处理。
"""
from PIL import Image, ImageDraw
import os
import numpy as np

def remove_background(input_path, output_path, threshold=35, feather=2):
    """
    从图片中移除纯色背景。
    threshold: 颜色差异阈值，越大移除越多
    feather: 边缘羽化像素数
    """
    img = Image.open(input_path).convert('RGBA')
    arr = np.array(img)
    h, w = arr.shape[:2]

    # 采样四角 10x10 区域取平均作为背景色
    corners = []
    for corner in [(0, 0), (w-10, 0), (0, h-10), (w-10, h-10)]:
        region = arr[corner[1]:corner[1]+10, corner[0]:corner[0]+10]
        corners.append(region.reshape(-1, 4).mean(axis=0))
    bg_color = np.mean(corners, axis=0).astype(int)
    print(f"  背景色: RGB({bg_color[0]}, {bg_color[1]}, {bg_color[2]})")

    # 计算每个像素与背景色的距离
    rgb = arr[:, :, :3].astype(float)
    dist = np.sqrt(np.sum((rgb - bg_color[:3])**2, axis=2))

    # 创建 alpha 通道
    alpha = arr[:, :, 3].copy().astype(float)

    # 距离 < threshold 的设为完全透明
    alpha[dist < threshold] = 0

    # 边缘羽化：threshold 到 threshold+feather 之间渐变
    feather_zone = (dist >= threshold) & (dist < threshold + feather * 3)
    if feather_zone.any():
        feather_alpha = 255 * (dist[feather_zone] - threshold) / (feather * 3)
        alpha[feather_zone] = feather_alpha

    arr[:, :, 3] = alpha.astype(np.uint8)
    result = Image.fromarray(arr)
    result.save(output_path, 'PNG')
    print(f"  保存: {output_path}")

if __name__ == '__main__':
    tubiao_dir = r'f:\脉衡界_完整备份_20260806\tubiao'
    output_dir = r'f:\脉衡界_完整备份_20260806\frontend\img'

    # 3张原图对应3个动作 + 第3张复用为guide
    mapping = {
        '057bb422518f70d31b770e9dc0c4a0ab.jpg': 'mascot_idle.png',
        'e0616e5ed01eed32155c24e0304542e0.jpg': 'mascot_thinking.png',
        'ff2e6dae0e31e433c13ca710bfc0d6bf.jpg': 'mascot_happy.png',
    }

    for src_name, dst_name in mapping.items():
        src = os.path.join(tubiao_dir, src_name)
        dst = os.path.join(output_dir, dst_name)
        print(f"处理: {src_name} -> {dst_name}")
        remove_background(src, dst, threshold=40, feather=3)

    # guide 复用 happy
    import shutil
    shutil.copy(
        os.path.join(output_dir, 'mascot_happy.png'),
        os.path.join(output_dir, 'mascot_guide.png')
    )
    print("复制 mascot_happy.png -> mascot_guide.png")
    print("全部完成！")
