# -----------------------------------------------------------------------------
# Project: GagaraGogo Setup Bot
# Component: app.py
# Author: chaolcam (https://github.com/chaolcam/gagaragogo-userbot)
# License: GNU GPL v3.0
# Copyright (c) 2026 chaolcam
# -----------------------------------------------------------------------------
import os
import logging
import gradio as gr
from bot import ggr_app

try:
    spaces = __import__("spaces")
except Exception:
    class spaces:
        @staticmethod
        def GPU(func=None, **kwargs):
            return func

@spaces.GPU
def ggr_check_gpu_status():
    return "GagaraGogo Online"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

with gr.Blocks(title="GagaraGogo Kurulum Botu") as demo:
    gr.Markdown("### 🤖 GagaraGogo Kurulum Botu Aktif ve Çalışıyor")

if __name__ == "__main__":
    logging.info("🌐 [GAGARAGOGO] Gradio Web Sunucusu 7860 portunda başlatılıyor...")
    demo.launch(server_name="0.0.0.0", server_port=7860, prevent_thread_lock=True)
    
    logging.info("🤖 [GAGARAGOGO] Telegram Kurulum Botu başlatılıyor...")
    ggr_app.run()
