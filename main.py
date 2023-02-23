"""
執行方法:
    python main.py

若 storage.json 過期，則用以下方法更新:

    執行
        ``` bash
        playwright open --storage-state=uber_eats_storage.json
        ```

    並手動登入 UE 帳號 (不要用 Google 登入) 後，再執行 `python main.py`
"""

import asyncio
import re
from typing import List, Optional, Set

import nest_asyncio
from loguru import logger
from playwright.async_api import BrowserContext, Page, async_playwright

# 開啟巢狀異步，方便於 debug console 中使用執行協程: asyncio.run([cor])
nest_asyncio.apply()


async def input_promote(context: BrowserContext, promote_str: str) -> None:
    """ 輸入優惠碼

    Args:
        context (BrowserContext)
        promote_str (str): 優惠碼
    """
    page = await context.new_page()
    logger.info(f'進入 UE 輸入優惠碼首頁並等待頁面加載完成 ...')
    promote_page_url = "https://www.ubereats.com/tw/feed?diningMode=DELIVERY&mod=promos&pl=JTdCJTIyYWRkcmVzcyUyMiUzQSUyMiVFOCU4RiVBRiVFNiU5NiVCMCVFOCVBMSU5NzE0MyVFNSVCNyVCNzUxJUU4JTk5JTlGJTIyJTJDJTIycmVmZXJlbmNlJTIyJTNBJTIyQ2hJSm5lTHBGMmtDYURRUkEtcm5vT1NjVHc4JTIyJTJDJTIycmVmZXJlbmNlVHlwZSUyMiUzQSUyMmdvb2dsZV9wbGFjZXMlMjIlMkMlMjJsYXRpdHVkZSUyMiUzQTI0Ljk4MDIzMTclMkMlMjJsb25naXR1ZGUlMjIlM0ExMjEuNTA2MzkwMiU3RA%3D%3D&ps=1"
    await page.goto(promote_page_url)
    promote_input_selector_str = "input[placeholder=輸入優惠序號]"
    await page.wait_for_selector(promote_input_selector_str)
    await page.fill(promote_input_selector_str, promote_str)
    await page.click("text=套用")
    await asyncio.sleep(5)
    await page.close()


async def get_prmote_str_set(context: BrowserContext) -> Set[str]:
    """ 獲取目前優惠碼集合

    Args:
        context (BrowserContext)

    Returns:
        Set[str]: 優惠碼集合
    """

    logger.info(f'進入 UE 首頁並等待頁面加載完成 ...')
    page = await context.new_page()
    ue_main_page_url = "https://www.ubereats.com"
    await page.goto(ue_main_page_url, timeout=None)
    a_list_selector_str = "#main-content > div > div > div:nth-child(2) > div > div > div > div > div > div > div:nth-child(3) a"
    await page.wait_for_selector(a_list_selector_str, timeout=None)

    logger.info(f'獲取優惠碼頁面連結串列 ...')
    a_list_locator = page.locator(a_list_selector_str)
    a_list_len = await a_list_locator.count()
    url_list = []
    for a_i in range(a_list_len):
        url = await a_list_locator.nth(a_i).get_attribute('href')
        if ('marketing?bbid' in url):
            url_list.append(f"{ue_main_page_url}{url}")

    async def get_promote_str(url: str) -> Optional[str]:
        """ 從優惠碼頁面獲取優惠碼

        Args:
            url (str): 優惠碼頁面連結

        Returns:
            Optional[str]: 優惠碼. 若為 None 則表示該頁面沒有優惠碼，或者為自取優惠碼.
        """
        page = await context.new_page()
        await page.goto(url, timeout=None)
        main_content_str = await page.inner_text("#main-content", timeout=None)
        await page.close()
        for promote_str in re.findall(
            r'【(.*)】',
            "\n".join(main_content_str.splitlines()[1:])
        ):
            if "自取" in main_content_str:
                logger.warning(f'promote_str: {promote_str} (自取優惠碼)')
                return None
            else:
                logger.success(f'promote_str: {promote_str}')
            return promote_str
        return None

    logger.info(f'解析各優惠碼頁面，並取得優惠碼 ...')
    promote_str_list = await asyncio.gather(*[
        get_promote_str(url) for url in url_list
    ])
    await page.close()
    return set([
        promote_str for promote_str in promote_str_list
        if promote_str is not None
    ])


async def input_all_promote() -> None:
    """ 自動輸入所有當期優惠碼
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
        )
        context = await browser.new_context(
            storage_state='uber_eats_storage.json',
        )
        # --------------------------------
        # 獲取優惠碼集合
        prmote_str_set = await get_prmote_str_set(
            context=context,
        )
        # 批次輸入優惠碼
        await asyncio.gather(*[
            input_promote(
                context=context,
                promote_str=prmote_str,
            )
            for prmote_str in prmote_str_set
        ])
        # --------------------------------
        await context.close()
        await browser.close()


async def main():
    await input_all_promote()


if __name__ == "__main__":
    asyncio.run(main())
