# -*- coding: utf-8 -*-
import os
import gzip
import tarfile
from flask import Flask, request, make_response, send_from_directory, render_template, stream_with_context, Response

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
upload_dir = BASE_DIR + "/flask_up/upload/"
temp_dir = BASE_DIR + "/flask_up/temp/"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


def get_files():
    print(upload_dir)
    dirpath, dirnames, filenames = list(os.walk(upload_dir))[0]
    return filenames


def generate(filename):
    with open(temp_dir+filename, "rb+") as r:
        while True:
            chunk_data = r.read(512)
            if not chunk_data:
                break
            yield chunk_data


@app.route('/download/<string:filename>', methods=['GET'])
def download(filename):  # 所有分片均上传完后被调用
    file_name = filename.encode().decode('latin-1')
    response = Response(stream_with_context(generate(file_name)))
    response.headers['Content-Disposition'] = "attachment; filename={0}".format(file_name)
    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Length'] = 20 * 1024 * 1024
    return response


@app.route('/down/<string:filename>', methods=['GET'])
def download2(filename):  # 所有分片均上传完后被调用
    file_name = filename.encode().decode('latin-1')
    response = make_response(send_from_directory(temp_dir, filename, as_attachment=True))
    response.headers['Content-Disposition'] = "attachment; filename={0}".format(file_name)
    response.headers['Content-Type'] = "application/octet-stream"
    # response.headers['Content-Length'] = 20 * 1024 * 1024
    return response


def gzipobject():
    dirpath, dirnames, filenames = list(os.walk(temp_dir))[0]
    with tarfile.open(temp_dir+"sample.tar", "w") as tar:
        for name in filenames:
            tar.add(dirpath + name)
    with open(temp_dir+"sample.tar", "rb+") as f:
        while True:
            chunk_data = f.read(512)
            if not chunk_data:
                break
            yield chunk_data


@app.route('/gzip/<string:filename>', methods=['GET'])
def gzipfile(filename):  # 所有分片均上传完后被调用
    file_name = filename.encode().decode('latin-1')
    response = Response(stream_with_context(gzipobject()), mimetype='application/gzip')
    # gzip_buffer = StringIO.StringIO()
    # gzip_file = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=gzip_buffer)
    # gzip_file.write(response.data)
    # gzip_file.close()
    # response.data = gzip_buffer.getvalue()
    # response.headers['Content-Encoding'] = 'gzip'
    # response.headers['Content-Length'] = len(response.data)
    response.headers['Content-Disposition'] = "attachment; filename={0}".format(file_name+".gz")
    # response.headers['Content-Length'] = 20 * 1024 * 1024
    return response


@app.route('/', methods=['GET', 'POST'])
def index():  # 一个分片上传后被调用
    if request.method == 'POST':
        print(request.form)
        upload_file = request.files['file']
        task = request.form.get('task_id')  # 获取文件唯一标识符
        chunk = request.form.get('chunk', 0)  # 获取该分片在所有分片中的序号
        filename = temp_dir + '%s%s' % (task, chunk)  # 构成该分片唯一标识符
        upload_file.save(filename)  # 保存分片到本地
    return render_template('hello.html', dir=upload_dir, files=get_files())


@app.route('/success', methods=['GET'])
def upload_success(chunk=0):  # 所有分片均上传完后被调用
    task = request.args.get('task_id')
    name = request.args.get('name')
    print(request.form)
    with open(upload_dir + '%s' % name, 'wb') as target_file:  # 创建新文件
        while True:
            try:
                filename = temp_dir + '%s%d' % (task, chunk)
                source_file = open(filename, 'rb')  # 按序打开每个分片
                target_file.write(source_file.read())  # 读取分片内容写入新文件
                source_file.close()
                chunk += 1
                os.remove(filename)  # 删除该分片，节约空间
            except IOError:
                break
    return render_template('hello.html', dir=upload_dir, files=get_files())


if __name__ == '__main__':
    app.secret_key = "packet"
    app.run(debug=True, host='0.0.0.0', port=8080)
