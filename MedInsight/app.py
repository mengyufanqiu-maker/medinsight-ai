import os
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ==========================================
# 🔐 100% 大厂无痕规范：仅从系统环境变量读取
# ==========================================
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/v1/chat/completions"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/audit', methods=['POST'])
def audit_document():
    try:
        # 🛡️ 极其关键的安全拦截：如果没有配钥匙，立刻报错！
        if not API_KEY:
            return jsonify({"error": "系统未检测到 API 密钥。请在 Render 的 Environment 环境变量中配置 DEEPSEEK_API_KEY！"}), 500

        medical_text = request.form.get('medical_text', '').strip()
        if not medical_text:
            return jsonify({"error": "请提供需要审计的医学文案文本内容！"}), 400

        system_prompt = f"""你是一位精通跨国药企医学事务（MA）合规审计与国家最新《广告法》医疗红线标准的资深合规专家。
请对以下输入的医学宣传物料进行高维度、零容错率的结构化审计。

【待审计文本】：
{medical_text}

【输出格式要求】：
请严格使用以下特定分隔暗号输出三个独立的结构，以便前端进行高规格医学卡片渲染。不要输出任何客套话。
每一部分之间请用 '===SECTION_SPLIT===' 隔开！

一、临床核心数据与医学证据链提取：
[结构化提取文献中的临床结论]
===SECTION_SPLIT===
二、涉嫌违反《广告法》/ 行业合规红线扫描：
[严格扫描是否含有“根治”、“全网第一”等绝对化用语，并明确指出风险等级]
===SECTION_SPLIT===
三、合规修正建议与话术改良：
[给出既符合科学事实又符合广告法合规要求的宣教改良话术]
"""

        response = requests.post(API_URL, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": system_prompt}],
            "temperature": 0.1  
        }, headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }, timeout=60)

        if response.status_code != 200:
            return jsonify({"error": f"医学大脑响应异常: {response.status_code}"}), 500

        return jsonify({"result": response.json()['choices'][0]['message']['content']})

    except Exception as e:
        return jsonify({"error": f"服务器内部审计错误: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
