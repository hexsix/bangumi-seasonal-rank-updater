import json
import re

import httpx
from loguru import logger

from app.config import config
from app.services import bgmtv, yucwiki


def extract_json(response):
    # 匹配 ```json 开头的代码块
    code_block_match = re.search(r"```json\n?(.*?)\n?```", response, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()

    # 匹配纯JSON对象（无代码块标记）
    json_match = re.search(r"\{.*\}", response, re.DOTALL)
    if json_match:
        return json_match.group(0)

    return response


class DSClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url="https://api.deepseek.com",
            headers={"Authorization": f"Bearer {config.ds_api_key}"},
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    async def get_subject_id(
        self, yuc_info: yucwiki.YucWiki, bgm_info: bgmtv.PagedSubject
    ) -> int:
        prompt = """
        你是一个动漫百科全书，请根据以下信息，判断BangumiInfo中是否存在YucWiki中的动漫，如果存在，请返回该动漫的Subject ID，否则返回-1。
        """
        prompt += f"YucWiki: {json.dumps(yuc_info.model_dump(), ensure_ascii=False)}"
        prompt += f"BgmInfo: {json.dumps(bgm_info.model_dump(), ensure_ascii=False)}"
        prompt += '请严格返回一个JSON对象，包含一个字段{"subject_id": int}，不要包含任何额外文本或代码块标记！'
        logger.info(f"ds prompt: {prompt}")
        response = await self.client.post(
            "/v1/chat/completions",
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        json_str = response.json()["choices"][0]["message"]["content"]
        logger.info(f"ds response: {json_str}")
        json_str = extract_json(json_str)
        try:
            return json.loads(json_str)["subject_id"]
        except Exception:
            return -1


ds_client = DSClient()


async def main():
    from app.services.bgmtv import search_subject_by_name

    client = DSClient()
    yuc_info = yucwiki.YucWiki(
        jp_title="HOTEL INHUMANS",
        cn_title="异人旅馆",
        staff="""原作：田岛青
(Sunday Webry/小学馆)
导演：网野哲郎
编剧：米村正二
动画人设：藤崎真吾
音乐：小春
动画制作：Bridge""",
        cast="""小林裕介
白浜灯奈乃""",
    )
    bgm_info = await search_subject_by_name("HOTEL INHUMANS")
    subject_id = await client.get_subject_id(yuc_info, bgm_info)
    logger.info(subject_id)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
