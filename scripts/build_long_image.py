# -*- coding: utf-8 -*-
"""生成图文拼接长图版教程（网页打不开时的兜底方案）。"""
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, "assets", "images")
OUT_PATH = os.path.join(BASE, "assets", "教程长图.png")

FONT_DIR = r"C:\Windows\Fonts"
FONT_BOLD = os.path.join(FONT_DIR, "msyhbd.ttc")
FONT_REG = os.path.join(FONT_DIR, "msyh.ttc")

W = 900
PAD = 48
BG = (15, 17, 21)
PANEL = (22, 26, 34)
BORDER = (42, 48, 64)
TEXT = (230, 232, 236)
TEXT_DIM = (150, 155, 168)
ACCENT = (79, 140, 255)
WARN = (255, 176, 32)
OK = (61, 220, 132)

title_font = ImageFont.truetype(FONT_BOLD, 40)
h2_font = ImageFont.truetype(FONT_BOLD, 30)
body_font = ImageFont.truetype(FONT_REG, 22)
caption_font = ImageFont.truetype(FONT_REG, 20)
badge_font = ImageFont.truetype(FONT_BOLD, 22)


def wrap_text(text, font, max_width, draw):
    lines = []
    for raw_line in text.split("\n"):
        line = ""
        for ch in raw_line:
            test = line + ch
            if draw.textlength(test, font=font) > max_width and line:
                lines.append(line)
                line = ch
            else:
                line = test
        lines.append(line)
    return lines


class Canvas:
    def __init__(self, width):
        self.width = width
        self.blocks = []  # list of (height, draw_fn)

    def add_space(self, h):
        self.blocks.append((h, lambda draw, y, w: None))

    def add_title(self, text):
        tmp = Image.new("RGB", (10, 10))
        d = ImageDraw.Draw(tmp)
        h = 70

        def draw_fn(draw, y, w):
            draw.text((PAD, y), text, font=title_font, fill=TEXT)

        self.blocks.append((h, draw_fn))

    def add_intro_panel(self, lines):
        tmp = Image.new("RGB", (10, 10))
        d = ImageDraw.Draw(tmp)
        inner_w = self.width - 2 * PAD - 40
        wrapped = []
        for ln in lines:
            wrapped.extend(wrap_text(ln, body_font, inner_w, d))
        h = 36 + len(wrapped) * 32 + 20

        def draw_fn(draw, y, w):
            draw.rounded_rectangle([PAD, y, w - PAD, y + h], radius=10, fill=PANEL, outline=BORDER, width=1)
            ty = y + 24
            for ln in wrapped:
                draw.text((PAD + 20, ty), ln, font=body_font, fill=TEXT_DIM)
                ty += 32

        self.blocks.append((h + 20, draw_fn))

    def add_step_header(self, num, title):
        h = 70

        def draw_fn(draw, y, w):
            cy = y + 18
            draw.ellipse([PAD, cy, PAD + 44, cy + 44], fill=(42, 58, 92))
            tb = draw.textbbox((0, 0), str(num), font=badge_font)
            tw, th = tb[2] - tb[0], tb[3] - tb[1]
            draw.text((PAD + 22 - tw / 2, cy + 22 - th / 2 - tb[1]), str(num), font=badge_font, fill=ACCENT)
            draw.text((PAD + 60, cy + 4), title, font=h2_font, fill=TEXT)

        self.blocks.append((h, draw_fn))

    def add_body_text(self, text, indent=True):
        tmp = Image.new("RGB", (10, 10))
        d = ImageDraw.Draw(tmp)
        x0 = PAD + 60 if indent else PAD
        inner_w = self.width - x0 - PAD
        wrapped = wrap_text(text, body_font, inner_w, d)
        h = len(wrapped) * 32 + 10

        def draw_fn(draw, y, w):
            ty = y
            for ln in wrapped:
                draw.text((x0, ty), ln, font=body_font, fill=TEXT_DIM)
                ty += 32

        self.blocks.append((h, draw_fn))

    def add_tip(self, text, indent=True):
        tmp = Image.new("RGB", (10, 10))
        d = ImageDraw.Draw(tmp)
        x0 = PAD + 60 if indent else PAD
        inner_w = self.width - x0 - PAD - 24
        wrapped = wrap_text(text, caption_font, inner_w, d)
        h = len(wrapped) * 28 + 24

        def draw_fn(draw, y, w):
            draw.rounded_rectangle([x0, y, x0 + inner_w + 24, y + h], radius=8,
                                    fill=(42, 32, 10), outline=(90, 68, 20), width=1)
            ty = y + 12
            for ln in wrapped:
                draw.text((x0 + 12, ty), ln, font=caption_font, fill=WARN)
                ty += 28

        self.blocks.append((h + 16, draw_fn))

    def add_images_row(self, items, indent=True):
        """items: list of (path, caption)"""
        x0 = PAD + 60 if indent else PAD
        max_total_w = self.width - x0 - PAD
        target_h = 420
        imgs = []
        total_w = 0
        for path, cap in items:
            im = Image.open(path).convert("RGB")
            scale = target_h / im.height
            nw = int(im.width * scale)
            imgs.append((im.resize((nw, target_h)), cap))
            total_w += nw
        gap = 24
        total_w += gap * (len(imgs) - 1)
        # scale down further if exceeds available width
        if total_w > max_total_w:
            factor = max_total_w / total_w
            new_imgs = []
            for im, cap in imgs:
                nw = int(im.width * factor)
                nh = int(im.height * factor)
                new_imgs.append((im.resize((nw, nh)), cap))
            imgs = new_imgs

        row_h = max(im.height for im, _ in imgs) + 40
        h = row_h

        def draw_fn(draw, y, w, imgs=imgs, canvas_img=None):
            pass  # placeholder, real compositing done in render()

        self.blocks.append((h + 16, ("IMAGE_ROW", imgs, x0)))

    def add_final(self, text):
        x0 = PAD + 60
        tmp = Image.new("RGB", (10, 10))
        d = ImageDraw.Draw(tmp)
        inner_w = self.width - x0 - PAD - 32
        wrapped = wrap_text(text, body_font, inner_w, d)
        h = len(wrapped) * 32 + 32

        def draw_fn(draw, y, w):
            draw.rounded_rectangle([x0, y, w - PAD, y + h], radius=8,
                                    fill=(16, 38, 26), outline=(40, 90, 60), width=1)
            ty = y + 16
            for ln in wrapped:
                draw.text((x0 + 16, ty), ln, font=body_font, fill=OK)
                ty += 32

        self.blocks.append((h + 16, draw_fn))

    def add_divider(self):
        h = 40

        def draw_fn(draw, y, w):
            draw.line([PAD, y + 20, w - PAD, y + 20], fill=BORDER, width=1)

        self.blocks.append((h, draw_fn))

    def render(self):
        total_h = sum(h for h, _ in self.blocks) + PAD * 2
        img = Image.new("RGB", (self.width, total_h), BG)
        draw = ImageDraw.Draw(img)
        y = PAD
        for h, fn in self.blocks:
            if isinstance(fn, tuple) and fn[0] == "IMAGE_ROW":
                _, imgs, x0 = fn
                x = x0
                for im, cap in imgs:
                    img.paste(im, (x, y))
                    cap_w = draw.textlength(cap, font=caption_font)
                    draw.text((x + (im.width - cap_w) / 2, y + im.height + 10), cap, font=caption_font, fill=TEXT_DIM)
                    x += im.width + 24
            else:
                fn(draw, y, self.width)
            y += h
        return img


def main():
    c = Canvas(W)
    c.add_title("新手引导教程（图文版）")
    c.add_intro_panel([
        "按下方顺序依次操作；本图为网页版教程的离线备份，网页打不开时可直接查看此图。",
        "下载地址：https://github.com/yingke-quant/bwxrk-tutorial/releases/latest",
    ])
    c.add_divider()

    c.add_step_header(1, "下载并解压")
    c.add_body_text("点击上方下载地址获取最新版压缩包，下载完成后，将压缩包内的全部文件解压出来"
                     "（不要只打开压缩包直接运行，务必先解压到一个独立文件夹）。")
    c.add_divider()

    c.add_step_header(2, "执行第一步")
    c.add_body_text("解压完成后，按图示完成“第一步”操作。")
    c.add_images_row([(os.path.join(IMG_DIR, "第一步.png"), "第一步操作示例")])
    c.add_divider()

    c.add_step_header(3, "浏览器点全屏")
    c.add_body_text("打开浏览器（支付宝端），先点击全屏，再进行下一步操作。")
    c.add_images_row([(os.path.join(IMG_DIR, "浏览器点全屏.png"), "浏览器点全屏示例")])
    c.add_divider()

    c.add_step_header(4, "开工检查")
    c.add_tip("注意：务必核对“标定结果图片”和“适配结果图片”是否正常，确认无误后才能继续。")
    c.add_body_text("下图为开工检查页面示例，以及对应的“浏览器画布标定”示例，供你比对核实。")
    c.add_images_row([
        (os.path.join(IMG_DIR, "开工检查.png"), "开工检查示例"),
        (os.path.join(IMG_DIR, "浏览器画布标定.png"), "浏览器画布标定示例"),
    ])
    c.add_divider()

    c.add_step_header(5, "窗口适配成功")
    c.add_body_text("核对无误后，窗口适配成功的效果如下图所示。")
    c.add_images_row([(os.path.join(IMG_DIR, "适配成功.jpg"), "窗口适配成功示例")])
    c.add_divider()

    c.add_step_header(6, "开始挂机")
    c.add_final("以上步骤确认都没问题后，就可以放心去挂机了。")

    img = c.render()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    img.save(OUT_PATH)
    print("saved:", OUT_PATH, img.size)


if __name__ == "__main__":
    main()
