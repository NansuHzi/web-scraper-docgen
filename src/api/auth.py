from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
import os
import logging
import threading
import time

logger = logging.getLogger(__name__)

router = APIRouter()

_BROWSER_STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.browser_state')
ZHIHU_STATE_FILE = os.path.join(_BROWSER_STATE_DIR, 'zhihu_state.json')
os.makedirs(_BROWSER_STATE_DIR, exist_ok=True)

_login_status = {
    "status": "idle",
    "message": "",
    "timestamp": None,
}


class LoginRequest(BaseModel):
    site: str = "zhihu"


class LoginStatusResponse(BaseModel):
    status: str
    message: str
    has_saved_state: bool


def _do_zhihu_login():
    global _login_status
    _login_status = {
        "status": "waiting_login",
        "message": "浏览器已打开，请在浏览器中登录知乎",
        "timestamp": time.time(),
    }

    try:
        with sync_playwright() as p:
            stealth = Stealth()
            browser = p.chromium.launch(
                headless=False,
                args=stealth._patch_blink_features_cli_args(['--no-sandbox']),
            )
            stealth.hook_playwright_context(p)

            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )

            page = context.new_page()
            page.goto("https://www.zhihu.com", wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(3000)

            _login_status = {
                "status": "waiting_login",
                "message": "请在浏览器中完成知乎登录",
                "timestamp": time.time(),
            }

            max_wait = 180
            logged_in = False
            for i in range(max_wait):
                current_url = page.url
                cookies = context.cookies()
                zhihu_cookies = [c for c in cookies if 'zhihu.com' in c.get('domain', '')]
                has_session = any(c['name'] in ('z_c0', 'SESSIONID', 'token') for c in zhihu_cookies)

                if has_session and "signin" not in current_url and "login" not in current_url:
                    logged_in = True
                    break

                page.wait_for_timeout(1000)

                if i % 15 == 0:
                    _login_status = {
                        "status": "waiting_login",
                        "message": f"等待登录中... ({i}秒)",
                        "timestamp": time.time(),
                    }

            if logged_in:
                context.storage_state(path=ZHIHU_STATE_FILE)
                _login_status = {
                    "status": "success",
                    "message": "登录成功！浏览器状态已保存",
                    "timestamp": time.time(),
                }
                logger.info(f"Zhihu login state saved to: {ZHIHU_STATE_FILE}")
            else:
                _login_status = {
                    "status": "timeout",
                    "message": "登录超时，请重试",
                    "timestamp": time.time(),
                }

            browser.close()

    except Exception as e:
        _login_status = {
            "status": "error",
            "message": f"登录过程出错: {str(e)}",
            "timestamp": time.time(),
        }
        logger.error(f"Zhihu login error: {e}")


@router.post("/login")
async def start_login(request: LoginRequest):
    global _login_status

    if _login_status.get("status") == "waiting_login":
        return {
            "success": False,
            "message": "已有登录流程正在进行中",
            "status": _login_status,
        }

    if request.site == "zhihu":
        thread = threading.Thread(target=_do_zhihu_login, daemon=True)
        thread.start()
        return {
            "success": True,
            "message": "浏览器已打开，请在浏览器中完成知乎登录",
            "status": "waiting_login",
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported site: {request.site}")


@router.get("/login/status")
async def get_login_status():
    has_saved_state = os.path.exists(ZHIHU_STATE_FILE)
    return LoginStatusResponse(
        status=_login_status.get("status", "idle"),
        message=_login_status.get("message", ""),
        has_saved_state=has_saved_state,
    )


@router.get("/login/state")
async def check_saved_state():
    sites = {}
    sites["zhihu"] = {
        "has_saved_state": os.path.exists(ZHIHU_STATE_FILE),
        "state_file": ZHIHU_STATE_FILE if os.path.exists(ZHIHU_STATE_FILE) else None,
    }
    return {"sites": sites}
