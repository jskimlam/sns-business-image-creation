"""Run the subscription-backed studio on the loopback interface."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import webbrowser
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8765
ORIGIN = f"http://{HOST}:{PORT}"
LOCK = threading.Lock()
ASSETS = {"/": ("studio-mobile.html", "text/html")}
MODELS = {"gpt-6-astra", "gpt-6.1-sol"}


def generate(model, brief, count):
    cli = shutil.which("codex")
    if not cli:
        raise ValueError("Codex CLI를 설치하고 codex login을 실행하세요.")
    env = {k: v for k, v in os.environ.items() if k not in {"OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"}}
    auth = subprocess.run([cli, "login", "status"], capture_output=True, env=env, timeout=20)
    if auth.returncode or b"logged in using chatgpt" not in (auth.stdout + auth.stderr).lower():
        raise ValueError("codex login에서 ChatGPT 계정으로 로그인한 뒤 다시 시도하세요.")
    with tempfile.TemporaryDirectory() as directory:
        schema = Path(directory, "schema.json")
        schema.write_text(json.dumps({"type":"object","additionalProperties":False,"required":["images"],"properties":{"images":{"type":"array","items":{"type":"string"}}}}))
        result = Path(directory, "result.json")
        prompt = (f"Create exactly {count} standalone SVG graphic designs. Return each complete SVG as a string in images. "
                  "Use a matching viewBox, self-contained vector illustration and legible Korean text. Use only inline SVG shapes, text and paths. "
                  "No script, external resources, foreignObject, tools or filesystem operations. For multiple outputs follow the requested variants. "
                  "Make each graphic visually complete at the specified aspect ratio. User design brief follows.\n" + brief)
        args = [cli, "exec", "--skip-git-repo-check", "--ephemeral", "-s", "read-only",
                "-c", 'model_provider="openai"', "-c", 'forced_login_method="chatgpt"', "-m", model,
                "--output-schema", str(schema), "-o", str(result), "-"]
        execution = subprocess.run(args, input=prompt.encode(), cwd=directory, env=env, capture_output=True, timeout=420)
        if execution.returncode or not result.exists():
            raise ValueError("모델 실행에 실패했습니다. Codex의 모델 이용 권한·구독 한도·연결 상태를 확인하세요.")
        images = json.loads(result.read_text(encoding="utf-8"))["images"]
        if not isinstance(images,list) or len(images) != count:
            raise ValueError("요청한 시안 수를 받지 못했습니다. 다시 생성하세요.")
        for svg in images:
            if not isinstance(svg,str) or len(svg)>2000000 or "<!DOCTYPE" in svg.upper():
                raise ValueError("시안 형식 오류입니다. 다시 생성하세요.")
            root = ET.fromstring(svg)
            if root.tag != "{http://www.w3.org/2000/svg}svg" or not root.get("viewBox"):
                raise ValueError("시안에 SVG 화면 영역이 없습니다. 다시 생성하세요.")
        return images


class Studio(BaseHTTPRequestHandler):
    def send_data(self, status, data, mime="application/json"):
        payload = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.headers.get("Host") != f"{HOST}:{PORT}":
            return self.send_data(403, {})
        if self.path == "/mode":
            return self.send_data(200, {"studio": True})
        if self.path in ASSETS:
            name, mime = ASSETS[self.path]
            return self.send_data(200, (ROOT / name).read_bytes(), mime)
        self.send_data(404, {})

    def do_POST(self):
        if self.path != "/generate" or self.headers.get("Origin") != ORIGIN or self.headers.get("Host") != f"{HOST}:{PORT}":
            return self.send_data(403, {})
        if self.headers.get_content_type() != "application/json":
            return self.send_data(415, {})
        if not LOCK.acquire(blocking=False):
            return self.send_data(409, {"error":"진행 중인 작업을 마친 뒤 다시 시도하세요."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length < 120000:
                raise ValueError("입력 분량을 줄여 주세요.")
            req = json.loads(self.rfile.read(length))
            model, brief, kind = req["model"], req["brief"], req["kind"]
            if model not in MODELS or not isinstance(brief,str) or not brief.strip() or type(kind) is not int or kind not in range(8):
                raise ValueError("제작 설정을 확인하세요.")
            images = generate(model, brief, {3:3, 4:2}.get(kind,1))
            self.send_data(200, {"images":images})
        except subprocess.TimeoutExpired:
            self.send_data(504, {"error":"모델 응답 시간이 초과되었습니다. 입력을 줄여 다시 시도하세요."})
        except (ValueError, ET.ParseError, TypeError, KeyError, OSError) as err:
            self.send_data(400, {"error":str(err)})
        finally:
            LOCK.release()


if __name__ == "__main__":
    with ThreadingHTTPServer((HOST, PORT), Studio) as server:
        print(ORIGIN, flush=True)
        webbrowser.open(ORIGIN)
        server.serve_forever()
