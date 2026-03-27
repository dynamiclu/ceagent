#!/usr/bin/env python3
"""使用 Playwright 自动化登录小红书并导出内容分析数据。"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from playwright.sync_api import Page, TimeoutError, sync_playwright


XHS_HOME = "https://creator.xiaohongshu.com"
DOWNLOAD_DIR = Path(__file__).parent / "downloads"


def click_first(page: Page, selectors: Iterable[str], timeout: int = 15000) -> None:
    """依次尝试点击多个 selector，直到成功。"""
    for selector in selectors:
        try:
            page.locator(selector).first.click(timeout=timeout)
            return
        except TimeoutError:
            continue
    raise TimeoutError(f"无法点击任何候选元素: {selectors}")


def wait_for_login(page: Page) -> None:
    """等待用户扫码登录。"""
    print("请在弹出的浏览器中完成扫码登录（如已登录会自动跳过）...")
    # 等到出现“发布”入口，表示已进入创作者后台首页。
    page.get_by_role("link", name="发布").wait_for(timeout=300_000)
    print("登录成功。")


def main() -> None:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=120)
        context = browser.new_context(accept_downloads=True, locale="zh-CN")
        page = context.new_page()

        print(f"打开小红书创作者平台: {XHS_HOME}")
        page.goto(XHS_HOME, wait_until="domcontentloaded")

        wait_for_login(page)

        print("进入【发布】页面...")
        click_first(page, [
            "a:has-text('发布')",
            "button:has-text('发布')",
            "text=发布",
        ])
        page.wait_for_load_state("networkidle")

        print("进入【数据看板】>【内容分析】...")
        click_first(page, [
            "a:has-text('数据看板')",
            "text=数据看板",
        ])
        click_first(page, [
            "a:has-text('内容分析')",
            "text=内容分析",
        ])
        page.wait_for_load_state("networkidle")

        print("点击【导出数据】并下载...")
        with page.expect_download(timeout=120_000) as download_info:
            click_first(page, [
                "button:has-text('导出数据')",
                "text=导出数据",
            ])

        download = download_info.value
        filename = download.suggested_filename
        save_path = DOWNLOAD_DIR / filename
        download.save_as(save_path)

        print(f"下载完成: {save_path.resolve()}")
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
