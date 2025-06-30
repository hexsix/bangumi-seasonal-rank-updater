import httpx
from bs4 import BeautifulSoup
from loguru import logger

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    "Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
)

BASE_URL = "https://yuc.wiki"


class YucWiki:
    jp_title: str
    cn_title: str
    staff: str
    cast: str

    def __init__(self, jp_title: str, cn_title: str, staff: str, cast: str):
        self.jp_title = jp_title
        self.cn_title = cn_title
        self.staff = staff
        self.cast = cast

    def __str__(self):
        return f"日文名：{self.jp_title}\n中文名：{self.cn_title}\nstaff：{self.staff}\ncast：{self.cast}"

    def model_dump(self) -> dict:
        return {
            "jp_title": self.jp_title,
            "cn_title": self.cn_title,
            "staff": self.staff,
            "cast": self.cast,
        }


async def get_raw_index(season_id: int) -> str:
    async with httpx.AsyncClient(
        base_url=BASE_URL,
        headers={"User-Agent": DEFAULT_USER_AGENT},
    ) as client:
        logger.info(f"从 {BASE_URL} 获取 {season_id} 季度的动画列表")
        response = await client.get(f"/{season_id}/")
        return response.text


def html_parser(html: str) -> list[YucWiki]:
    soup = BeautifulSoup(html, "lxml")
    jp_titles = [el.get_text(strip=True) for el in soup.select('[class^="title_jp"]')]
    cn_titles = [el.get_text(strip=True) for el in soup.select('[class^="title_cn"]')]
    staffs = [el.get_text(strip=True) for el in soup.select('[class^="staff"]')]
    casts = [el.get_text(strip=True) for el in soup.select('[class^="cast"]')]
    yucwiki_list = []
    for i in range(len(jp_titles)):
        yucwiki_list.append(YucWiki(jp_titles[i], cn_titles[i], staffs[i], casts[i]))

    return yucwiki_list


async def get_anime_list(season_id: int) -> list[YucWiki]:
    raw_index = await get_raw_index(season_id)
    return html_parser(raw_index)


async def main():
    from app.services.bgmtv.api import search_anime

    yucwiki_list = await get_anime_list(202507)
    logger.info(f"获取到 {len(yucwiki_list)} 部动画")
    for yucwiki in yucwiki_list:
        logger.info("================================================")
        logger.info(f"yucwiki: {yucwiki}")
        jp_subjects = await search_anime(yucwiki.jp_title)
        for i, subject in enumerate(jp_subjects.data):
            if subject.name == yucwiki.jp_title:
                logger.info(
                    f"日文名第 {i} 项完全匹配, bangumi subject_id: {subject.id}"
                )
                break
        else:
            pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
