import asyncio
import json
import time
from pathlib import Path
from subprocess import Popen
from typing import List, Set

import nest_asyncio
from loguru import logger
from playwright.async_api import async_playwright

from .chrome import Chrome


class UberEats:
    MAIN_PAGE_URL = "https://www.ubereats.com"
    browser = None
    page = None

    @classmethod
    async def login(cls):
        # 進續登入頁面
        await cls.page.goto("https://www.ubereats.com/login-redirect/")

    @classmethod
    async def get_prmote_page_url_list(cls) -> List[str]:
        """ 獲取目前優惠碼集合

        Returns:
            Set[str]: 優惠碼集合
        """
        logger.info('進入 UE 首頁並等待頁面加載完成 ...')
        await cls.page.goto(cls.MAIN_PAGE_URL, timeout=0)
        a_list_locator = cls.page.locator(
            "#main-content > div > div > div:nth-child(2) > div > div > div > div > div > div > div:nth-child(3) a"
        )
        await a_list_locator.first.wait_for(timeout=0)

        logger.info('獲取優惠碼頁面連結串列 ...')
        a_list_len = await a_list_locator.count()
        url_list = []
        for a_i in range(a_list_len):
            href_str = await a_list_locator.nth(a_i).get_attribute('href')
            if ('marketing?bbid' in href_str):
                url_list.append(f"{cls.MAIN_PAGE_URL}{href_str}")
        return url_list

    @classmethod
    async def run(cls):
        Chrome.run_background()

        # 登入
        async with async_playwright() as playwright:
            cls.browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
            cls.page = await cls.browser.new_page()

            logger.info('獲取優惠碼頁面連結串列 ...')
            prmote_page_url_list = await cls.get_prmote_page_url_list()
            print((prmote_page_url_list))
            # for prmote_page_url in prmote_page_url_list:
            # print(prmote_page_url_list)

        # await save_cookies_json()
        # await test_google_without_login()

        Chrome.close()
