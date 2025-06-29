import json

import httpx
from bs4 import BeautifulSoup
from loguru import logger

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    "Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
)

BASE_URL = "https://youranimes.tw"


async def get_raw_index(season_id: int) -> str:
    async with httpx.AsyncClient(
        base_url=BASE_URL,
        headers={"User-Agent": DEFAULT_USER_AGENT},
    ) as client:
        response = await client.get(f"/bangumi/{season_id}")
        return response.text


async def get_anime_list(season_id: int) -> list[str]:
    logger.info(f"从 {BASE_URL} 获取 {season_id} 季度的动画列表")
    raw_index = await get_raw_index(season_id)
    return html_parser(raw_index)


def html_parser(html: str) -> list[str]:
    anime_list = []
    soup = BeautifulSoup(html, "html.parser")

    script_tags = soup.find_all("script")
    for script in script_tags:
        if hasattr(script, "string"):
            s = getattr(script, "string", None)
            if s and "jpName" in s:
                try:
                    script_content = json.loads(s[19:-1])
                    content = json.loads(script_content[1][2:])[0][3]["children"]

                    # 解析meta_info（页面标题和描述信息）
                    meta_info = content[0][3]["children"]
                    page_title = meta_info[0][3]["children"]
                    logger.info(f"页面标题: {page_title}")
                    page_description = meta_info[1][3]["children"]
                    logger.info(f"页面描述: {page_description}")

                    # 解析动画列表
                    animes = content[1][3]["animes"]
                    for anime in animes:
                        cross = anime.get("cross")
                        if cross:
                            continue
                        anime_name = anime.get("jpName")
                        if anime_name:
                            anime_list.append(anime_name)
                        else:
                            anime_name = anime.get("name")
                            if anime_name:
                                anime_list.append(anime_name)

                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    logger.warning(f"解析JavaScript数据失败: {e}")
                    continue

    logger.info(f"找到 {len(anime_list)} 个动画")
    return anime_list


if __name__ == "__main__":
    import asyncio

    anime_list = asyncio.run(get_anime_list(202507))

    logger.info(f"前5个动画: {anime_list[:5]}")

    assert "Turkey!" in anime_list
    assert "CITY THE ANIMATION" in anime_list
    assert "白豚貴族ですが前世の記憶が生えたのでひよこな弟育てます" in anime_list
    assert "デキちゃうまで婚" in anime_list
    assert "人妻の唇は缶チューハイの味がして" in anime_list
    assert "ぬきたし THE ANIMATION" in anime_list
    assert "Summer Pockets" not in anime_list
