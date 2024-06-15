from flask import Flask, request, render_template_string
import csv
from collections import defaultdict, deque
import subprocess
import base64
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
CSV_FILE_PATH = os.path.join(UPLOAD_FOLDER, 'edges.csv')


# 读取 CSV 文件，返回节点关系的字典
def read_csv(file_path):
    edges = defaultdict(list)
    nodes = set()
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            start, end = row
            edges[start].append(end)
            nodes.add(start)
            nodes.add(end)
    return edges, nodes


# 生成 PlantUML 文本
def generate_plantuml(edges, nodes):
    plantuml_lines = ["@startuml"]
    for node in nodes:
        plantuml_lines.append(f"node {node} {{\n}}")
    for start, ends in edges.items():
        for end in ends:
            plantuml_lines.append(f"{start} --> {end}")
    plantuml_lines.append("@enduml")
    return "\n".join(plantuml_lines)


# 生成指定节点的调用链路
def generate_call_chain(edges, start_node):
    plantuml_lines = ["@startuml"]
    visited = set()
    queue = deque([start_node])

    while queue:
        current_node = queue.popleft()
        if current_node not in visited:
            visited.add(current_node)
            plantuml_lines.append(f"node {current_node} {{\n}}")
            for neighbor in edges[current_node]:
                plantuml_lines.append(f"{current_node} --> {neighbor}")
                if neighbor not in visited:
                    queue.append(neighbor)

    plantuml_lines.append("@enduml")
    return "\n".join(plantuml_lines)


@app.route('/', methods=['GET', 'POST'])
def index():
    plantuml_image_base64 = ""
    if request.method == 'POST':
        start_node = request.form.get('start_node')
        if 'file' in request.files:
            file = request.files['file']
            if file.filename.endswith('.csv'):
                file.save(CSV_FILE_PATH)

        edges, nodes = read_csv(CSV_FILE_PATH)
        if start_node:
            plantuml_text = generate_call_chain(edges, start_node)
        else:
            plantuml_text = generate_plantuml(edges, nodes)

        with open("output.puml", "w") as f:
            f.write(plantuml_text)

        # Use PlantUML to generate PNG image with higher DPI
        subprocess.run(["java", "-DPLANTUML_DPI=300", "-jar", "./plantuml.jar",
                        "output.puml"])

        # Convert image to base64
        with open("output.png", "rb") as image_file:
            plantuml_image_base64 = base64.b64encode(image_file.read()).decode(
                'utf-8')

    return render_template_string('''
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>CSV to PlantUML</title>
            <script src="https://cdn.tailwindcss.com"></script>
          </head>
          <body class="bg-gray-100">
            <div class="container mx-auto px-4 py-8">
              <h1 class="text-3xl font-bold text-center mb-8">CSV to PlantUML</h1>
              <form method="post" enctype="multipart/form-data" class="max-w-lg mx-auto bg-white p-6 rounded-lg shadow-md">
                <div class="mb-4">
                  <label for="file" class="block text-gray-700 text-lg font-bold">Upload CSV</label>
                  <input type="file" class="form-input mt-1 block w-full border border-gray-300 rounded-md p-2" id="file" name="file">
                </div>
                <div class="mb-4">
                  <label for="start_node" class="block text-gray-700 text-lg font-bold">Start Node</label>
                  <input type="text" class="form-input mt-1 block w-full border border-gray-300 rounded-md p-2" id="start_node" name="start_node" placeholder="Enter start node">
                </div>
                <button type="submit" class="w-full bg-blue-500 text-white font-bold py-2 px-4 rounded-md hover:bg-blue-700">Generate</button>
              </form>
              {% if plantuml_image_base64 %}
              <div class="mt-8 text-center">
                <h3 class="text-2xl font-semibold mb-4">Generated Diagram</h3>
                <div class="inline-block border-4 border-gray-300 p-2">
                  <img src="data:image/png;base64,{{ plantuml_image_base64 }}" alt="PlantUML Diagram" class="max-w-full h-auto">
                </div>
              </div>
              {% endif %}
            </div>
          </body>
        </html>
    ''', plantuml_image_base64=plantuml_image_base64)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
