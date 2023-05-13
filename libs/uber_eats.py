import asyncio
import re
from typing import List, Optional

from loguru import logger
from playwright.async_api import Page, async_playwright

from .chrome import Chrome


class UberEats:
    MAIN_PAGE_URL = "https://www.ubereats.com"
    LOGIN_PAGE_URL = f"{MAIN_PAGE_URL}/login-redirect"
    INPUT_PROMOTE_PAGE_URL = f"{MAIN_PAGE_URL}/tw/feed?mod=promos"
    browser = None
    page = None

    @classmethod
    async def login(cls):
        # 進續登入頁面
        await cls.page.goto(cls.LOGIN_PAGE_URL)

    @classmethod
    @property
    def page(cls) -> Page:
        return cls.browser.contexts[0].pages[0]

    @classmethod
    async def get_prmote_page_url_list(cls) -> List[str]:
        """ 獲取優惠碼說明頁面連結串列

        Returns:
            List[str]: 優惠碼說明頁面連結串列
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
    async def get_promote_str_list(cls, prmote_page_url: str) -> List[str]:
        """ 從優惠碼頁面連結獲取優惠碼串列

        Args:
            prmote_page_url (str): 優惠碼頁面連結

        Returns:
            List[str]
        """
        page = await cls.browser.contexts[0].new_page()
        await page.goto(prmote_page_url, timeout=0)
        main_content_str = await page.inner_text("#main-content", timeout=None)
        await page.close()
        promote_str_list = []
        for promote_str in re.findall(
            r'輸入【(.*)】',
            "\n".join(main_content_str.splitlines()[1:])
        ):
            if "自取" in main_content_str:
                logger.warning(f'promote_str: {promote_str} (自取優惠碼)')
            else:
                logger.success(f'promote_str: {promote_str}')
                promote_str_list.append(promote_str)
        return promote_str_list

    @classmethod
    async def input_promote(cls, promote_str: str) -> None:
        """ 輸入優惠碼

        Args:
            promote_str (str): 優惠碼
        """
        page = await cls.browser.contexts[0].new_page()
        logger.info(f'輸入優惠碼: {promote_str} ...')
        await page.goto(cls.INPUT_PROMOTE_PAGE_URL, timeout=0)
        promote_input_locator = page.locator("input[placeholder=輸入優惠序號]")
        await promote_input_locator.wait_for(timeout=0)
        await promote_input_locator.fill(promote_str)
        apply_btn_locator = page.locator("text=套用")
        await apply_btn_locator.click()
        await apply_btn_locator.wait_for(timeout=0)
        await asyncio.sleep(2)
        await page.close()

    @classmethod
    async def run(cls):
        # 開啟背景執行除錯模式的 chrome
        Chrome.run_background()

        # 將 playwright 連接到 chrome
        async with async_playwright() as playwright:
            cls.browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")

            logger.info('獲取優惠碼頁面連結串列 ...')
            prmote_page_url_list = await cls.get_prmote_page_url_list()
            promote_str_list_list = await asyncio.gather(*[
                cls.get_promote_str_list(prmote_page_url)
                for prmote_page_url in prmote_page_url_list
            ])
            promote_str_set = {
                promote_str for promote_str in sum(promote_str_list_list, [])
            }
            logger.info('批量輸入優惠碼 ...')
            await asyncio.gather(*[
                cls.input_promote(promote_str)
                for promote_str in promote_str_set
                if promote_str is not None
            ])

        # 關閉 chrome
        Chrome.close()
