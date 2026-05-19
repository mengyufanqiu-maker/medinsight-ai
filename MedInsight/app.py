import os
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# 尝试导入文档解析库
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx
except ImportError:
    docx = None

app = Flask(__name__)
# 允许跨域请求
CORS(app)


# ==================================================
# 核心路由 1：负责展示前端网页（前厅）
# ==================================================
@app.route('/')
def home():
    return render_template('index.html')


# ==================================================
# 你的专属密钥与配置
# ==================================================
API_KEY = "sk-48bf10f821904382ae63972a30f5f6db"
API_URL = "https://api.deepseek.com/v1/chat/completions"


def parse_pdf(file_path):
    if fitz is None:
        return "[错误] 未安装 PyMuPDF 库，无法解析 PDF。"
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        return f"[PDF解析失败]: {str(e)}"


def parse_docx(file_path):
    if docx is None:
        return "[错误] 未安装 python-docx 库，无法解析 Word。"
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        return f"[Word解析失败]: {str(e)}"


# ==================================================
# 核心路由 2：负责处理大模型 AI 解析逻辑（后厨）
# ==================================================
@app.route('/api/analyze', methods=['POST'])
def analyze():
    mode = request.form.get('mode')
    input_text = ""

    if mode == 'text':
        input_text = request.form.get('text', '')
    elif mode == 'file':
        if 'file' not in request.files:
            return jsonify({"error": "没有收到上传的文件"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "未选择任何文件"}), 400

        temp_dir = os.path.join(os.getcwd(), "temp_uploads")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)

        if file.filename.lower().endswith('.pdf'):
            input_text = parse_pdf(file_path)
        elif file.filename.lower().endswith(('.docx', '.doc')):
            input_text = parse_docx(file_path)
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    input_text = f.read()
            except:
                input_text = "[不支持的文件格式] 请上传 PDF 或 Word 文档。"

        try:
            os.remove(file_path)
        except:
            pass

    # 修复了那个坑人的拦截 Bug（现在开头的正常中括号不会被拦截了）
    if not input_text.strip() or input_text.startswith("[错误") or input_text.startswith("[不支持"):
        return jsonify({"result": f"文件解析异常或内容为空。\n{input_text}"})

    system_prompt = """你是一个资深的外企药企医学部(Medical Affairs)总监和极度严谨的药品合规部(Compliance)专家。
请仔细阅读用户提供的原始医学资料，并严格按照以下三个结构化矩阵模块进行中文深度解读，格式要求清晰美观，多用加粗和分条列项：

### 📈 一、核心学术结论 (Key Clinical Findings)
- 精准提取临床试验的核心有效性终点数据（如总生存期 OS、无进展生存期 PFS、风险比 HR、P值等）。

### 🩺 二、规范化临床用药建议 (Clinical Practice Guideline)
- 提炼推荐给药剂量、给药周期、以及联合用药方案。
- 给出针对特殊人群的剂量调剂或监测红线提示。

### 🛡️ 三、推广物料合规红线扫描 (DA Compliance Risk Audit)
- 重点审查：严厉指出用户文本中是否存在夸大疗效、绝对化用语（如“最安全”、“保证治愈”、“无副作用”）等违规行为。
- 如果存在违规，给出修改前后的对比。"""

    try:
        response = requests.post(API_URL, json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                # 修复了那个引发 500 报错的无引号 Bug！
                {"role": "user", "content": input_text}
            ],
            "temperature": 0.2
        }, headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }, timeout=60)

        if response.status_code != 200:
            return jsonify({"error": f"调用大模型失败，状态码: {response.status_code}"}), 500

        res_data = response.json()
        ai_result = res_data['choices'][0]['message']['content']
        return jsonify({"result": ai_result})

    except Exception as e:
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500


if __name__ == '__main__':
    print("==================================================")
    print(" MedInsight AI 真实全栈后端服务器已启动！")
    print(" 访问地址: http://127.0.0.1:5000")
    print("==================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)